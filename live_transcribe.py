import sounddevice as sd
import numpy as np
import whisper
import librosa
import torch
from deep_translator import GoogleTranslator
import queue

# ================= SETTINGS =================
DEVICE_INDEX = 1
TARGET_RATE = 16000
CHUNK_DURATION = 5   # seconds per processing chunk
MODEL_SIZE = "base"

print("Loading Whisper model...")
model = whisper.load_model(MODEL_SIZE)

translator = GoogleTranslator(source='auto', target='en')

audio_queue = queue.Queue()

default_rate = int(sd.query_devices(DEVICE_INDEX)['default_samplerate'])

print("Listening continuously...")

# ================= CALLBACK =================
def callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

# ================= STREAM =================
with sd.InputStream(
    samplerate=default_rate,
    device=DEVICE_INDEX,
    channels=2,
    callback=callback
):
    buffer = np.empty((0, 2), dtype="float32")

    try:
        while True:
            data = audio_queue.get()
            buffer = np.vstack((buffer, data))

            # Process every CHUNK_DURATION seconds
            if len(buffer) >= default_rate * CHUNK_DURATION:

                chunk = buffer[:default_rate * CHUNK_DURATION]
                buffer = buffer[default_rate * CHUNK_DURATION:]

                # Stereo → Mono
                chunk = np.mean(chunk, axis=1)

                # Resample
                chunk = librosa.resample(chunk, orig_sr=default_rate, target_sr=TARGET_RATE)

                if np.max(np.abs(chunk)) < 0.01:
                    continue

                result = model.transcribe(
    chunk,
    task="translate",
    fp16=torch.cuda.is_available()
)
                text = result["text"].strip()

                if text:
                    print("Original:", text)

                    translated = translator.translate(text)
                    print("English:", translated)
                    print("-" * 50)

    except KeyboardInterrupt:
        print("\nStopped by user")