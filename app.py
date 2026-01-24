from flask import Flask, render_template, request, jsonify
import requests
import base64
import os

app = Flask(__name__)

# GET TOKEN FROM ENVIRONMENT VARIABLE (For Security on Cloud)
HF_TOKEN = os.environ.get("HF_TOKEN") 
API_URL = "https://router.huggingface.co/v1/chat/completions"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_trade():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        image_bytes = file.read()
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        system_prompt = (
            "ACT AS: Senior Trading Psychologist. "
            "TASK: Analyze this trade screenshot. "
            "OUTPUT: Brutally honest diagnosis of FOMO, Risk, and Psychology. "
            "FORMAT: HTML formatted text with <b>bold</b> keys."
        )

        payload = {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                    ]
                }
            ],
            "max_tokens": 1000
        }

        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"analysis": response.json()['choices'][0]['message']['content']})
        return jsonify({"error": "AI Error"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
