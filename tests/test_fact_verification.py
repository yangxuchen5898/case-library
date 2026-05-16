"""事实核查模块的单元测试（全部使用 Mock，不发起真实网络请求）。"""

from unittest.mock import MagicMock, patch

import pytest

from backend.fact_verification import (
    FactVerifier,
    extract_text_from_html,
    fetch_url,
    verify_claim,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# extract_text_from_html
# ---------------------------------------------------------------------------

def test_extract_text_strips_tags():
    html = "<p>Hello <b>world</b></p>"
    result = extract_text_from_html(html)
    assert result == "Hello world"


def test_extract_text_empty():
    assert extract_text_from_html("") == ""


def test_extract_text_with_script_and_style():
    html = "<div>正文<script>alert('x')</script><style>.x{}</style>结束</div>"
    result = extract_text_from_html(html)
    assert "正文" in result
    assert "alert" not in result
    assert "style" not in result
    assert "结束" in result


# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------

def _make_mock_response(body: bytes, code: int = 200, final_url: str = None):
    """构造一个可被 urlopen 返回的 mock response 对象。"""
    mock = MagicMock()
    mock.read.return_value = body
    mock.getcode.return_value = code
    mock.geturl.return_value = final_url or "http://example.com/final"
    mock.headers = {"Content-Type": "text/html; charset=utf-8"}
    return mock


@patch("backend.fact_verification.urlopen")
def test_fetch_url_success(mock_urlopen):
    html = "<html><body>测试内容</body></html>".encode("utf-8")
    mock_urlopen.return_value = _make_mock_response(html, 200, "http://example.com")

    result = fetch_url("http://example.com")
    assert result["success"] is True
    assert result["status_code"] == 200
    assert "测试内容" in result["content"]
    assert result["error"] is None


@patch("backend.fact_verification.urlopen")
def test_fetch_url_http_error(mock_urlopen):
    from urllib.error import HTTPError

    mock_urlopen.side_effect = HTTPError(
        "http://example.com", 404, "Not Found", {}, None
    )

    result = fetch_url("http://example.com")
    assert result["success"] is False
    assert "404" in result["error"]


@patch("backend.fact_verification.urlopen")
def test_fetch_url_timeout(mock_urlopen):
    from urllib.error import URLError

    mock_urlopen.side_effect = URLError("timed out")

    result = fetch_url("http://example.com")
    assert result["success"] is False
    assert "timeout" in result["error"].lower()


@patch("backend.fact_verification.urlopen")
def test_fetch_url_redirect(mock_urlopen):
    html = "<html><body>redirected</body></html>".encode("utf-8")
    mock_urlopen.return_value = _make_mock_response(
        html, 200, "http://example.com/final-page"
    )

    result = fetch_url("http://example.com")
    assert result["success"] is True
    assert result["url"] == "http://example.com/final-page"


# ---------------------------------------------------------------------------
# verify_claim
# ---------------------------------------------------------------------------

@patch("backend.fact_verification.fetch_url")
def test_verify_claim_found(mock_fetch):
    mock_fetch.return_value = {
        "success": True,
        "url": "http://example.com",
        "content": "这是关于人工智能发展的重要政策文件",
        "error": None,
    }

    result = verify_claim("人工智能发展", ["http://example.com"])
    assert result["verified"] is True
    assert result["confidence"] == "medium"
    assert result["evidence"][0]["found"] is True
    assert "人工智能发展" in result["evidence"][0]["snippet"]


@patch("backend.fact_verification.fetch_url")
def test_verify_claim_not_found(mock_fetch):
    mock_fetch.return_value = {
        "success": True,
        "url": "http://example.com",
        "content": "这是关于环境保护的内容",
        "error": None,
    }

    result = verify_claim("人工智能发展", ["http://example.com"])
    assert result["verified"] is False
    assert result["confidence"] == "low"
    assert result["evidence"][0]["found"] is False


@patch("backend.fact_verification.fetch_url")
def test_verify_claim_multiple_sources(mock_fetch):
    def side_effect(url, **kwargs):
        if "source1" in url:
            return {
                "success": True,
                "url": url,
                "content": "人工智能发展政策",
                "error": None,
            }
        else:
            return {
                "success": True,
                "url": url,
                "content": "其他内容",
                "error": None,
            }

    mock_fetch.side_effect = side_effect

    result = verify_claim("人工智能发展", ["http://source1.com", "http://source2.com"])
    assert result["verified"] is True
    assert result["confidence"] == "medium"


@patch("backend.fact_verification.fetch_url")
def test_verify_claim_no_sources(mock_fetch):
    result = verify_claim("人工智能发展", [])
    assert result["verified"] is False
    assert result["confidence"] == "none"
    assert "未提供来源" in result["summary"]


@patch("backend.fact_verification.fetch_url")
def test_verify_claim_fetch_failure(mock_fetch):
    mock_fetch.return_value = {
        "success": False,
        "url": "http://example.com",
        "content": "",
        "error": "connection refused",
    }

    result = verify_claim("人工智能发展", ["http://example.com"])
    assert result["verified"] is False
    assert result["confidence"] == "none"
    assert result["evidence"][0]["status"].startswith("fetch_failed")


# ---------------------------------------------------------------------------
# FactVerifier
# ---------------------------------------------------------------------------

@patch("backend.fact_verification.fetch_url")
def test_fact_verifier_verify(mock_fetch):
    mock_fetch.return_value = {
        "success": True,
        "url": "http://example.com",
        "content": "测试内容匹配",
        "error": None,
    }

    verifier = FactVerifier()
    result = verifier.verify("测试内容", ["http://example.com"])
    assert isinstance(result, dict)
    assert result["verified"] is True


@patch("backend.fact_verification.fetch_url")
def test_fact_verifier_batch_verify(mock_fetch):
    mock_fetch.return_value = {
        "success": True,
        "url": "http://example.com",
        "content": "批量测试内容",
        "error": None,
    }

    verifier = FactVerifier()
    claims = [
        {"claim": "批量测试", "sources": ["http://example.com"]},
        {"claim": "不存在的内容", "sources": ["http://example.com"]},
    ]
    results = verifier.batch_verify(claims)
    assert len(results) == 2
    assert isinstance(results[0], dict)
    assert isinstance(results[1], dict)
