"""Benchmark 报告生成器。"""

import json
from typing import List


class ConsoleReporter:
    """控制台表格报告。"""

    def __init__(self, results: List[dict]) -> None:
        self.results = results

    def print(self) -> None:
        print("\n" + "=" * 80)
        print("Benchmark 对比报告")
        print("=" * 80)
        print(f"{'模型':<15} {'Skill':<10} {'类型准确率':<10} {'主题准确率':<10} {'综合准确率':<10} {'状态':<6}")
        print("-" * 80)

        for r in self.results:
            status = "PASS" if r["passed"] else "FAIL"
            print(
                f"{r['model']:<15} {r['skill']:<10} "
                f"{r['type_accuracy']:<10.2f} {r['theme_accuracy']:<10.2f} "
                f"{r['overall_accuracy']:<10.2f} {status:<6}"
            )

        print("-" * 80)

        # 按模型分组显示提升
        models = sorted(set(r["model"] for r in self.results))
        skills = sorted(set(r["skill"] for r in self.results))

        if len(skills) >= 2:
            print("\n技能版本对比（按模型）:")
            for model in models:
                model_results = [r for r in self.results if r["model"] == model]
                if len(model_results) >= 2:
                    baseline = model_results[0]["overall_accuracy"]
                    latest = model_results[-1]["overall_accuracy"]
                    delta = latest - baseline
                    print(f"  {model}: {baseline:.2f} -> {latest:.2f} ({delta:+.2f})")

        print("=" * 80)


class JsonReporter:
    """JSON 文件报告。"""

    def __init__(self, results: List[dict]) -> None:
        self.results = results

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": {
                        "total_runs": len(self.results),
                        "passed": sum(1 for r in self.results if r["passed"]),
                        "failed": sum(1 for r in self.results if not r["passed"]),
                    },
                    "results": self.results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n结果已保存: {path}")
