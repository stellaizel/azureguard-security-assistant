import streamlit as st
import google.generativeai as genai

# ─────────────────────────────────────────────
#  CONFIG — API key is read from Streamlit Secrets
#  In Streamlit Community Cloud:
#    Go to App Settings → Secrets → add:
#    GEMINI_API_KEY = "your-key-here"
# ─────────────────────────────────────────────
API_KEY = st.secrets["GEMINI_API_KEY"]

# ─────────────────────────────────────────────
#  SYSTEM PROMPT — defines the agent's behaviour
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """
You are Cloud Security Assistant, an expert AI tutor specialising in 
Microsoft Azure certifications — specifically AZ-900 (Azure Fundamentals) 
and AZ-500 (Azure Security Technologies).

Your responsibilities:
1. Answer AZ-900 and AZ-500 exam questions clearly and accurately.
2. Explain Azure security concepts in plain, beginner-friendly English.
3. When asked, quiz the user on a topic by generating multiple-choice 
   questions, then reveal the correct answer and explain why.
4. Always tell the user whether a topic belongs to AZ-900, AZ-500, or both.
5. Keep responses concise but thorough — use bullet points and short 
   paragraphs to aid readability.
6. If a question is outside Azure / cloud security scope, politely say so 
   and redirect to the relevant Azure topic.

Tone: friendly, encouraging, and professional — like a study buddy who 
really knows their stuff.

When labelling exam scope, use these tags at the start of your response:
  📘 AZ-900  |  🔐 AZ-500  |  📘🔐 Both
"""

# ─────────────────────────────────────────────
#  PAGE SETUP
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cloud Security Assistant",
    page_icon="☁️",
    layout="centered"
)

st.title("☁️ Cloud Security Assistant")
st.caption("Your AI study buddy for AZ-900 & AZ-500 — ask anything, get quizzed, or explore a concept.")

st.divider()

# ─────────────────────────────────────────────
#  GEMINI CLIENT SETUP
# ─────────────────────────────────────────────
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",   # free tier model
    system_instruction=SYSTEM_PROMPT
)

# ─────────────────────────────────────────────
#  CHAT HISTORY — stored in session state
#  Gemini uses "model" instead of "assistant"
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # stores {role, content} for display

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []  # stores Gemini-format history

# Show existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────
#  CHAT INPUT
# ─────────────────────────────────────────────
user_input = st.chat_input("Ask a question, request a quiz, or type a topic...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Add to display history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ─────────────────────────────────────────
    #  CALL GEMINI API
    # ─────────────────────────────────────────
    try:
        # Start a chat session with existing history
        chat = model.start_chat(history=st.session_state.gemini_history)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            # Stream the response
            for chunk in chat.send_message(user_input, stream=True):
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")

            # Final render without cursor
            response_placeholder.markdown(full_response)

        # Save to display history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Save to Gemini-format history for context carry-over
        st.session_state.gemini_history.append({"role": "user", "parts": [user_input]})
        st.session_state.gemini_history.append({"role": "model", "parts": [full_response]})

    except Exception as e:
        err = str(e)
        if "API_KEY" in err or "invalid" in err.lower():
            st.error("❌ Invalid API key. Check the API_KEY value at the top of app.py.")
        else:
            st.error(f"❌ Something went wrong: {err}")

# ─────────────────────────────────────────────
#  SIDEBAR — quick-start prompts
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("💡 Try these prompts")
    prompts = [
        "Quiz me on AZ-900 identity concepts",
        "Explain Zero Trust in plain English",
        "What does Microsoft Defender for Cloud do?",
        "What's the difference between authentication and authorisation?",
        "Quiz me on AZ-500 key vault topics",
        "What is the shared responsibility model?",
        "Explain RBAC vs ABAC in Azure",
    ]
    for p in prompts:
        if st.button(p, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": p})
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.rerun()
