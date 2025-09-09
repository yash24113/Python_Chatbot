import os
import openai
from flask import Flask, render_template, request, redirect
import glob

# --- Validate API Key ---
OPENAI_API_KEY = "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"
if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY environment variable.")

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# Read documents
def read_docs(doc_dir="docs"):
    allowed_exts = ("*.txt", "*.md", "*.pdf", "*.docx", "*.xlsx", "*.tsv")
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

# Combine docs into a single context string
def build_context(docs):
    return "\n\n".join([f"--- {d['name']} ---\n{d['content']}" for d in docs])

# Load docs once on server start
docs = read_docs()
doc_context = build_context(docs)

# Conversation history (UI messages only)
ui_messages = []

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", messages=ui_messages)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")
    if not user_message:
        return redirect("/")

    # Save user message for UI
    ui_messages.append({"role": "user", "content": user_message})

    try:
        # Construct conversation for GPT
        conversation = [
            {"role": "system", "content": "You are a helpful assistant. Use the provided document context to answer questions."},
            {"role": "system", "content": f"Here is the context:\n\n{doc_context}"},
        ] + ui_messages  # only user/assistant turns

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=conversation,
            temperature=0.2
        )
        assistant_reply = response.choices[0].message["content"]

        # Save assistant reply for UI
        ui_messages.append({"role": "assistant", "content": assistant_reply})
    except Exception as e:
        print(f"❌ GPT Error: {e}")
        ui_messages.append({"role": "assistant", "content": "⚠️ Error: Could not get response from GPT."})

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=3000)
