"""事实核查模块 —— 网页抓取与声明验证。

提供网页内容获取、HTML 文本提取、以及基于来源 URL 的声明验证功能。
被审核 skill 可直接调用 `verify_claim()` 或 `FactVerifier` 类进行素材真实性验证。

依赖：仅使用 Python 标准库（urllib, html.parser, re 等）。
"""

import re
from html.parser import HTMLParser
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class _TextExtractor(HTMLParser):
    """简单的 HTML 文本提取器，忽略标签，只收集文本内容。"""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip_tags = {"script", "style", "noscript", "iframe", "canvas"}
        self._in_skip = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in self._skip_tags:
            self._in_skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._skip_tags:
            self._in_skip -= 1

    def handle_data(self, data: str) -> None:
        if self._in_skip <= 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        text = "".join(self._pieces)
        # 合并空白字符
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def extract_text_from_html(html: str) -> str:
    """从 HTML 字符串中提取纯文本内容。

    Args:
        html: 原始 HTML 字符串

    Returns:
        去除标签后的纯文本，空白字符已合并
    """
    if not html:
        return ""
    extractor = _TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        # HTML 解析失败时回退到正则
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    return extractor.get_text()


def fetch_url(url: str, timeout: int = 10) -> dict:
    """获取指定 URL 的网页内容。

    Args:
        url: 目标网址
        timeout: 超时时间（秒），默认 10 秒

    Returns:
        {
            "success": bool,
            "url": str,
            "status_code": int,
            "content": str,
            "error": str or None
        }
    """
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CaseLibraryBot/1.0)",
        },
    )

    try:
        with urlopen(req, timeout=timeout) as response:
            final_url = response.geturl() or url
            status_code = response.getcode()

            # 读取原始字节
            raw_bytes = response.read()

            # 尝试解码
            content_type = response.headers.get("Content-Type", "")
            charset = None
            if "charset=" in content_type:
                match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
                if match:
                    charset = match.group(1)

            if charset:
                try:
                    content = raw_bytes.decode(charset, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    content = raw_bytes.decode("utf-8", errors="replace")
            else:
                # 先尝试 UTF-8，失败则替换
                content = raw_bytes.decode("utf-8", errors="replace")

            # 提取文本并截断到 5000 字符
            text = extract_text_from_html(content)
            if len(text) > 5000:
                text = text[:5000]

            return {
                "success": True,
                "url": final_url,
                "status_code": status_code,
                "content": text,
                "error": None,
            }

    except HTTPError as exc:
        return {
            "success": False,
            "url": url,
            "status_code": exc.code,
            "content": "",
            "error": f"HTTP {exc.code}",
        }
    except URLError as exc:
        error_msg = str(exc.reason) if hasattr(exc, "reason") else str(exc)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = "timeout"
        return {
            "success": False,
            "url": url,
            "status_code": 0,
            "content": "",
            "error": error_msg,
        }
    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "status_code": 0,
            "content": "",
            "error": str(exc),
        }


def _extract_snippet(text: str, claim: str, radius: int = 100) -> Optional[str]:
    """在文本中提取声明附近的片段。"""
    lower_text = text.lower()
    lower_claim = claim.lower()
    idx = lower_text.find(lower_claim)
    if idx == -1:
        return None
    start = max(0, idx - radius)
    end = min(len(text), idx + len(claim) + radius)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def verify_claim(claim: str, sources: Optional[List[str]] = None) -> dict:
    """验证声明在给定的来源 URL 中是否出现。

    Args:
        claim: 要验证的声明文本
        sources: 来源 URL 列表

    Returns:
        {
            "claim": str,
            "verified": bool,
            "confidence": str ("high"/"medium"/"low"/"none"),
            "evidence": list[dict],
            "summary": str
        }
    """
    if not sources:
        return {
            "claim": claim,
            "verified": False,
            "confidence": "none",
            "evidence": [],
            "summary": "未提供来源，无法验证",
        }

    evidence = []
    found_count = 0
    failed_count = 0

    for url in sources:
        result = fetch_url(url)
        if not result["success"]:
            failed_count += 1
            evidence.append({
                "url": url,
                "found": False,
                "snippet": None,
                "status": f"fetch_failed: {result.get('error', 'unknown')}",
            })
            continue

        text = result["content"]
        lower_text = text.lower()
        lower_claim = claim.lower()

        # 检查完整声明或关键短语
        found = lower_claim in lower_text
        snippet = _extract_snippet(text, claim) if found else None

        if found:
            found_count += 1

        evidence.append({
            "url": result["url"],
            "found": found,
            "snippet": snippet,
            "status": "found" if found else "not_found",
        })

    # 确定 confidence
    if found_count >= 2:
        confidence = "high"
    elif found_count == 1:
        confidence = "medium"
    elif failed_count == len(sources):
        confidence = "none"
    else:
        confidence = "low"

    verified = found_count > 0

    if verified:
        summary = f"在 {found_count}/{len(sources)} 个来源中找到匹配"
    elif failed_count == len(sources):
        summary = f"所有 {len(sources)} 个来源均无法访问"
    else:
        summary = f"来源可访问但未找到声明内容（检查了 {len(sources) - failed_count} 个来源）"

    return {
        "claim": claim,
        "verified": verified,
        "confidence": confidence,
        "evidence": evidence,
        "summary": summary,
    }


class FactVerifier:
    """有状态的事实核查器，支持批量验证。"""

    def __init__(self, llm_client=None) -> None:
        self._llm_client = llm_client

    def verify(self, claim: str, sources: List[str]) -> dict:
        """验证单个声明。

        Args:
            claim: 要验证的声明
            sources: 来源 URL 列表

        Returns:
            verify_claim 的返回结果
        """
        return verify_claim(claim, sources)

    def batch_verify(self, claims: List[dict]) -> List[dict]:
        """批量验证多个声明。

        Args:
            claims: 每个元素为 {"claim": str, "sources": [...]}

        Returns:
            与输入顺序对应的验证结果列表
        """
        results = []
        for item in claims:
            claim = item.get("claim", "")
            sources = item.get("sources", [])
            result = verify_claim(claim, sources)
            results.append(result)
        return results


if __name__ == "__main__":
    url = "https://www.gov.cn"
    print(f"Fetching {url} ...")
    result = fetch_url(url, timeout=15)
    if result["success"]:
        print(f"Success! Status: {result['status_code']}, Content length: {len(result['content'])}")
    else:
        print(f"Failed: {result['error']}")
