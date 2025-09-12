import os
import glob
from flask import Flask, request, jsonify
import google.generativeai as genai

# --- Configure Gemini ---

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")

if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY environment variable.")

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
            print(f"⚠️ Could not read {f}: {e}")

    return docs

def build_context(docs):
    return "\n\n".join([f"--- {d['name']} ---\n{d['content']}" for d in docs])

docs = read_docs()
doc_context = build_context(docs)

# ----------------------------
# Flask API
# ----------------------------
app = Flask(__name__)
messages = []  # Conversation memory

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Save user message
    messages.append({"role": "user", "content": user_message})

    try:
        # Build conversation string
        conversation = (
            "You are a helpful assistant. Use the provided document context to answer questions.\n\n"
            f"Here is the context:\n{doc_context}\n\nConversation:\n"
        )
        for msg in messages:
            conversation += f"{msg['role'].capitalize()}: {msg['content']}\n"

        # Generate response
        response = model.generate_content(conversation)
        assistant_reply = response.text if response else "⚠️ No reply from Gemini."

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        assistant_reply = "⚠️ Error: Could not get response from Gemini."

    # Save assistant reply
    messages.append({"role": "assistant", "content": assistant_reply})

    return jsonify({"reply": assistant_reply})

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "✅ Gemini chatbot API is live!",
        "docs_loaded": len(docs),
        "chat_endpoint": "/chat"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
