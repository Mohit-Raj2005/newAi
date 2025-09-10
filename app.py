from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS for production
CORS(app, origins=["*"])  # You can restrict this to your domain later

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/ask', methods=["POST", "OPTIONS"])
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
        return jsonify({"answer": "Server missing GEMINI_API_KEY. Please contact administrator."}), 500

    payload = {"contents": [{"parts": [{"text": question}]}]}

    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
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
        error_msg = f"Gemini API error: {e.response.status_code}"
        return jsonify({"answer": error_msg}), 500
    except Exception as e:
        return jsonify({"answer": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # For production, use environment variables for host and port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
