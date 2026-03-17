"""
calculator_skill.py — 本地计算器，支持四则运算和常用数学函数
零依赖，纯 Python 实现。
"""
import re, math

SKILL_NAME = "计算器"
SKILL_DESC = "支持四则运算和常用数学函数，直接在飞书里算数"
TRIGGERS   = ["/calc", "/计算", "/算"]
KEYWORDS   = ["计算", "等于多少", "算一下", "多少钱", "怎么算"]

_SAFE_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_NAMES.update({"abs": abs, "round": round, "int": int, "float": float, "pow": pow})

_PREFIX = re.compile(r'^(/calc|/计算|/算)\s*', re.IGNORECASE)
_CLEAN  = re.compile(r'[^0-9+\-*/().% ,a-zA-Z_]')


def handle(user_text: str) -> str:
    expr = _PREFIX.sub("", user_text.strip())
    # 中文符号替换
    expr = expr.replace("×", "*").replace("÷", "/").replace("，", ",").replace("x", "*")
    expr = expr.strip("=？?等于是 ")
    if not expr:
        return "用法：/算 1+2*3 或 /算 sqrt(144)"
    try:
        result = eval(expr, {"__builtins__": {}}, _SAFE_NAMES)  # noqa: S307
        if isinstance(result, float) and result == int(result):
            result = int(result)
        return f"🧮 {expr} = {result}"
    except ZeroDivisionError:
        return "❌ 除数不能为零"
    except Exception:
        return f"❌ 无法计算「{expr}」，支持：+ - * / ** sqrt() sin() cos() 等"
