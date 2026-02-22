import os
import random
import streamlit as st
from groq import Groq
from io import BytesIO
import requests
import speech_recognition as sr

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="AI Detective Game 🕵️", page_icon="🕵️")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found. Add it in Hugging Face Space Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ----------------------------
# Cases Database with multiple suspects & images
# ----------------------------
CASES = [
    {
        "victim": "Mr. Jonathan Reed",
        "crime": "Diamond theft",
        "location": "City Museum",
        "time": "midnight",
        "suspects": [
            {"name": "Night Guard", "secret": "Disabled cameras and stole the diamond."},
            {"name": "Curator", "secret": "Had access to keys but innocent."},
            {"name": "Janitor", "secret": "Was cleaning late, innocent."}
        ],
        "image": "https://images.unsplash.com/photo-1572373446215-933b3aef5e0b?auto=format&fit=crop&w=800&q=80"
    },
    {
        "victim": "Ms. Clara Stone",
        "crime": "Poisoning",
        "location": "Grand Hotel",
        "time": "during dinner",
        "suspects": [
            {"name": "Business Partner", "secret": "Poisoned the drink to gain control."},
            {"name": "Chef", "secret": "Cooked dinner, innocent."},
            {"name": "Guest", "secret": "Attended dinner, innocent."}
        ],
        "image": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?auto=format&fit=crop&w=800&q=80"
    }
]

# ----------------------------
# Initialize Game State
# ----------------------------
def start_new_case():
    case = random.choice(CASES)
    st.session_state.case = case
    st.session_state.questions_left = 10
    st.session_state.solved = False
    st.session_state.score = st.session_state.get("score", {"solved":0, "wrong":0})
    
    st.session_state.difficulty = st.session_state.get("difficulty", "Easy")
    
    st.session_state.selected_suspect = random.choice(case["suspects"])
    
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                f"You are the suspect '{st.session_state.selected_suspect['name']}' in a detective mystery game. "
                f"The crime is: {case['crime']} at {case['location']} {case['time']}. "
                f"The victim is {case['victim']}. "
                f"Difficulty: {st.session_state.difficulty}. "
                "Do NOT reveal the truth directly. Give subtle clues or mislead depending on difficulty. "
                "If the player guesses correctly, confirm they solved the case."
            )
        },
        {"role": "assistant", "content": f"I am {st.session_state.selected_suspect['name']}. Ask carefully…"}
    ]

if "messages" not in st.session_state:
    start_new_case()

case = st.session_state.case

# ----------------------------
# Difficulty Selection
# ----------------------------
st.sidebar.title("🎛️ Settings")
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Hard"], index=["Easy","Hard"].index(st.session_state.difficulty))
st.session_state.difficulty = difficulty

# ----------------------------
# Suspect Selection
# ----------------------------
suspect_names = [s["name"] for s in case["suspects"]]
selected_suspect = st.sidebar.selectbox("Select Suspect to Interrogate", suspect_names)
for s in case["suspects"]:
    if s["name"] == selected_suspect:
        st.session_state.selected_suspect = s
        break

# ----------------------------
# Display Crime Scene
# ----------------------------
st.image(case["image"], caption="Crime Scene", use_column_width=True)

# ----------------------------
# Case File
# ----------------------------
with st.expander("🗂️ Case File"):
    st.markdown(f"""
    **Victim:** {case['victim']}  
    **Crime:** {case['crime']}  
    **Location:** {case['location']}  
    **Time:** {case['time']}  
    **Questions Left:** {st.session_state.questions_left}  
    **Difficulty:** {st.session_state.difficulty}
    """)

# ----------------------------
# Chat History
# ----------------------------
for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

# ----------------------------
# Voice Input (optional)
# ----------------------------
st.markdown("### 🎤 Ask via Voice (optional)")
audio_file = st.file_uploader("Upload your question (mp3/wav)", type=["wav","mp3"])
user_input = None
if audio_file:
    recognizer = sr.Recognizer()
    with sr.AudioFile(BytesIO(audio_file.read())) as source:
        audio_data = recognizer.record(source)
        try:
            user_input = recognizer.recognize_google(audio_data)
            st.info(f"🎙️ You asked: {user_input}")
        except:
            st.error("Could not understand audio.")

# ----------------------------
# Text Input
# ----------------------------
if user_input is None:
    user_input = st.chat_input("Type your question for the suspect...")

# ----------------------------
# Process Input
# ----------------------------
if user_input and not st.session_state.solved and st.session_state.questions_left > 0:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    st.session_state.questions_left -= 1

    # Modify AI behavior based on difficulty
    temp = 0.5 if difficulty=="Easy" else 0.8

    with st.spinner("Suspect is thinking..."):
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=st.session_state.messages,
            temperature=temp,
            max_tokens=250,
        )
        reply = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

# ----------------------------
# Make a Guess
# ----------------------------
st.markdown("### 🧠 Make Your Final Guess")
guess = st.text_input("Who is the culprit? What happened?")

if st.button("Submit Guess"):
    culprit = st.session_state.selected_suspect["name"]
    if culprit.lower() in guess.lower():
        st.success("🎉 Case Solved! You caught the culprit.")
        st.session_state.solved = True
        st.session_state.score["solved"] += 1
    else:
        st.error("❌ Wrong accusation!")
        st.session_state.score["wrong"] += 1

# ----------------------------
# Scoreboard
# ----------------------------
st.sidebar.markdown("### 📊 Scoreboard")
st.sidebar.markdown(f"Solved Cases: {st.session_state.score['solved']}  \nWrong Guesses: {st.session_state.score['wrong']}")

# ----------------------------
# Game Controls
# ----------------------------
if st.button("🔄 New Case"):
    start_new_case()
    st.experimental_rerun()
