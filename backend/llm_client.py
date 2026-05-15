"""LLM 客户端模块 —— 为分类测试、审核、事实核查提供统一的 LLM 调用接口。

环境变量要求（需在 .env 文件中配置）：
  - OPENAI_BASE_URL: OpenAI 兼容 API 的端点地址
  - OPENAI_API_KEY: API 密钥
  - OPENAI_MODEL: 默认模型名称，如 deepseek-chat、qwen-max
  - OPENAI_MODELS: （可选）逗号分隔的可用模型列表，如 "qwen-plus,deepseek-v3"

使用示例：
    from llm_client import get_llm_client
    client = get_llm_client()                    # 使用默认模型
    client = get_llm_client(model="qwen-plus")   # 切换模型
    text = client.chat_completion("系统提示", "用户提示")
    data = client.chat_completion_json("系统提示", "用户提示")
"""

import json
import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import APIError, APITimeoutError, OpenAI

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

# 如果 OPENAI_MODEL 未设置，尝试从 OPENAI_MODELS 取第一个
if not OPENAI_MODEL:
    _models_env = os.getenv("OPENAI_MODELS", "")
    if _models_env:
        OPENAI_MODEL = _models_env.split(",")[0].strip()

_client: Optional["LLMClient"] = None


class LLMClient:
    """封装 OpenAI 兼容 API 的同步客户端，支持普通对话和 JSON 结构化输出。"""

    def __init__(self, model: Optional[str] = None) -> None:
        missing = []
        if not OPENAI_BASE_URL:
            missing.append("OPENAI_BASE_URL")
        if not OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if missing:
            raise RuntimeError(
                f"缺少 LLM 环境变量: {', '.join(missing)}。"
                f"请在 .env 文件中配置后重试。"
            )

        self._client = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
        )
        self.model = model or OPENAI_MODEL or "deepseek-chat"

    @property
    def available_models(self) -> list[str]:
        """返回环境变量中配置的可用模型列表。"""
        models_env = os.getenv("OPENAI_MODELS", "")
        if models_env:
            return [m.strip() for m in models_env.split(",") if m.strip()]
        return [self.model] if self.model else []

    def _retry_call(self, **kwargs):
        """带指数退避的重试逻辑，最多重试 3 次。"""
        last_exception = None
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(**kwargs)
                return response
            except (APIError, APITimeoutError) as exc:
                last_exception = exc
                sleep_time = 2 ** attempt
                time.sleep(sleep_time)
        raise last_exception

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """调用 LLM 返回纯文本回复。

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 采样温度，默认 0.7
            max_tokens: 最大生成 token 数，默认 2000

        Returns:
            助手的文本回复内容
        """
        response = self._retry_call(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""

    def _supports_json_mode(self) -> bool:
        supported = {"gpt-4", "gpt-4o", "gpt-3.5-turbo", "deepseek-chat", "qwen-max", "qwen-plus"}
        env_models = os.getenv("JSON_MODE_MODELS", "")
        if env_models:
            supported = {m.strip() for m in env_models.split(",") if m.strip()}
        return self.model in supported

    def chat_completion_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> dict:
        """调用 LLM 返回 JSON 结构化回复。

        Args:
            system_prompt: 系统提示词（应包含 "return JSON" 相关指令）
            user_prompt: 用户提示词
            temperature: 采样温度，默认 0.3（更低以提高 JSON 稳定性）
            max_tokens: 最大生成 token 数，默认 2000

        Returns:
            解析后的 Python 字典

        Raises:
            ValueError: JSON 解析失败时抛出
        """
        if self._supports_json_mode():
            response = self._retry_call(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
        else:
            content = self._extract_json_from_text(
                system_prompt, user_prompt, temperature, max_tokens
            )

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 内容可能包含多个 JSON 块或额外文字，尝试提取第一个有效 JSON
            decoder = json.JSONDecoder()
            idx = content.find("{")
            while idx != -1:
                try:
                    obj, end = decoder.raw_decode(content, idx)
                    return obj
                except json.JSONDecodeError:
                    idx = content.find("{", idx + 1)
            raise ValueError("LLM 返回的 JSON 解析失败，无法提取有效 JSON") from None

    def _extract_json_from_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """不支持 JSON mode 的模型降级：用普通文本调用，从回复中提取 JSON。"""
        text = self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt + "\n\n请严格返回合法 JSON，不要添加任何解释文字。",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        decoder = json.JSONDecoder()
        idx = text.find('{')
        while idx != -1:
            try:
                obj, end = decoder.raw_decode(text, idx)
                return text[idx:end]
            except json.JSONDecodeError:
                idx = text.find('{', idx + 1)
        return "{}"


def get_llm_client(model: Optional[str] = None) -> LLMClient:
    """获取 LLMClient 实例。

    Args:
        model: 指定模型名称，覆盖环境变量默认值。
               若未指定且单例已存在，返回现有单例；
               若指定了不同模型，创建新实例（非单例模式）。
    """
    global _client
    if model is None:
        if _client is None:
            _client = LLMClient()
        return _client
    return LLMClient(model=model)


if __name__ == "__main__":
    missing = []
    if not OPENAI_BASE_URL:
        missing.append("OPENAI_BASE_URL")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not OPENAI_MODEL:
        missing.append("OPENAI_MODEL")

    if missing:
        print(f"缺少环境变量: {', '.join(missing)}")
    else:
        try:
            client = get_llm_client()
            print("LLM client initialized successfully")
        except Exception as exc:
            print(f"LLM client initialization failed: {exc}")
