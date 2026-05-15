"""审核 Skill 单元测试与集成测试。

运行方式：
  - 仅硬审核（无 LLM）：pytest tests/test_audit_skill.py -v -m unit
  - 集成测试：pytest tests/test_audit_skill.py -v -m integration
  - 全部：pytest tests/test_audit_skill.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.audit_skill import (
    AuditReport,
    HardAuditor,
    SoftAuditor,
    audit_case,
)


# ===========================================================================
# Hard audit tests (no LLM, no network)
# ===========================================================================

@pytest.mark.unit
def test_hard_audit_word_count_pass():
    auditor = HardAuditor()
    content = "这是一段测试内容。" * 200  # ~400 中文字符
    result = auditor._check_word_count(content)
    assert result["passed"] is True
    assert result["detail"]["count"] >= 500


@pytest.mark.unit
def test_hard_audit_word_count_fail_short():
    auditor = HardAuditor()
    content = "这是一段短内容。"
    result = auditor._check_word_count(content)
    assert result["passed"] is False
    assert result["detail"]["count"] < 500


@pytest.mark.unit
def test_hard_audit_word_count_fail_long():
    auditor = HardAuditor()
    content = "这是一段很长的测试内容。" * 2000  # ~40000 中文字符
    result = auditor._check_word_count(content)
    assert result["passed"] is False
    assert result["detail"]["count"] > 3000


@pytest.mark.unit
def test_hard_audit_required_fields_pass():
    auditor = HardAuditor()
    case = {
        "title": "测试案例",
        "content": (
            "适用课程：思想道德与法治\n"
            "素材类型：新闻事件\n"
            "素材性质：正面典型\n"
            "主打思政主题：家国情怀"
        ),
    }
    result = auditor._check_required_fields(case)
    assert result["passed"] is True


@pytest.mark.unit
def test_hard_audit_required_fields_fail():
    auditor = HardAuditor()
    case = {
        "title": "",
        "content": "缺少大部分必填字段的内容",
    }
    result = auditor._check_required_fields(case)
    assert result["passed"] is False
    assert "missing" in result["detail"]


@pytest.mark.unit
def test_hard_audit_structure_template_a():
    auditor = HardAuditor()
    content = (
        "【情境还原】某事件...\n"
        "【冲突与抉择】面临选择...\n"
        "【行动与结果】最终结果...\n"
        "【思政映射】价值点...\n"
        "【讨论问题】\n1. 问题一\n2. 问题二"
    )
    result = auditor._check_structure(content)
    assert result["passed"] is True
    assert result["detail"]["template"] == "A"


@pytest.mark.unit
def test_hard_audit_structure_template_b():
    auditor = HardAuditor()
    content = (
        "【现象层】观察到...\n"
        "【本质层】原理是...\n"
        "【价值层】体现了...\n"
        "【讨论问题】\n1. 专业问题\n2. 思政问题"
    )
    result = auditor._check_structure(content)
    assert result["passed"] is True
    assert result["detail"]["template"] == "B"


@pytest.mark.unit
def test_hard_audit_discussion_questions_pass():
    auditor = HardAuditor()
    content = "【讨论问题】\n1. 问题一\n2. 问题二\n3. 问题三"
    result = auditor._check_discussion_questions(content)
    assert result["passed"] is True
    assert result["detail"]["count"] >= 2


@pytest.mark.unit
def test_hard_audit_discussion_questions_fail():
    auditor = HardAuditor()
    content = "【讨论问题】\n1. 只有一个问题"
    result = auditor._check_discussion_questions(content)
    assert result["passed"] is False
    assert result["detail"]["count"] < 2


@pytest.mark.unit
def test_hard_audit_negative_case_no_exit():
    auditor = HardAuditor()
    content = "A negative case with no exit mechanism at all."
    result = auditor._check_negative_case_exit(content, "negative_case")
    assert result["passed"] is False


@pytest.mark.unit
def test_hard_audit_negative_case_with_exit():
    auditor = HardAuditor()
    content = "A negative case. Institutional response: school has corrected."
    result = auditor._check_negative_case_exit(content, "negative_case")
    assert result["passed"] is True


@pytest.mark.unit
def test_hard_audit_overall_score():
    auditor = HardAuditor()
    case = {
        "title": "测试",
        "content": (
            "【情境还原】某事件发生了一些重要的事情需要详细描述...\n"
            "【冲突与抉择】面临选择时需要考虑多方面因素和权衡利弊...\n"
            "【行动与结果】最终结果展示了积极的价值导向和社会意义...\n"
            "【思政映射】价值点体现在个人理想与国家需要的有机结合...\n"
            "【讨论问题】\n1. 问题一是关于事实理解层面的基础问题\n"
            "2. 问题二是关于价值分析层面的深入思考\n"
            "素材来源：某高校官方公众号2026年4月报道\n"
            "适用课程：思想道德与法治课程\n"
            "素材类型：新闻事件类素材\n"
            "素材性质：正面典型案例\n"
            "主打思政主题：家国情怀与理想信念\n"
            + "正文内容补充说明。" * 150  # 确保字数超过500
        ),
    }
    result = auditor.audit(case)
    assert result["score"] == 100  # 全部通过
    assert result["passed_all"] is True


# ===========================================================================
# Soft audit tests (mocked LLM)
# ===========================================================================

@pytest.mark.unit
def test_soft_audit_format():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {
        "findings": [
            {
                "category": "style_risk",
                "severity": "concern",
                "description": "存在说教式表达",
                "location": "价值层",
                "recommendation": "改为启发式提问",
            },
            {
                "category": "teaching_value",
                "severity": "suggestion",
                "description": "可以增加对比视角",
                "location": "讨论问题",
                "recommendation": "补充反面观点",
            },
        ]
    }

    auditor = SoftAuditor(llm_client=mock_llm)
    result = auditor.audit({"title": "测试", "content": "测试内容"})

    assert result["finding_count"] == 2
    assert len(result["findings"]) == 2
    finding = result["findings"][0]
    assert "category" in finding
    assert "severity" in finding
    assert "description" in finding
    assert "location" in finding
    assert "recommendation" in finding


@pytest.mark.unit
def test_soft_audit_no_warnings():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {
        "findings": [
            {"category": "teaching_value", "severity": "suggestion", "description": "建议", "location": "", "recommendation": ""}
        ]
    }

    auditor = SoftAuditor(llm_client=mock_llm)
    result = auditor.audit({"title": "测试", "content": "测试内容"})
    assert result["has_warnings"] is False


@pytest.mark.unit
def test_soft_audit_with_warnings():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {
        "findings": [
            {"category": "style_risk", "severity": "warning", "description": "严重说教", "location": "", "recommendation": ""}
        ]
    }

    auditor = SoftAuditor(llm_client=mock_llm)
    result = auditor.audit({"title": "测试", "content": "测试内容"})
    assert result["has_warnings"] is True


@pytest.mark.unit
def test_soft_audit_llm_failure():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.side_effect = RuntimeError("API error")

    auditor = SoftAuditor(llm_client=mock_llm)
    result = auditor.audit({"title": "测试", "content": "测试内容"})
    assert result["findings"] == []
    assert result["finding_count"] == 0
    assert result["error"] is not None


# ===========================================================================
# Integration tests
# ===========================================================================

@pytest.mark.integration
def test_audit_case_overall_passed():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {"findings": []}

    case = {
        "title": "优秀案例",
        "content": (
            "【情境还原】某事件...\n"
            "【冲突与抉择】面临选择...\n"
            "【行动与结果】最终结果...\n"
            "【思政映射】价值点...\n"
            "【讨论问题】\n1. 问题一\n2. 问题二\n"
            "素材来源：某公众号\n"
            "适用课程：思政课\n"
            "素材类型：新闻\n"
            "素材性质：正面典型\n"
            "主打思政主题：家国情怀\n"
            + "正文内容。" * 100
        ),
    }
    report = audit_case(case, llm_client=mock_llm)
    assert report.overall_status == "passed"


@pytest.mark.integration
def test_audit_case_overall_needs_review():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {
        "findings": [
            {"category": "style_risk", "severity": "warning", "description": "问题", "location": "", "recommendation": ""}
        ]
    }

    case = {
        "title": "有问题的案例",
        "content": (
            "【情境还原】某事件...\n"
            "【冲突与抉择】面临选择...\n"
            "【行动与结果】最终结果...\n"
            "【思政映射】价值点...\n"
            "【讨论问题】\n1. 问题一\n2. 问题二\n"
            "素材来源：某公众号\n"
            "适用课程：思政课\n"
            "素材类型：新闻\n"
            "素材性质：正面典型\n"
            "主打思政主题：家国情怀\n"
            + "正文内容。" * 100
        ),
    }
    report = audit_case(case, llm_client=mock_llm)
    assert report.overall_status == "needs_review"


@pytest.mark.integration
def test_audit_case_overall_rejected():
    case = {
        "title": "",
        "content": "太短",
    }
    report = audit_case(case)
    assert report.overall_status == "rejected"
    assert report.hard_result["score"] < 60


@pytest.mark.integration
def test_audit_report_markdown():
    mock_llm = MagicMock()
    mock_llm.chat_completion_json.return_value = {"findings": []}

    case = {
        "title": "测试报告",
        "content": (
            "【情境还原】某事件...\n"
            "【冲突与抉择】面临选择...\n"
            "【行动与结果】最终结果...\n"
            "【思政映射】价值点...\n"
            "【讨论问题】\n1. 问题一\n2. 问题二\n"
            "素材来源：某公众号\n"
            "适用课程：思政课\n"
            "素材类型：新闻\n"
            "素材性质：正面典型\n"
            "主打思政主题：家国情怀\n"
            + "正文内容。" * 100
        ),
    }
    report = audit_case(case, llm_client=mock_llm)
    md = report.to_markdown()
    assert "硬审核结果" in md
    assert "软审核发现" in md
    assert "综合评估" in md
    assert "事实核查" in md
