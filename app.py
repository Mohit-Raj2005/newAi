from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "https://dcoderaibuddy.vercel.app/",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

@app.route('/health', methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "DCoder AI Backend is running",
        "api_configured": bool(GEMINI_API_KEY)
    }), 200

@app.route('/', methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "DCoder AI Backend API",
        "endpoints": {
            "/health": "Health check",
            "/ask": "Ask AI questions (POST)"
        },
        "status": "running"
    })

@app.route('/ask', methods=["POST"])
def ask_gemini():
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    
    if not question:
        return jsonify({"answer": "Please enter a valid question."}), 400
    
    if not GEMINI_API_KEY:
        return jsonify({"answer": "⚠️ Server configuration error: GEMINI_API_KEY not found."}), 500
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Please provide a helpful and informative answer to this question: {question}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1000,
        }
    }
    
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
        r.raise_for_status()
        result = r.json()
        
        answer = (
            result.get("candidates", [{}])[0]
                  .get("content", {})
                  .get("parts", [{}])[0]
                  .get("text", "")
            or "No response received from AI."
        )
        
        return jsonify({"answer": answer.strip()})
    
    except requests.HTTPError as e:
        error_msg = f"🚫 Gemini API error: HTTP {e.response.status_code}"
        if e.response.status_code == 429:
            error_msg += " (Rate limit exceeded. Please try again later.)"
        elif e.response.status_code == 403:
            error_msg += " (API key invalid or quota exceeded.)"
        return jsonify({"answer": error_msg}), 500
        
    except requests.Timeout:
        return jsonify({"answer": "⏰ Request timed out. Please try again with a shorter question."}), 500
        
    except Exception as e:
        return jsonify({"answer": f"🔧 Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
