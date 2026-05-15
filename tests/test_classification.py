"""分类准确率测试框架。

运行方式：
  - 完整测试（含 LLM 调用）：pytest tests/test_classification.py -v -s
  - 跳过慢测试（仅本地规则验证）：pytest tests/test_classification.py -m "not slow" -v
"""

import pytest

from backend.classify_llm import build_system_prompt, classify_with_llm
from tests.benchmark.metrics import jaccard_similarity


@pytest.mark.slow
def test_classification_accuracy(ground_truth_data, llm_client):
    """对全部 ground truth 案例运行 LLM 分类并计算批次准确率。"""
    type_accuracies = []
    theme_accuracies = []
    results = []

    for case in ground_truth_data:
        predicted = classify_with_llm(case["content"], case.get("title", ""))

        type_acc = jaccard_similarity(
            predicted.get("types", []), case["expected_types"]
        )
        theme_acc = jaccard_similarity(
            predicted.get("themes", []), case["expected_themes"]
        )

        type_accuracies.append(type_acc)
        theme_accuracies.append(theme_acc)
        results.append(
            {
                "id": case["id"],
                "title": case.get("title", "")[:30],
                "type_acc": type_acc,
                "theme_acc": theme_acc,
                "pred_types": predicted.get("types", []),
                "exp_types": case["expected_types"],
                "pred_themes": predicted.get("themes", []),
                "exp_themes": case["expected_themes"],
            }
        )

    avg_type_accuracy = sum(type_accuracies) / len(type_accuracies) if type_accuracies else 0.0
    avg_theme_accuracy = sum(theme_accuracies) / len(theme_accuracies) if theme_accuracies else 0.0
    avg_overall_accuracy = (avg_type_accuracy + avg_theme_accuracy) / 2

    # 打印汇总表
    print("\n" + "=" * 80)
    print("分类准确率测试结果")
    print("=" * 80)
    print(f"{'ID':<10} {'标题':<30} {'类型准确率':<12} {'主题准确率':<12}")
    print("-" * 80)
    for r in results:
        print(
            f"{r['id']:<10} {r['title']:<30} "
            f"{r['type_acc']:<12.2f} {r['theme_acc']:<12.2f}"
        )
    print("-" * 80)
    print(f"批次平均类型准确率: {avg_type_accuracy:.2f}")
    print(f"批次平均主题准确率: {avg_theme_accuracy:.2f}")
    print(f"批次综合准确率:     {avg_overall_accuracy:.2f}")
    print("=" * 80)

    assert avg_overall_accuracy >= 0.80, (
        f"综合准确率 {avg_overall_accuracy:.2f} 低于阈值 0.80。\n"
        f"详细结果: {results}"
    )


@pytest.mark.slow
def test_classification_output_format(ground_truth_data, llm_client):
    """验证 LLM 分类返回的数据格式和字段有效性。"""
    case = ground_truth_data[0]
    result = classify_with_llm(case["content"], case.get("title", ""))

    required_keys = {"types", "themes", "reason", "primary_type"}
    assert required_keys.issubset(result.keys()), (
        f"返回结果缺少必要字段。期望包含 {required_keys}，实际有 {set(result.keys())}"
    )

    valid_types = {"TYPE_A", "TYPE_B", "TYPE_C"}
    for t in result["types"]:
        assert t in valid_types, f"无效的类型值: {t}"

    valid_themes = {"强国建设", "上海实践", "创新发展", "校园文明"}
    for theme in result["themes"]:
        assert theme in valid_themes, f"无效的主题值: {theme}"


def test_classification_rules_loaded():
    """验证分类规则文件能被正确加载且包含必要内容。"""
    prompt = build_system_prompt()
    assert len(prompt) > 0, "系统提示词为空"
    assert "TYPE_A" in prompt, "系统提示词缺少 TYPE_A"
    assert "TYPE_B" in prompt, "系统提示词缺少 TYPE_B"
    assert "TYPE_C" in prompt, "系统提示词缺少 TYPE_C"
    assert "分类规则" in prompt, "系统提示词缺少分类规则说明"
