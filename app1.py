"""Scientific Calculator built with Streamlit."""

import ast
import math
import operator

import streamlit as st

st.set_page_config(page_title="Scientific Calculator", page_icon="🧮", layout="centered")

# ----------------------------------------------------------------------------
# Safe expression evaluator (no eval(), so arbitrary code can't be executed)
# ----------------------------------------------------------------------------
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _factorial(x):
    if x < 0 or x != int(x) or x > 170:
        raise ValueError("Factorial needs an integer between 0 and 170")
    return math.factorial(int(x))


def get_functions(mode):
    """Return the function table. Trig functions respect Deg/Rad mode."""
    deg = mode == "Deg"
    to_rad = (lambda x: math.radians(x)) if deg else (lambda x: x)
    from_rad = (lambda x: math.degrees(x)) if deg else (lambda x: x)
    return {
        "sin": lambda x: math.sin(to_rad(x)),
        "cos": lambda x: math.cos(to_rad(x)),
        "tan": lambda x: math.tan(to_rad(x)),
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        "log": math.log10,
        "ln": math.log,
        "exp": math.exp,
        "sqrt": math.sqrt,
        "abs": abs,
        "fact": _factorial,
    }


def normalize(expr: str) -> str:
    for old, new in {"×": "*", "÷": "/", "−": "-", "^": "**", "π": "pi", "√": "sqrt"}.items():
        expr = expr.replace(old, new)
    return expr.strip()


def _eval(node, funcs, consts):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left = _eval(node.left, funcs, consts)
        right = _eval(node.right, funcs, consts)
        if isinstance(node.op, ast.Pow) and abs(right) > 10000:
            raise OverflowError("Exponent too large")
        return BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](_eval(node.operand, funcs, consts))
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in funcs
        and len(node.args) == 1
        and not node.keywords
    ):
        return funcs[node.func.id](_eval(node.args[0], funcs, consts))
    raise ValueError("Invalid expression")


def evaluate(expr: str, mode: str, ans: float):
    expr = normalize(expr)
    if not expr:
        raise ValueError("Empty expression")
    consts = {"pi": math.pi, "e": math.e, "ans": ans, "Ans": ans}
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise ValueError("Syntax error")
    result = _eval(tree.body, get_functions(mode), consts)
    if isinstance(result, complex):
        raise ValueError("Result is not a real number")
    if isinstance(result, float) and (math.isnan(result) or math.isinf(result)):
        raise ValueError("Result is undefined or infinite")
    return result


def fmt(x) -> str:
    if isinstance(x, int):
        return str(x)
    if float(x).is_integer() and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.12g}"


def friendly_error(exc: Exception) -> str:
    if isinstance(exc, ZeroDivisionError):
        return "Cannot divide by zero"
    if isinstance(exc, OverflowError):
        return "Number too large"
    if isinstance(exc, ValueError) and "math domain" in str(exc):
        return "Math domain error (input outside the allowed range)"
    return str(exc) or "Error"


# ----------------------------------------------------------------------------
# State & callbacks
# ----------------------------------------------------------------------------
if "expr" not in st.session_state:
    st.session_state.expr = ""
    st.session_state.ans = 0
    st.session_state.history = []
    st.session_state.error = ""


def press(token: str):
    st.session_state.error = ""
    st.session_state.expr += token


def backspace():
    st.session_state.expr = st.session_state.expr[:-1]
    st.session_state.error = ""


def clear_all():
    st.session_state.expr = ""
    st.session_state.error = ""


def calculate():
    expr = st.session_state.expr
    try:
        result = evaluate(expr, st.session_state.angle, st.session_state.ans)
        text = fmt(result)
        st.session_state.history.insert(0, f"{expr} = {text}")
        st.session_state.ans = result
        st.session_state.expr = text
        st.session_state.error = ""
    except Exception as exc:  # noqa: BLE001
        st.session_state.error = friendly_error(exc)


def recall(text: str):
    st.session_state.expr = text
    st.session_state.error = ""


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    div.stButton > button { height: 3rem; font-size: 1.05rem; border-radius: 10px; }
    div[data-testid="stTextInput"] input { font-size: 1.6rem; text-align: right;
        font-family: 'Courier New', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧮 Scientific Calculator")

top_l, top_r = st.columns([3, 2])
with top_r:
    st.radio("Angle mode", ["Deg", "Rad"], key="angle", horizontal=True)

st.text_input(
    "Expression",
    key="expr",
    placeholder="Type or tap buttons, e.g. sin(30) + 2^3",
    label_visibility="collapsed",
)

# Live preview of the current expression
if st.session_state.error:
    st.error(st.session_state.error)
elif st.session_state.expr:
    try:
        preview = evaluate(st.session_state.expr, st.session_state.angle, st.session_state.ans)
        st.success(f"= {fmt(preview)}")
    except Exception:  # noqa: BLE001
        st.caption("Keep typing…")
else:
    st.caption(f"Ans = {fmt(st.session_state.ans)}")

# (label, action, argument)
KEYS = [
    [("sin", "ins", "sin("), ("cos", "ins", "cos("), ("tan", "ins", "tan("), ("(", "ins", "("), (")", "ins", ")")],
    [("sin⁻¹", "ins", "asin("), ("cos⁻¹", "ins", "acos("), ("tan⁻¹", "ins", "atan("), ("xʸ", "ins", "^"), ("√", "ins", "sqrt(")],
    [("log", "ins", "log("), ("ln", "ins", "ln("), ("eˣ", "ins", "exp("), ("n!", "ins", "fact("), ("|x|", "ins", "abs(")],
    [("x²", "ins", "^2"), ("1/x", "ins", "1/("), ("10ˣ", "ins", "10^("), ("%", "ins", "%"), ("Ans", "ins", "Ans")],
    [("7", "ins", "7"), ("8", "ins", "8"), ("9", "ins", "9"), ("÷", "ins", "÷"), ("⌫", "back", "")],
    [("4", "ins", "4"), ("5", "ins", "5"), ("6", "ins", "6"), ("×", "ins", "×"), ("AC", "clear", "")],
    [("1", "ins", "1"), ("2", "ins", "2"), ("3", "ins", "3"), ("−", "ins", "−"), ("+", "ins", "+")],
    [("0", "ins", "0"), (".", "ins", "."), ("π", "ins", "π"), ("e", "ins", "e"), ("=", "eq", "")],
]

for r, row in enumerate(KEYS):
    cols = st.columns(5)
    for c, (label, action, arg) in enumerate(row):
        key = f"btn_{r}_{c}"
        with cols[c]:
            if action == "ins":
                st.button(label, key=key, on_click=press, args=(arg,), use_container_width=True)
            elif action == "back":
                st.button(label, key=key, on_click=backspace, use_container_width=True)
            elif action == "clear":
                st.button(label, key=key, on_click=clear_all, use_container_width=True)
            else:
                st.button(label, key=key, on_click=calculate, type="primary", use_container_width=True)

with st.sidebar:
    st.header("History")
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history[:20]):
            result_text = item.split(" = ")[-1]
            st.button(item, key=f"hist_{i}", on_click=recall, args=(result_text,), use_container_width=True)
        if st.button("Clear history"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No calculations yet.")
    st.divider()
    st.caption("Tip: click a history item to reuse its result. Use `Ans` for the last answer.")
