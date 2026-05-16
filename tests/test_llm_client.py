from unittest.mock import patch

from backend.llm_client import LLMClient


class TestSupportsJsonMode:
    def test_json_mode_supported_uses_response_format(self):
        """支持 JSON mode 的模型使用 response_format 参数。"""
        client = LLMClient.__new__(LLMClient)
        client.model = "deepseek-chat"
        assert client._supports_json_mode() is True

    def test_json_mode_unsupported_falls_back(self):
        """不支持 JSON mode 的模型降级为文本提取。"""
        client = LLMClient.__new__(LLMClient)
        client.model = "unknown-model"
        assert client._supports_json_mode() is False


class TestExtractJsonFromText:
    def test_extract_json_nested_braces(self):
        """嵌套 JSON 对象能正确提取，不被截断。"""
        client = LLMClient.__new__(LLMClient)
        client._client = None
        with patch.object(
            client, "chat_completion", return_value='前缀 {"a": {"b": 1}} 后缀'
        ):
            result = client._extract_json_from_text("sys", "user", 0.3, 2000)
            assert result == '{"a": {"b": 1}}'

    def test_extract_json_multiple_blocks(self):
        """文本中有多个 JSON 块时提取第一个有效的。"""
        client = LLMClient.__new__(LLMClient)
        client._client = None
        with patch.object(
            client,
            "chat_completion",
            return_value='{"first": 1} 中间文字 {"second": 2}',
        ):
            result = client._extract_json_from_text("sys", "user", 0.3, 2000)
            assert result == '{"first": 1}'
