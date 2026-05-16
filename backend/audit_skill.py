"""案例审核 Skill —— 硬审核自动化 + 软审核 AI 辅助。

提供 HardAuditor（格式合规检查）、SoftAuditor（LLM 风险高亮）、
AuditReport（审核报告生成）以及统一的 `audit_case()` 入口。

依赖：
  - llm_client（软审核调用 LLM）
  - fact_verification（案例内 URL/引用核查）
"""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from llm_client import get_llm_client
except ImportError:
    from backend.llm_client import get_llm_client

try:
    from fact_verification import verify_claim
except ImportError:
    from backend.fact_verification import verify_claim


# ---------------------------------------------------------------------------
# HardAuditor
# ---------------------------------------------------------------------------

class HardAuditor:
    """自动化硬审核器 —— 检查格式合规性，无需 LLM。"""

    # 模板类型到必含结构的映射
    TEMPLATE_STRUCTURES = {
        "A": ["情境还原", "冲突与抉择", "行动与结果", "思政映射", "讨论问题"],
        "B": ["现象层", "本质层", "价值层", "讨论问题"],
        "C": ["对比维度", "思政落点"],
        "D": [
            "事件客观呈现",
            "多元视角还原",
            "原因分层分析",
            "制度回应",
            "思政价值点提炼",
            "讨论问题",
        ],
    }

    # 判断模板类型的关键词（优先级：D > B > A > C）
    TEMPLATE_KEYWORDS = {
        "D": ["事件客观呈现", "多元视角还原", "原因分层分析"],
        "B": ["现象层", "本质层", "价值层"],
        "A": ["情境还原", "冲突与抉择", "行动与结果"],
        "C": ["对比维度", "比较分析"],
    }

    REQUIRED_FIELDS = [
        "title",
        "适用课程",
        "素材类型",
        "素材性质",
        "主打思政主题",
    ]

    def audit(self, case: dict) -> dict:
        """对案例执行全部硬审核检查。

        Args:
            case: 案例字典，至少包含 title 和 content

        Returns:
            {"passed_all": bool, "checks": list[dict], "score": int}
        """
        content = case.get("content", "")
        checks = []

        checks.append(self._check_word_count(content))
        checks.append(self._check_required_fields(case))
        checks.append(self._check_structure(content))
        checks.append(self._check_discussion_questions(content))
        checks.append(self._check_source_attribution(content))
        checks.append(self._check_negative_case_exit(content, case.get("素材性质", "")))

        passed_all = all(c["passed"] for c in checks)
        failed_count = sum(1 for c in checks if not c["passed"])
        score = max(0, 100 - failed_count * 10)

        return {
            "passed_all": passed_all,
            "checks": checks,
            "score": score,
        }

    def _check_word_count(self, content: str) -> dict:
        """检查中文字数是否在 500-3000 之间。"""
        chinese_chars = re.findall(r"[一-鿿]", content)
        count = len(chinese_chars)
        passed = 500 <= count <= 3000
        return {
            "name": "字数检查",
            "passed": passed,
            "message": f"中文字符数: {count} (标准: 500-3000)" if passed else f"字数不合格: {count} (标准: 500-3000)",
            "detail": {"count": count, "min": 500, "max": 3000},
        }

    def _check_required_fields(self, case: dict) -> dict:
        """检查必填字段是否存在且非空。"""
        missing = []
        # 直接字段
        for field in ["title"]:
            if not case.get(field):
                missing.append(field)
        # 内容中需包含的字段（用关键词匹配）
        content = case.get("content", "")
        field_keywords = {
            "适用课程": ["适用课程", "课程", "教学场景"],
            "素材类型": ["素材类型", "类型"],
            "素材性质": ["素材性质", "性质", "正面", "负面", "中性"],
            "主打思政主题": ["主打思政主题", "思政主题", "主题"],
        }
        for field, keywords in field_keywords.items():
            if not any(kw in content for kw in keywords) and not case.get(field):
                missing.append(field)

        passed = len(missing) == 0
        return {
            "name": "必填字段检查",
            "passed": passed,
            "message": "所有必填字段已填写" if passed else f"缺少字段: {', '.join(missing)}",
            "detail": {"missing": missing},
        }

    def _detect_template_type(self, content: str) -> Optional[str]:
        """根据内容关键词判断模板类型。"""
        scores = {}
        for template, keywords in self.TEMPLATE_KEYWORDS.items():
            scores[template] = sum(1 for kw in keywords if kw in content)
        if not scores:
            return None
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else None

    def _check_structure(self, content: str) -> dict:
        """检查案例结构完整性（按模板类型）。"""
        template = self._detect_template_type(content)
        if template is None:
            # 无法判断模板类型时，检查是否至少有一些常见结构
            common_sections = ["讨论问题", "思政", "案例"]
            found = sum(1 for s in common_sections if s in content)
            passed = found >= 2
            return {
                "name": "结构完整性检查",
                "passed": passed,
                "message": "无法判断模板类型，但包含基本结构" if passed else "无法识别案例结构",
                "detail": {"template": None, "found_sections": found},
            }

        required = self.TEMPLATE_STRUCTURES.get(template, [])
        missing = [s for s in required if s not in content]
        passed = len(missing) == 0
        return {
            "name": "结构完整性检查",
            "passed": passed,
            "message": f"模板{template}结构完整" if passed else f"模板{template}缺少: {', '.join(missing)}",
            "detail": {"template": template, "missing": missing, "required": required},
        }

    def _check_discussion_questions(self, content: str) -> dict:
        """检查讨论问题数量是否 >= 2。"""
        # 匹配讨论问题章节后的列表项
        # 先找到"讨论问题"之后的内容
        match = re.search(r"讨论问题[\s\S]*?(?=# \[|#{1,2}\s|$)", content)
        section = match.group(0) if match else content

        # 统计以 -、•、数字开头的行
        questions = re.findall(r"^[\s]*[-•*\d][\.\、\)]*[\s]+", section, re.MULTILINE)
        count = len(questions)
        passed = count >= 2
        return {
            "name": "讨论问题数量检查",
            "passed": passed,
            "message": f"讨论问题数: {count} (要求 >= 2)" if passed else f"讨论问题不足: {count} (要求 >= 2)",
            "detail": {"count": count, "required": 2},
        }

    def _check_source_attribution(self, content: str) -> dict:
        """检查是否有素材来源标注。"""
        keywords = ["素材来源", "来源", "原文链接", "参考", "出处"]
        found = any(kw in content for kw in keywords)
        return {
            "name": "素材来源检查",
            "passed": found,
            "message": "已标注素材来源" if found else "未找到素材来源标注",
            "detail": {"keywords_found": [k for k in keywords if k in content]},
        }

    def _check_negative_case_exit(self, content: str, material_nature: str) -> dict:
        """负面案例检查是否有制度回应/纠错过程。"""
        is_negative = (
            "negative" in material_nature.lower()
            or "反面" in material_nature
            or "负面" in material_nature
        )
        if not is_negative:
            return {
                "name": "负面案例出口检查",
                "passed": True,
                "message": "非负面案例，跳过",
                "detail": {"is_negative": False},
            }

        exit_keywords = ["制度回应", "纠错", "改进", "处理结果", "整改", "institutional response", "corrected", "improved"]
        found = any(kw in content for kw in exit_keywords)
        return {
            "name": "负面案例出口检查",
            "passed": found,
            "message": "负面案例已包含制度回应/纠错过程" if found else "负面案例缺少制度回应/纠错过程",
            "detail": {"is_negative": True, "exit_found": found},
        }


# ---------------------------------------------------------------------------
# SoftAuditor
# ---------------------------------------------------------------------------

_SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "audit" / "SKILL.md"


class SoftAuditor:
    """AI 辅助软审核器 —— 标记疑似问题，不自动拦截。"""

    def __init__(self, llm_client=None) -> None:
        self._llm_client = llm_client

    def _build_system_prompt(self) -> str:
        """读取 SKILL.md 并构造软审核系统提示词。"""
        if not _SKILL_PATH.exists():
            raise FileNotFoundError(f"审核标准文件不存在: {_SKILL_PATH}")
        skill_doc = _SKILL_PATH.read_text(encoding="utf-8")
        return (
            "你是一名思政案例库的质量审核助手。请对以下案例进行软审核，"
            "标记疑似问题但不做出通过/不通过判断。\n\n"
            "审核维度：\n"
            "1. style_risk — 风格风险（过度宣传、拔高渲染、说教式表达）\n"
            "2. phrasing_risk — 表述风险（可能引发歧义、敏感话题未充分说明、价值判断过于绝对）\n"
            "3. factual_concern — 事实存疑（数据/日期/政策文件缺少来源、关键事实无法追溯）\n"
            "4. teaching_value — 教学价值（讨论问题是否有效、案例与知识点联结是否自然）\n\n"
            "严重级别：suggestion（建议）、concern（关注）、warning（警告）。\n"
            "注意：teaching_value 仅使用 suggestion 级别。\n\n"
            "请严格按以下 JSON 格式返回（不要添加任何额外文字）：\n"
            '{"findings": [{"category": "style_risk", "severity": "concern", '
            '"description": "...", "location": "...", "recommendation": "..."}]}\n\n'
            f"=== 审核标准文档 ===\n{skill_doc}"
        )

    def audit(self, case: dict) -> dict:
        """对案例执行软审核。

        Args:
            case: 案例字典

        Returns:
            {"findings": list[dict], "finding_count": int, "has_warnings": bool, "error": str or None}
        """
        if self._llm_client is None:
            return {
                "findings": [],
                "finding_count": 0,
                "has_warnings": False,
                "error": "LLM client not provided",
            }

        title = case.get("title", "")
        content = case.get("content", "")

        system_prompt = self._build_system_prompt()
        user_prompt = (
            f"案例标题：{title}\n\n"
            f"案例内容：\n{content}\n\n"
            f"请按 JSON 格式返回软审核发现项。"
        )

        try:
            response = self._llm_client.chat_completion_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000,
            )
        except Exception as exc:
            return {
                "findings": [],
                "finding_count": 0,
                "has_warnings": False,
                "error": str(exc),
            }

        if not isinstance(response, dict):
            return {
                "findings": [],
                "finding_count": 0,
                "has_warnings": False,
                "error": f"LLM 返回格式错误: {response!r}",
            }

        findings = response.get("findings", [])
        if not isinstance(findings, list):
            findings = []

        # 规范化 findings
        valid_categories = {"style_risk", "phrasing_risk", "factual_concern", "teaching_value"}
        valid_severities = {"suggestion", "concern", "warning"}
        normalized = []
        for f in findings:
            if not isinstance(f, dict):
                continue
            cat = f.get("category", "")
            sev = f.get("severity", "suggestion")
            if cat not in valid_categories:
                cat = "style_risk"
            if sev not in valid_severities:
                sev = "suggestion"
            normalized.append({
                "category": cat,
                "severity": sev,
                "description": str(f.get("description", "")),
                "location": str(f.get("location", "")),
                "recommendation": str(f.get("recommendation", "")),
            })

        has_warnings = any(f["severity"] == "warning" for f in normalized)

        return {
            "findings": normalized,
            "finding_count": len(normalized),
            "has_warnings": has_warnings,
            "error": None,
        }


# ---------------------------------------------------------------------------
# Fact verification integration
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://[^\s\)\]\>\"\']+", re.IGNORECASE)


def _extract_sources(content: str) -> List[str]:
    """从案例内容中提取 URL。"""
    return _URL_RE.findall(content)


def _verify_sources(content: str) -> dict:
    """对内容中的 URL 进行事实核查。"""
    urls = _extract_sources(content)
    if not urls:
        return {"verified_claims": [], "unverified_claims": [], "has_issues": False}

    results = []
    has_issues = False
    for url in urls:
        # 用 URL 本身作为 "claim" 进行验证（简化：验证 URL 可访问）
        result = verify_claim(url, [url])
        results.append(result)
        if not result["verified"]:
            has_issues = True

    verified = [r for r in results if r["verified"]]
    unverified = [r for r in results if not r["verified"]]

    return {
        "verified_claims": verified,
        "unverified_claims": unverified,
        "has_issues": has_issues,
    }


# ---------------------------------------------------------------------------
# AuditReport
# ---------------------------------------------------------------------------

_BEIJING_TZ = timezone(timedelta(hours=8))


class AuditReport:
    """审核报告，整合硬审核、软审核和事实核查结果。"""

    def __init__(
        self,
        case_id: str,
        case_title: str,
        hard_result: dict,
        soft_result: dict,
        fact_result: dict,
        timestamp: Optional[str] = None,
    ):
        self.case_id = case_id
        self.case_title = case_title
        self.hard_result = hard_result
        self.soft_result = soft_result
        self.fact_result = fact_result
        self.timestamp = timestamp or datetime.now(_BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        self.overall_status = self._determine_status()

    def _determine_status(self) -> str:
        score = self.hard_result.get("score", 0)
        if score < 60:
            return "rejected"
        if score >= 80:
            soft_has_warnings = self.soft_result.get("has_warnings", False)
            fact_has_issues = self.fact_result.get("has_issues", False)
            if not soft_has_warnings and not fact_has_issues:
                return "passed"
        return "needs_review"

    def to_markdown(self) -> str:
        """生成人工可读的中文审核报告。"""
        lines = [
            f"# 案例审核报告：{self.case_title}",
            "",
            f"- **案例编号**: {self.case_id}",
            f"- **审核时间**: {self.timestamp}",
            f"- **综合状态**: {self._status_label(self.overall_status)}",
            "",
            "---",
            "",
            "## 硬审核结果",
            "",
            f"**综合评分**: {self.hard_result.get('score', 0)} / 100",
            "",
            "| 检查项 | 结果 | 说明 |",
            "|--------|------|------|",
        ]
        for check in self.hard_result.get("checks", []):
            status = "✅ 通过" if check["passed"] else "❌ 未通过"
            lines.append(f"| {check['name']} | {status} | {check['message']} |")

        lines.extend(["", "## 软审核发现", ""])
        findings = self.soft_result.get("findings", [])
        if findings:
            lines.append(f"共发现 **{len(findings)}** 项：")
            lines.append("")
            for i, f in enumerate(findings, 1):
                sev_label = self._severity_label(f.get("severity", "suggestion"))
                lines.append(f"### {i}. [{sev_label}] {f.get('category', '')}")
                lines.append(f"- **位置**: {f.get('location', '未指定')}")
                lines.append(f"- **描述**: {f.get('description', '')}")
                lines.append(f"- **建议**: {f.get('recommendation', '')}")
                lines.append("")
        else:
            lines.append("未发现明显问题。")

        lines.extend(["", "## 事实核查", ""])
        verified = self.fact_result.get("verified_claims", [])
        unverified = self.fact_result.get("unverified_claims", [])
        if verified or unverified:
            lines.append(f"- **已验证来源**: {len(verified)}")
            lines.append(f"- **未验证来源**: {len(unverified)}")
            if unverified:
                lines.append("")
                lines.append("**未验证详情**:")
                for u in unverified:
                    lines.append(f"- {u.get('claim', '')}: {u.get('summary', '')}")
        else:
            lines.append("案例中未检测到需要核查的 URL 或引用。")

        lines.extend(["", "---", "", "## 综合评估", ""])
        lines.append(self._overall_summary())
        lines.append("")

        return "\n".join(lines)

    def _status_label(self, status: str) -> str:
        labels = {
            "passed": "✅ 审核通过",
            "needs_review": "⚠️ 需人工复核",
            "rejected": "❌ 退回修改",
        }
        return labels.get(status, status)

    def _severity_label(self, severity: str) -> str:
        labels = {
            "suggestion": "建议",
            "concern": "关注",
            "warning": "警告",
        }
        return labels.get(severity, severity)

    def _overall_summary(self) -> str:
        if self.overall_status == "passed":
            return "案例通过全部自动化审核，格式合规、无明显风险项，建议入库。"
        if self.overall_status == "rejected":
            return f"案例硬审核评分过低（{self.hard_result.get('score', 0)}分），存在严重格式问题，请修改后重新提交。"
        # needs_review
        reasons = []
        if self.soft_result.get("has_warnings"):
            reasons.append("软审核发现警告级别问题")
        if self.fact_result.get("has_issues"):
            reasons.append("事实核查存在未验证项")
        if self.hard_result.get("score", 0) < 80:
            reasons.append("硬审核评分未达优秀标准")
        reason_str = "；".join(reasons) if reasons else "存在需要关注的事项"
        return f"案例基本合规，但 {reason_str}，建议人工复核后决定是否入库。"

    def to_dict(self) -> dict:
        """导出为字典（供 API 返回或序列化）。"""
        return {
            "case_id": self.case_id,
            "case_title": self.case_title,
            "hard_result": self.hard_result,
            "soft_result": self.soft_result,
            "fact_result": self.fact_result,
            "overall_status": self.overall_status,
            "timestamp": self.timestamp,
            "report_md": self.to_markdown(),
        }


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def audit_case(case: dict, llm_client=None) -> AuditReport:
    """对单个案例执行完整审核流程。

    Args:
        case: 案例字典，至少包含 title 和 content
        llm_client: 可选的 LLMClient 实例（用于软审核）

    Returns:
        AuditReport 实例
    """
    case_id = case.get("id", case.get("title", "unknown"))
    case_title = case.get("title", "未命名案例")

    # 硬审核
    hard_auditor = HardAuditor()
    hard_result = hard_auditor.audit(case)

    # 软审核
    soft_auditor = SoftAuditor(llm_client=llm_client)
    soft_result = soft_auditor.audit(case)

    # 事实核查
    fact_result = _verify_sources(case.get("content", ""))

    return AuditReport(
        case_id=case_id,
        case_title=case_title,
        hard_result=hard_result,
        soft_result=soft_result,
        fact_result=fact_result,
    )


if __name__ == "__main__":
    # 冒烟测试：使用一个简单案例
    test_case = {
        "title": "测试案例",
        "content": (
            "本案例围绕新时代青年理想信念教育展开。\n\n"
            "【情境还原】某高校学生面临职业选择...\n\n"
            "【冲突与抉择】在理想与现实之间...\n\n"
            "【行动与结果】最终选择扎根基层...\n\n"
            "【思政映射】体现了把个人理想融入国家战略的价值导向。\n\n"
            "【讨论问题】\n"
            "1. 如果你是主人公，你会如何选择？\n"
            "2. 个人理想与国家需要如何平衡？\n\n"
            "素材来源：某高校官方公众号，2026年4月。\n"
            "适用课程：思想道德与法治\n"
            "素材类型：新闻事件\n"
            "素材性质：正面典型\n"
            "主打思政主题：家国情怀"
        ),
    }
    report = audit_case(test_case)
    print(f"Overall status: {report.overall_status}")
    print(f"Hard score: {report.hard_result['score']}")
    print(report.to_markdown()[:500] + "...")
