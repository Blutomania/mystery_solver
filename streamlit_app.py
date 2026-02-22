import streamlit as st
import os
from groq import Groq

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="🕵️ AI Mystery Solver Game",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# Load Groq API Key
# -------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found. Set it in Hugging Face Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# -------------------------
# LLM Helper Function
# -------------------------
def llm(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # updated model
            messages=[
                {"role": "system", "content": "You are a creative mystery game engine. Never reveal the culprit unless explicitly asked in the solution phase."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ LLM Error: {e}"

# -------------------------
# Session State
# -------------------------
if "mystery" not in st.session_state:
    st.session_state.mystery = ""
    st.session_state.suspects = []
    st.session_state.solution = ""

# -------------------------
# UI Layout
# -------------------------
st.title("🕵️ AI Mystery Solver Game")

left_col, right_col = st.columns([2, 1])

# -------------------------
# Left: Mystery Story
# -------------------------
with left_col:
    st.subheader("📜 Mystery Story")
    if st.button("🎲 Generate New Mystery"):
        with st.spinner("Creating mystery..."):
            story = llm("""
Create a short detective mystery with:
- A crime
- 3 suspects with names and short backgrounds
- Clues and red herrings
- A hidden culprit (do not reveal the culprit)
""")
            st.session_state.mystery = story

            suspects_text = llm("Extract and list suspects from this mystery in bullet points:\n" + story)
            st.session_state.suspects = [s.strip("- ").strip() for s in suspects_text.split("\n") if s.strip()]

            solution = llm("Who is the real culprit in this mystery and why? Explain logically:\n" + story)
            st.session_state.solution = solution

    st.markdown(
        st.session_state.mystery if st.session_state.mystery else "*Click 'Generate New Mystery' to start the game!*"
    )

# -------------------------
# Right: Suspects & Interrogation
# -------------------------
with right_col:
    st.subheader("🧑‍🤝‍🧑 Suspects")
    if st.session_state.suspects:
        selected_suspect = st.selectbox("Select a suspect to interrogate:", st.session_state.suspects)
        question = st.text_input("Ask your question:")

        if st.button("🔍 Interrogate"):
            if selected_suspect and question:
                with st.spinner("Interrogating..."):
                    reply = llm(f"""
You are suspect {selected_suspect} in this mystery:
{st.session_state.mystery}

Answer the detective's question in character.
Do not reveal the real culprit.
Question: {question}
""")
                    st.success(reply)
            else:
                st.warning("Select a suspect and write your question.")
    else:
        st.info("Suspects will appear here after generating a mystery.")

# -------------------------
# Final Guess
# -------------------------
st.divider()
st.subheader("🧠 Make Your Final Guess")
guess = st.selectbox("Who is the culprit?", ["Select a suspect"] + st.session_state.suspects)

if st.button("✅ Submit Final Answer"):
    if guess == "Select a suspect" or not st.session_state.mystery:
        st.warning("Generate a mystery and select a suspect first!")
    else:
        with st.spinner("Evaluating..."):
            verdict = llm(f"""
Mystery:
{st.session_state.mystery}

Player guessed: {guess}

Actual solution:
{st.session_state.solution}

Tell the player if their guess is correct.
If wrong, reveal the real culprit with explanation.
""")
            st.subheader("🧾 Case Result")
            st.write(verdict)

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.caption("Powered by Groq LLM • Deployed on Hugging Face Spaces")
