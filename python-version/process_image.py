import os

import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import datetime
import json

app = Flask(__name__, static_folder='src', static_url_path='/')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Replace 'YOUR_DEFAULT_API_KEY' with the name of the environment variable
DEFAULT_API_KEY = os.environ.get('OPENAI_API_KEY', 'YOUR_DEFAULT_API_KEY')

@app.route('/')
def index():
    """Return the index.html page."""
    return app.send_static_file('index.html')

@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

@socketio.on('summarize')
def summarize_image(data):
    print(data)
    summary = process_image(data['data'])
    # summary = "THIS IS A TEST"
    print(summary)
    if 'error' in summary:
        socketio.emit('error', summary)
    else:
        with open("gptv_logs.csv", "a") as f:
            f.write("%s,%s\n" % (datetime.datetime.now(), summary["choices"][0]["message"]["content"].replace("\n", ";")))
        socketio.emit('summary', {'summary': summary["choices"][0]["message"]["content"]})
    # socketio.emit('summary', {'summary': summary})

def process_image(base64_image):
    if base64_image:
        api_key = DEFAULT_API_KEY
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What’s in this image? Be descriptive. For each significant item recognized, wrap this word in <b> tags. Example: The image shows a <b>man</b> in front of a neutral-colored <b>wall</b>. He has short hair, wears <b>glasses</b>, and is donning a pair of over-ear <b>headphones</b>. ... Also output an itemized list of objects recognized, wrapped in <br> and <b> tags with label <br><b>Objects:."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            return {'error': 'Failed to process the image.'}

        return json.loads(response.content.decode('utf-8'))

    else:
        return {'error': 'No image data received.'}


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)