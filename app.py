import os
import glob
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

# --- Validate API Key ---
GEMINI_API_KEY = "AIzaSyBvgW9daVuVsg6SqtSmDz25NIT044eeWHA"
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY environment variable.")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini model (fast + cheap, you can change to "gemini-1.5-pro" if needed)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

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

    print(f"📄 Loaded {len(docs)} documents.")
    return docs

def build_context(docs):
    return "\n\n".join([f"--- {d['name']} ---\n{d['content']}" for d in docs])

docs = read_docs()
doc_context = build_context(docs)

# ----------------------------
# Conversation Memory
# ----------------------------
ui_messages = []

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", messages=ui_messages)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")
    if not user_message:
        return jsonify({"error": "No message received"}), 400

    # Save user message
    ui_messages.append({"role": "user", "content": user_message})

    try:
        # Build conversation string for Gemini
        conversation = (
            "You are a helpful assistant. Use the provided document context to answer questions.\n\n"
            f"Here is the context:\n{doc_context}\n\n"
            "Conversation:\n"
        )
        for msg in ui_messages:
            conversation += f"{msg['role'].capitalize()}: {msg['content']}\n"

        # Send to Gemini
        response = model.generate_content(conversation)
        assistant_reply = response.text if response else "⚠️ No reply from Gemini."

        # Save reply
        ui_messages.append({"role": "", "content": assistant_reply})

        return jsonify({"reply": assistant_reply})

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        error_message = "⚠️ Error: Could not get response from Gemini."
        ui_messages.append({"role": "assistant", "content": error_message})
        return jsonify({"reply": error_message}), 500


if __name__ == "__main__":
    app.run(debug=True, port=3000)
