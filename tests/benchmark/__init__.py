"""Skills Benchmark 框架 —— 用于对比测试不同模型和提示词版本的分类效果。

使用示例：
    from tests.benchmark import BenchmarkRunner
    from backend.llm_client import get_llm_client
    from backend.classify_llm import classify_with_llm

    runner = BenchmarkRunner("tests/data/classification_ground_truth.json")
    runner.register_model("qwen-plus", get_llm_client("qwen-plus"))
    runner.register_skill("current", classify_with_llm)
    results = runner.run()
    runner.report()
    runner.save("benchmark_results.json")
"""

from .core import BenchmarkRunner
from .metrics import jaccard_similarity

__all__ = ["BenchmarkRunner", "jaccard_similarity"]
