import os
import glob
import streamlit as st
import google.generativeai as genai

# --- Configure Gemini ---
GEMINI_API_KEY = "AIzaSyBvgW9daVuVsg6SqtSmDz25NIT044eeWHA"
if not GEMINI_API_KEY:
    st.error("❌ Missing GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------------
# Document Loader
# ----------------------------
def read_docs(doc_dir="docs"):
    allowed_exts = ("*.txt", "*.md", "*.tsv")
    files = []
    for ext in allowed_exts:
        files.extend(glob.glob(os.path.join(doc_dir, ext)))

    docs = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                content = file.read()
                docs.append({"name": os.path.basename(f), "content": content})
        except Exception as e:
            st.warning(f"⚠️ Could not read {f}: {e}")

    return docs

def build_context(docs):
    return "\n\n".join([f"--- {d['name']} ---\n{d['content']}" for d in docs])

docs = read_docs()
doc_context = build_context(docs)

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="📄 Document Chatbot", layout="centered")
st.title("📄 Document Chatbot (Gemini LLM)")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Show chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# Input box
if user_input := st.chat_input("Type your question here..."):
    # Save user input
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    try:
        # Build conversation string
        conversation = (
            "You are a helpful assistant. Use the provided document context to answer questions.\n\n"
            f"Here is the context:\n{doc_context}\n\nConversation:\n"
        )
        for msg in st.session_state["messages"]:
            conversation += f"{msg['role'].capitalize()}: {msg['content']}\n"

        # Generate reply
        response = model.generate_content(conversation)
        assistant_reply = response.text if response else "⚠️ No reply from Gemini."

    except Exception as e:
        st.error(f"❌ Gemini Error: {e}")
        assistant_reply = "⚠️ Error: Could not get response from Gemini."

    # Save & display assistant reply
    st.session_state["messages"].append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").write(assistant_reply)
