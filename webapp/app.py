from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Try to import the local chatbot wrapper from src. This is intentionally
# tolerant: if your `src.chatbot` exposes a `Chatbot` class with an `ask`
# or `run` method it will be used. Otherwise the API will return a helpful
# message explaining the backend isn't available.
bot = None
try:
    from src.chatbot import Chatbot
    bot = Chatbot()
except Exception:
    try:
        from src.chatbot import ChatBot as Chatbot
        bot = Chatbot()
    except Exception:
        bot = None


def get_answer(message: str):
    if not bot:
        return {"answer": "Backend chatbot not available. Ensure `src.chatbot` exports a `Chatbot` class with an `ask()` or `run()` method.", "sources": []}
    try:
        if hasattr(bot, "ask"):
            ans = bot.ask(message)
        elif hasattr(bot, "run"):
            ans = bot.run(message)
        elif hasattr(bot, "get_answer"):
            ans = bot.get_answer(message)
        else:
            ans = str(bot)
        if isinstance(ans, dict):
            return ans
        return {"answer": str(ans), "sources": []}
    except Exception as e:
        return {"answer": f"Error running chatbot: {e}", "sources": []}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        message = data.get("message", "")
        result = get_answer(message)
        return jsonify(result)
    except Exception:
        return jsonify({"answer": "Internal server error", "error": traceback.format_exc()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
