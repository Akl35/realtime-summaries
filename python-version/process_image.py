import os
import time
import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import datetime
import json

app = Flask(__name__, static_folder='src', static_url_path='/')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
use_followup_prompt = False
conversation_history = []

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

    start_time = time.time()
    summary = process_image(data['data'])
    total_time = time.time() - start_time
    # summary = "THIS IS A TEST"
    print(summary)
    if 'error' in summary:
        socketio.emit('error', summary)
    else:
        with open("gptv_logs.csv", "a") as f:
            f.write("%s,%s,%s\n" % (datetime.datetime.now(), summary["choices"][0]["message"]["content"].replace("\n", ";"), total_time))
        socketio.emit('summary', {'summary': summary["choices"][0]["message"]["content"]})
    # socketio.emit('summary', {'summary': summary})
        
 # For image stitching: https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python
def process_image(base64_image):
    if base64_image:
        api_key = DEFAULT_API_KEY
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # Fix prompt to do this prompt initially and then ask what has changed in the image
        payload = {}
        gpt_prompt = "What’s in this image? Be descriptive. For each significant item recognized, wrap this word in <b> tags. Example: The image shows a <b>man</b> in front of a neutral-colored <b>wall</b>. He has short hair, wears <b>glasses</b>, and is donning a pair of over-ear <b>headphones</b>. ... Also output an itemized list of objects recognized, wrapped in <br> and <b> tags with label <br><b>Objects:."
        if use_followup_prompt:
            gpt_prompt = "Now, describe what is in this image by specifying if there are any new events in the image compared to the previous images. For each new or modified item, wrap the word in <b> tags. Example: In the updated scene, the <b>wall</b> color has changed to a vibrant <b>blue</b>. The <b>man</b> is now wearing a <b>hat</b> and has replaced the over-ear <b>headphones</b> with <b>earbuds</b>. ..."
        else:
            use_followup_prompt = True

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": conversation_history + [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": gpt_prompt
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
        

        conversation_history.append({"role": "user", "content": gpt_prompt})


    # measure the metrics for time it takes to finish request, test out with different image sizes 
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        summary = json.loads(response.content.decode('utf-8'))

        conversation_history.append({"role": "assistant", "content": summary["choices"][0]["message"]["content"]})

        if response.status_code != 200:
            return {'error': 'Failed to process the image.'}

        return summary

    else:
        return {'error': 'No image data received.'}


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)

# def process_image_sharedgpt(base64_image):
