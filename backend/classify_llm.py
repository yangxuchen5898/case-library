"""分类 LLM 调用模块 —— 读取 skill 提示词并调用 LLM 进行分类。"""

from pathlib import Path

from backend.llm_client import get_llm_client

from backend.response_parser import parse_classification

_CLASSIFIER_PATH = Path(__file__).resolve().parent.parent / "skills" / "zhutifenlei" / "classifier.md"


def build_system_prompt() -> str:
    if not _CLASSIFIER_PATH.exists():
        raise FileNotFoundError(f"分类规则文件不存在: {_CLASSIFIER_PATH}")
    return _CLASSIFIER_PATH.read_text(encoding="utf-8")


def _load_prompt(skill_name: str, **kwargs) -> str:
    path = Path(__file__).resolve().parent.parent / "skills" / skill_name / "prompt.md"
    if not path.exists():
        raise FileNotFoundError(f"提示词模板文件不存在: {path}")
    template = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def classify_with_llm(content: str, title: str = "", llm_client=None) -> dict:
    """使用 LLM 对素材进行分类。"""
    system_prompt = build_system_prompt()

    user_prompt = _load_prompt("zhutifenlei", title=title, content=content)

    client = llm_client or get_llm_client()
    response = client.chat_completion_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1500,
    )

    if not isinstance(response, dict):
        raise ValueError(f"LLM 返回的不是 JSON 对象: {response!r}")

    return parse_classification(response, fallback_title=title)
