
import streamlit as st

st.set_page_config(page_title="Scientific Calculator", page_icon="🧮", layout="centered")

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

st.title(" Scientific Calculator")

_, top_r = st.columns([3, 2])
with top_r:
    st.radio("Angle mode", ["Deg", "Rad"], horizontal=True)

st.text_input("Expression", value="", placeholder="0", label_visibility="collapsed")
st.caption("Ans = 0")

KEYS = [
    ["sin", "cos", "tan", "(", ")"],
    ["sin⁻¹", "cos⁻¹", "tan⁻¹", "xʸ", "√"],
    ["log", "ln", "eˣ", "n!", "|x|"],
    ["x²", "1/x", "10ˣ", "%", "Ans"],
    ["7", "8", "9", "÷", "⌫"],
    ["4", "5", "6", "×", "AC"],
    ["1", "2", "3", "−", "+"],
    ["0", ".", "π", "e", "="],
]

for r, row in enumerate(KEYS):
    cols = st.columns(5)
    for c, label in enumerate(row):
        with cols[c]:
            st.button(
                label,
                key=f"btn_{r}_{c}",
                type="primary" if label == "=" else "secondary",
                use_container_width=True,
            )

with st.sidebar:
    st.header("History")
    st.caption("No calculations yet.")
