from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests
from dotenv import load_dotenv

load_dotenv(".env")  # loads .env file
app = Flask(__name__)
CORS(app)  # allow requests from your front-end (even file://)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
GEMINI_URL =f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
@app.route('/ask', methods=["POST","OPTIONS"])

def ask_gemini():
    if request.method == 'OPTIONS':
        # CORS preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"answer": "Please enter a valid question."}), 400
    if not GEMINI_API_KEY:
        return jsonify({"answer": "Server missing GEMINI_API_KEY."}), 500

    payload = {"contents": [{"parts": [{"text": question}]}]}

    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        r.raise_for_status()
        result = r.json()

        # Safely extract the model's text
        answer = (
            result.get("candidates", [{}])[0]
                  .get("content", {})
                  .get("parts", [{}])[0]
                  .get("text", "")
            or "No response received."
        )
        return jsonify({"answer": answer})
    except requests.HTTPError as e:
        return jsonify({"answer": f"Gemini API error: {e.response.text}"}), 500
    except Exception as e:
        return jsonify({"answer": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # For local dev
    # app.run(host="0.0.0.0", port=5000, debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Gemini AI Backend is running! Use POST /ask"})
