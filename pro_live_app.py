from flask import Flask, render_template
from flask_socketio import SocketIO
import whisper
import sounddevice as sd
import numpy as np
import queue
import threading

# ---------------- BASIC SETUP ---------------- #

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load whisper model
model = whisper.load_model("base")

# Create audio queue
audio_queue = queue.Queue()

# ---------------- FRONTEND ROUTE ---------------- #

@app.route("/")
def index():
    return render_template("live.html")

# ---------------- AUDIO CAPTURE ---------------- #

def audio_callback(indata, frames, time, status):
    audio_queue.put(indata.copy())

def transcribe_audio():
    while True:
        audio = audio_queue.get()
        audio = np.squeeze(audio)

        result = model.transcribe(audio, fp16=False)
        text = result["text"]

        print("Original:", text)

        socketio.emit("original_text", {"text": text})

# ---------------- START STREAM ---------------- #

def start_stream():
    stream = sd.InputStream(
        samplerate=16000,
        channels=1,
        callback=audio_callback
    )
    with stream:
        transcribe_audio()

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    threading.Thread(target=start_stream).start()
    socketio.run(app, debug=True)