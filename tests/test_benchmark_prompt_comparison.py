"""使用 benchmark 框架对比旧版和新版提示词效果。

运行方式：
    PYTHONPATH=E:/shared/workplace/case-library pytest tests/test_benchmark_prompt_comparison.py -v -s
"""

import pytest

from backend.llm_client import get_llm_client
from tests.benchmark import BenchmarkRunner


# 旧版分类函数（读取 classifier.md）
def _classify_old(content: str, title: str = "", llm_client=None):
    from backend.classify_llm import build_system_prompt
    from backend.response_parser import parse_classification

    system_prompt = build_system_prompt()
    user_prompt = (
        f"请对以下素材进行分类。\n\n"
        f"素材标题：{title}\n"
        f"素材内容：\n{content}\n\n"
        f"请严格按照系统提示中的分类规则和输出格式返回JSON结果。"
    )

    client = llm_client or get_llm_client()
    response = client.chat_completion_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1500,
    )

    return parse_classification(response, fallback_title=title)


# 新版分类函数（内联精简提示词）
def _classify_new(content: str, title: str = "", llm_client=None):
    from backend.classify_llm import classify_with_llm
    return classify_with_llm(content, title, llm_client=llm_client)


@pytest.mark.slow
@pytest.mark.model("qwen-plus")
def test_prompt_comparison_qwen_plus(llm_client):
    runner = BenchmarkRunner("tests/data/classification_ground_truth.json", threshold=0.80)
    runner.register_model("qwen-plus", llm_client)
    runner.register_skill("old_prompt", _classify_old)
    runner.register_skill("new_prompt", _classify_new)
    results = runner.run()
    runner.report()

    # 断言新版必须比旧版好
    old_result = next(r for r in results if r["skill"] == "old_prompt")
    new_result = next(r for r in results if r["skill"] == "new_prompt")
    assert new_result["overall_accuracy"] > old_result["overall_accuracy"], (
        f"新版准确率 {new_result['overall_accuracy']} 没有超过旧版 {old_result['overall_accuracy']}"
    )


@pytest.mark.slow
@pytest.mark.model("Qwen3-32B")
def test_prompt_comparison_qwen3_32b(llm_client):
    runner = BenchmarkRunner("tests/data/classification_ground_truth.json", threshold=0.80)
    runner.register_model("Qwen3-32B", llm_client)
    runner.register_skill("old_prompt", _classify_old)
    runner.register_skill("new_prompt", _classify_new)
    results = runner.run()
    runner.report()

    old_result = next(r for r in results if r["skill"] == "old_prompt")
    new_result = next(r for r in results if r["skill"] == "new_prompt")
    assert new_result["overall_accuracy"] > old_result["overall_accuracy"]
