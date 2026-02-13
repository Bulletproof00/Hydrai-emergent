import ast
from collections.abc import Mapping

import numpy as np
import pandas as pd

ALLOWED_FUNCS = {"abs", "min", "max", "clamp"}
ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
ALLOWED_CMPOPS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)


def _clamp(x, lo, hi):
    return np.minimum(np.maximum(x, lo), hi)


def _safe_func(name: str):
    if name == "abs":
        return np.abs
    if name == "min":
        return np.minimum
    if name == "max":
        return np.maximum
    if name == "clamp":
        return _clamp
    raise ValueError(f"Function not allowed: {name}")


def validate_formula(expr: str) -> None:
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute, ast.Subscript, ast.Lambda, ast.DictComp, ast.ListComp, ast.GeneratorExp, ast.Await, ast.Yield, ast.NamedExpr)):
            raise ValueError("Unsupported syntax")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                raise ValueError("Only allowlisted functions are supported")
        if isinstance(node, ast.BinOp) and not isinstance(node.op, ALLOWED_BINOPS):
            raise ValueError("Operator not allowed")
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if not isinstance(op, ALLOWED_CMPOPS):
                    raise ValueError("Comparison operator not allowed")


def _eval(node: ast.AST, data: Mapping[str, pd.Series]):
    if isinstance(node, ast.Expression):
        return _eval(node.body, data)
    if isinstance(node, ast.Name):
        if node.id not in data:
            raise ValueError(f"Unknown feature reference: {node.id}")
        return data[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand, data)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return ~operand.astype(bool)
        raise ValueError("Unary operator not allowed")
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, data)
        right = _eval(node.right, data)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise ValueError("Operator not allowed")
    if isinstance(node, ast.BoolOp):
        values = [_eval(v, data).astype(bool) for v in node.values]
        out = values[0]
        for v in values[1:]:
            out = out & v if isinstance(node.op, ast.And) else out | v
        return out
    if isinstance(node, ast.Compare):
        left = _eval(node.left, data)
        right = _eval(node.comparators[0], data)
        op = node.ops[0]
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        raise ValueError("Comparison not allowed")
    if isinstance(node, ast.Call):
        func = _safe_func(node.func.id)
        args = [_eval(a, data) for a in node.args]
        return func(*args)
    raise ValueError("Unsupported formula expression")


def evaluate_formula(expr: str, data: Mapping[str, pd.Series]) -> pd.Series:
    validate_formula(expr)
    tree = ast.parse(expr, mode="eval")
    out = _eval(tree, data)
    if isinstance(out, pd.Series):
        return out
    if np.isscalar(out):
        idx = next(iter(data.values())).index
        return pd.Series([out] * len(idx), index=idx)
    return pd.Series(out)
