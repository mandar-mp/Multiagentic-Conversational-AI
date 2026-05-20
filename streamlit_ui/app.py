import streamlit as st
from api_client import send_chat_message, check_backend_health
from config import AppConfig

CONFIG = AppConfig()

# Page configuration and theme settings.
st.set_page_config(
    page_title=CONFIG.app_title,
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)


def reset_conversation() -> None:
    """Reset the conversation history and conversation ID."""
    st.session_state.messages = []
    st.session_state.conversation_id = ""
    st.session_state.status = "Ready to chat"


def render_message(message: dict) -> None:
    """Render a single message bubble with a role-specific style."""
    is_user = message["role"] == "user"
    tag = "You" if is_user else "Gemini"
    role_class = "user" if is_user else "assistant"

    st.markdown(
        f"<div class='message-row {role_class}'>"
        f"  <div class='message-tag'>{tag}</div>"
        f"  <div class='message-bubble'>{message['content']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    """Render the stored conversation history."""
    if not st.session_state.messages:
        st.info("Start the conversation by typing a message below.")
        return

    for message in st.session_state.messages:
        render_message(message)


# Initialize session state.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""
if "status" not in st.session_state:
    st.session_state.status = "Ready to chat"

# Sidebar content.
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input(
        label="Backend API Base URL",
        value=CONFIG.api_url,
        help="Set the backend chat API URL. Example: http://localhost:8000/api/v1",
    )
    
    # Check backend health
    is_healthy, health_msg = check_backend_health(api_url.strip() or CONFIG.api_url)
    if is_healthy:
        st.success(f"✓ {health_msg}")
    else:
        st.error(f"✗ {health_msg}")

    if st.button("Reset Conversation"):
        reset_conversation()

    st.markdown("---")
    st.write("**Conversation ID**")
    st.write(st.session_state.conversation_id or "new session")
    st.markdown("---")
    st.write("**Status**")
    st.info(st.session_state.status)
    st.markdown("---")
    st.caption("Built for easy integration with your FastAPI backend.")

# Application UI.
st.markdown(
    "<style>div[data-testid='stSidebar'] {background: #0b1220; color: #eef2ff;} </style>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='header'><h1>Gemini-style Streamlit Chat</h1>"
    "<p>Simple, production-ready, and easy to customize.</p></div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<style>"
    "  .header h1 { margin-bottom: 0.1rem; }"
    "  .header p { margin-top: 0.1rem; color: #aab3cd; }"
    "  .message-row { margin-bottom: 18px; display: flex; flex-direction: column; }"
    "  .message-tag { font-size: 0.82rem; color: #7f8bb6; margin-bottom: 6px; }"
    "  .message-bubble { padding: 16px; border-radius: 18px; line-height: 1.6; }"
    "  .user .message-bubble { background: rgba(71, 85, 223, 0.15); border: 1px solid rgba(120, 130, 255, 0.35); color: #eef2ff; }"
    "  .assistant .message-bubble { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255,255,255,0.12); color: #f0f4ff; }"
    "  .stTextArea textarea { background: #07101d; color: #eef2ff; border: 1px solid rgba(255,255,255,0.1); }"
    "  .stButton button { background: linear-gradient(135deg, #7b72ff, #11d1ff); border: none; color: white; }"
    "  .stApp { background: #06101c; color: #eef2ff; }"
    "</style>",
    unsafe_allow_html=True,
)

st.markdown("## Conversation")

render_chat_history()

st.markdown("---")

with st.form(key="chat_form"):
    user_input = st.text_area("Your message", key="user_input", height=140)
    submitted = st.form_submit_button("Send to Gemini")

if submitted and user_input.strip():
    st.session_state.status = "Sending message..."
    try:
        response = send_chat_message(
            message=user_input.strip(),
            conversation_id=st.session_state.conversation_id,
            api_url=api_url.strip() or CONFIG.api_url,
        )

        st.session_state.conversation_id = response.get("conversation_id", "")
        st.session_state.messages.append(
            {"role": "user", "content": user_input.strip()}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": response.get("response", "")}
        )
        st.session_state.status = "Reply received"
        st.experimental_rerun()
    except Exception as exc:
        error_detail = str(exc)
        st.session_state.status = f"Error: {error_detail}"
        st.error(f"Unable to send the message:\n\n{error_detail}\n\nEnsure the backend API is running at: {api_url.strip() or CONFIG.api_url}")
        st.stop()

if st.session_state.status:
    st.success(st.session_state.status)
