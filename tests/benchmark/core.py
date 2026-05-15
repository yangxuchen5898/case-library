"""Benchmark 核心运行器。"""

import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .metrics import jaccard_similarity
from .reporters import ConsoleReporter, JsonReporter


class BenchmarkRunner:
    """Skills benchmark 运行器。

    支持注册多个模型和多个 skill 版本，运行交叉测试并生成对比报告。
    """

    def __init__(self, dataset_path: str, threshold: float = 0.80) -> None:
        """初始化 benchmark 运行器。

        Args:
            dataset_path: ground truth 数据集 JSON 文件路径
            threshold: 综合准确率通过阈值（默认 0.80）
        """
        self.dataset_path = Path(dataset_path)
        self.threshold = threshold
        self._models: Dict[str, object] = {}
        self._skills: Dict[str, Callable] = {}
        self._results: List[dict] = []

    def register_model(self, name: str, client) -> "BenchmarkRunner":
        """注册一个模型客户端。

        Args:
            name: 模型名称，如 "qwen-plus"
            client: LLMClient 实例
        """
        self._models[name] = client
        return self

    def register_skill(self, name: str, classify_fn: Callable) -> "BenchmarkRunner":
        """注册一个分类 skill 函数。

        Args:
            name: skill 版本名称，如 "v1"、"v2"
            classify_fn: 分类函数，签名为 (content, title, llm_client) -> dict
        """
        self._skills[name] = classify_fn
        return self

    def load_dataset(self) -> List[dict]:
        """加载 ground truth 数据集。"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"数据集不存在: {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run(self, models: Optional[List[str]] = None, skills: Optional[List[str]] = None) -> List[dict]:
        """运行 benchmark。

        Args:
            models: 指定要测试的模型列表（None = 全部）
            skills: 指定要测试的 skill 列表（None = 全部）

        Returns:
            结果列表，每个元素包含 model/skill/case 级别的详细数据
        """
        cases = self.load_dataset()
        models_to_test = {k: v for k, v in self._models.items() if models is None or k in models}
        skills_to_test = {k: v for k, v in self._skills.items() if skills is None or k in skills}

        self._results = []

        for model_name, client in models_to_test.items():
            for skill_name, classify_fn in skills_to_test.items():
                print(f"\n[Benchmark] 模型: {model_name} | Skill: {skill_name}")
                type_accs = []
                theme_accs = []
                case_results = []

                for case in cases:
                    start = time.time()
                    try:
                        predicted = classify_fn(
                            case["content"], case.get("title", ""), llm_client=client
                        )
                        error = None
                    except Exception as exc:
                        predicted = {"types": [], "themes": []}
                        error = str(exc)

                    elapsed = time.time() - start
                    type_acc = jaccard_similarity(
                        predicted.get("types", []), case["expected_types"]
                    )
                    theme_acc = jaccard_similarity(
                        predicted.get("themes", []), case["expected_themes"]
                    )

                    type_accs.append(type_acc)
                    theme_accs.append(theme_acc)
                    case_results.append({
                        "case_id": case["id"],
                        "type_accuracy": type_acc,
                        "theme_accuracy": theme_acc,
                        "predicted_types": predicted.get("types", []),
                        "expected_types": case["expected_types"],
                        "predicted_themes": predicted.get("themes", []),
                        "expected_themes": case["expected_themes"],
                        "error": error,
                        "elapsed_ms": round(elapsed * 1000, 1),
                    })

                avg_type = sum(type_accs) / len(type_accs) if type_accs else 0.0
                avg_theme = sum(theme_accs) / len(theme_accs) if theme_accs else 0.0
                overall = (avg_type + avg_theme) / 2
                passed = overall >= self.threshold

                result = {
                    "model": model_name,
                    "skill": skill_name,
                    "type_accuracy": round(avg_type, 2),
                    "theme_accuracy": round(avg_theme, 2),
                    "overall_accuracy": round(overall, 2),
                    "passed": passed,
                    "threshold": self.threshold,
                    "cases": case_results,
                }
                self._results.append(result)
                status = "PASS" if passed else "FAIL"
                print(f"  结果: 类型={avg_type:.2f} 主题={avg_theme:.2f} 综合={overall:.2f} [{status}]")

        return self._results

    def report(self) -> None:
        """输出控制台对比报告。"""
        ConsoleReporter(self._results).print()

    def save(self, path: str) -> None:
        """保存结果为 JSON 文件。"""
        JsonReporter(self._results).save(path)
