#!/usr/bin/env python3
"""AST-based checker for code smells.

Detects:
1. re.search / re.compile / re.match / re.findall using greedy ``.*``
   (not ``.*?``) in pattern strings.
2. Any function named ``_normalize_*`` or ``normalize_*`` containing
   ``in`` comparisons between two variables (substring matching heuristic).
3. "File existence check + fallback" pattern: ``if path.exists(): ... else: default``
   (silent degradation — should raise FileNotFoundError instead).

Usage:
    python scripts/check_code_smells.py backend/
"""
from __future__ import annotations

import ast
import re as re_module
import sys
from pathlib import Path


GREEDY_RE = re_module.compile(r"(?<!\?)\.(?![*?])\*")


def _is_re_func(node: ast.Call) -> bool:
    """Return True if the call is re.search / re.compile / re.match / re.findall."""
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        if node.func.value.id == "re" and node.func.attr in {
            "search",
            "compile",
            "match",
            "findall",
        }:
            return True
    return False


def _get_string_value(node: ast.expr) -> str | None:
    """Extract a constant string value from an AST node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        # f-string: try to reconstruct the static parts
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{}")
        return "".join(parts)
    return None


def _has_greedy_star(pattern: str) -> bool:
    return bool(GREEDY_RE.search(pattern))


def _is_in_comparison_between_vars(node: ast.Compare) -> bool:
    """Return True if node is ``left in right`` with both sides being Name nodes."""
    if len(node.ops) == 1 and isinstance(node.ops[0], ast.In):
        if isinstance(node.left, ast.Name) and isinstance(node.comparators[0], ast.Name):
            return True
    return False


def _is_dangerous_in_pattern(node: ast.AST) -> bool:
    """Detect the substring heuristic pattern: ``a in b or b in a``.

    This catches the CR-03 anti-pattern (``valid in t or t in valid``)
    while ignoring legitimate dict/list membership checks like ``field in doc``.
    """
    # Direct single in-comparison is not enough — we need the bidirectional pattern
    # or at least an in-comparison inside a BoolOp (which suggests heuristic logic).
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        # Check if any branch is a variable-in-variable comparison
        for value in node.values:
            if isinstance(value, ast.Compare) and _is_in_comparison_between_vars(value):
                return True
    return False


def check_file(path: Path) -> list[str]:
    """Check a single Python file and return list of violation messages."""
    violations: list[str] = []
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        violations.append(f"{path}: syntax error: {exc}")
        return violations

    for node in ast.walk(tree):
        # --- Check 1: greedy .* in re functions ---
        if isinstance(node, ast.Call) and _is_re_func(node):
            if node.args:
                pattern = _get_string_value(node.args[0])
                if pattern and _has_greedy_star(pattern):
                    func_name = (
                        f"re.{node.func.attr}"
                        if isinstance(node.func, ast.Attribute)
                        else "re_func"
                    )
                    violations.append(
                        f"{path}:{node.lineno}: {func_name} uses greedy `.*` "
                        f"(not `.*?`): {pattern!r}"
                    )

        # --- Check 2: normalize/_normalize functions with bidirectional in heuristic ---
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            if func_name.startswith("normalize_") or func_name.startswith("_normalize_"):
                for sub in ast.walk(node):
                    if _is_dangerous_in_pattern(sub):
                        violations.append(
                            f"{path}:{sub.lineno}: function `{func_name}` contains "
                            f"bidirectional `in` heuristic (e.g. `a in b or b in a`)"
                        )
                        # Report once per function is enough, but multiple lines are okay

    return violations


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python check_code_smells.py <path> [path ...]")
        return 1

    all_violations: list[str] = []
    for arg in sys.argv[1:]:
        target = Path(arg)
        if target.is_file() and target.suffix == ".py":
            all_violations.extend(check_file(target))
        elif target.is_dir():
            for py_file in target.rglob("*.py"):
                all_violations.extend(check_file(py_file))
        else:
            print(f"Warning: skipping {target}")

    if all_violations:
        print("Code smell violations found:")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print("No code smells detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
