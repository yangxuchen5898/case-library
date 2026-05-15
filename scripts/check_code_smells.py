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


# ---------------------------------------------------------------------------
# Check 3 helpers: file-existence check + fallback
# ---------------------------------------------------------------------------


def _is_exists_call(node: ast.expr) -> bool:
    """Return True if node is a path.exists() or os.path.exists() call."""
    if isinstance(node, ast.Call):
        # path.exists() — Attribute(value=Name, attr='exists')
        if isinstance(node.func, ast.Attribute) and node.func.attr == "exists":
            return True
        # os.path.exists(...)
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and node.func.value.attr == "path"
            and node.func.attr == "exists"
        ):
            return True
    return False


def _is_file_read_call(node: ast.expr) -> bool:
    """Return True if node is a file-reading call (read_text / read_bytes / read_json / open(...).read() etc.)."""
    if not isinstance(node, ast.Call):
        return False
    # path.read_text() / read_bytes() / read_json()
    if isinstance(node.func, ast.Attribute) and node.func.attr in {
        "read_text",
        "read_bytes",
        "read_json",
        "read",
    }:
        return True
    return False


def _is_open_call(node: ast.expr) -> bool:
    """Return True if node is an open(...) call."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"


def _collect_assigned_vars(body: list[ast.stmt]) -> set[str]:
    """Collect simple variable names assigned in a statement list."""
    names: set[str] = set()
    for stmt in body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(stmt, ast.With):
            for item in stmt.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    names.add(item.optional_vars.id)
            # Also recurse into the with body
            names |= _collect_assigned_vars(stmt.body)
        elif isinstance(stmt, ast.If):
            names |= _collect_assigned_vars(stmt.body)
            names |= _collect_assigned_vars(stmt.orelse)
        elif isinstance(stmt, ast.Try):
            names |= _collect_assigned_vars(stmt.body)
            for handler in stmt.handlers:
                names |= _collect_assigned_vars(handler.body)
            names |= _collect_assigned_vars(stmt.orelse)
            names |= _collect_assigned_vars(stmt.finalbody)
        elif isinstance(stmt, (ast.For, ast.While)):
            names |= _collect_assigned_vars(stmt.body)
            names |= _collect_assigned_vars(stmt.orelse)
    return names


def _collect_file_read_vars(body: list[ast.stmt]) -> set[str]:
    """Collect variable names that receive a file-read result in the statement list."""
    names: set[str] = set()
    for stmt in body:
        if isinstance(stmt, ast.Assign):
            # e.g. data = path.read_text()
            if stmt.value and _is_file_read_call(stmt.value):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            # e.g. data = open(path).read()
            if isinstance(stmt.value, ast.Call) and _is_file_read_call(stmt.value):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            # e.g. data = open(path, 'r').read()
            if (
                isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr == "read"
                and stmt.value.args
                and isinstance(stmt.value.func.value, ast.Call)
                and _is_open_call(stmt.value.func.value)
            ):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
        elif isinstance(stmt, ast.With):
            # with open(path) as f: data = f.read()
            for item in stmt.items:
                if item.context_expr and _is_open_call(item.context_expr):
                    for sub in stmt.body:
                        if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Call):
                            if (
                                isinstance(sub.value.func, ast.Attribute)
                                and sub.value.func.attr == "read"
                            ):
                                for target in sub.targets:
                                    if isinstance(target, ast.Name):
                                        names.add(target.id)
            names |= _collect_file_read_vars(stmt.body)
        elif isinstance(stmt, ast.If):
            names |= _collect_file_read_vars(stmt.body)
            names |= _collect_file_read_vars(stmt.orelse)
        elif isinstance(stmt, ast.Try):
            names |= _collect_file_read_vars(stmt.body)
            for handler in stmt.handlers:
                names |= _collect_file_read_vars(handler.body)
            names |= _collect_file_read_vars(stmt.orelse)
            names |= _collect_file_read_vars(stmt.finalbody)
        elif isinstance(stmt, (ast.For, ast.While)):
            names |= _collect_file_read_vars(stmt.body)
            names |= _collect_file_read_vars(stmt.orelse)
    return names


def _collect_fallback_vars(body: list[ast.stmt]) -> set[str]:
    """Collect variable names assigned a default fallback value in the statement list."""
    names: set[str] = set()
    for stmt in body:
        if isinstance(stmt, ast.Assign):
            # Check if RHS is a simple literal default: "", [], {}, None, or other constant
            is_default = False
            if isinstance(stmt.value, ast.Constant) and stmt.value.value in ("", [], {}, None):
                is_default = True
            elif isinstance(stmt.value, ast.List) and len(stmt.value.elts) == 0:
                is_default = True
            elif isinstance(stmt.value, ast.Dict) and len(stmt.value.keys) == 0:
                is_default = True
            elif isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                is_default = True
            if is_default:
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
        elif isinstance(stmt, ast.If):
            names |= _collect_fallback_vars(stmt.body)
            names |= _collect_fallback_vars(stmt.orelse)
        elif isinstance(stmt, ast.Try):
            names |= _collect_fallback_vars(stmt.body)
            for handler in stmt.handlers:
                names |= _collect_fallback_vars(handler.body)
            names |= _collect_fallback_vars(stmt.orelse)
            names |= _collect_fallback_vars(stmt.finalbody)
        elif isinstance(stmt, (ast.For, ast.While)):
            names |= _collect_fallback_vars(stmt.body)
            names |= _collect_fallback_vars(stmt.orelse)
        elif isinstance(stmt, ast.With):
            names |= _collect_fallback_vars(stmt.body)
    return names


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

        # --- Check 3: file existence check + fallback (silent degradation) ---
        if isinstance(node, ast.If) and _is_exists_call(node.test) and node.orelse:
            read_vars = _collect_file_read_vars(node.body)
            fallback_vars = _collect_fallback_vars(node.orelse)
            degraded = read_vars & fallback_vars
            for var_name in degraded:
                violations.append(
                    f"{path}:{node.lineno}: silent degradation -- variable "
                    f"'{var_name}' falls back to default when file missing "
                    f"(use FileNotFoundError instead)"
                )

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
