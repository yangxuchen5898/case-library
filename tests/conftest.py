"""pytest 共享 fixtures。"""

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "unit: fast unit tests with no network calls")
    config.addinivalue_line("markers", "integration: integration tests with mocked dependencies")
    config.addinivalue_line("markers", "model(name): specify LLM model for test")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def ground_truth_data():
    """加载人工标注的分类测试数据集。"""
    data_path = _project_root() / "tests" / "data" / "classification_ground_truth.json"
    if not data_path.exists():
        pytest.skip(f"测试数据集不存在: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def llm_client(request):
    """返回 LLMClient 实例；如果环境变量未配置则跳过测试。

    支持通过 pytest.mark.model 标记指定模型：
        @pytest.mark.model("qwen-plus")
        def test_something(llm_client):
            ...
    """
    required = ["OPENAI_BASE_URL", "OPENAI_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        pytest.skip(f"缺少 LLM 环境变量: {', '.join(missing)}")

    from backend.llm_client import get_llm_client

    model_marker = request.node.get_closest_marker("model")
    model_name = model_marker.args[0] if model_marker else None
    return get_llm_client(model=model_name)
