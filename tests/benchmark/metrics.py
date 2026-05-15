"""评估指标计算模块。"""


def jaccard_similarity(predicted: list, expected: list) -> float:
    """计算两组标签的 Jaccard 相似度（交集 / 并集）。"""
    pred_set = set(predicted)
    exp_set = set(expected)
    if not pred_set and not exp_set:
        return 1.0
    intersection = pred_set & exp_set
    union = pred_set | exp_set
    return len(intersection) / len(union)


def exact_match(predicted: list, expected: list) -> float:
    """精确匹配率（两组标签完全一致才得 1.0）。"""
    return 1.0 if set(predicted) == set(expected) else 0.0


def precision(predicted: list, expected: list) -> float:
    """精确率 = 正确预测数 / 总预测数。"""
    pred_set = set(predicted)
    exp_set = set(expected)
    if not pred_set:
        return 1.0 if not exp_set else 0.0
    return len(pred_set & exp_set) / len(pred_set)


def recall(predicted: list, expected: list) -> float:
    """召回率 = 正确预测数 / 总期望数。"""
    pred_set = set(predicted)
    exp_set = set(expected)
    if not exp_set:
        return 1.0 if not pred_set else 0.0
    return len(pred_set & exp_set) / len(exp_set)
