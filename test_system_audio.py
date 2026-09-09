import sounddevice as sd
import numpy as np

duration = 5  # seconds
samplerate = 16000

print("Recording system audio for 5 seconds...")

recording = sd.rec(int(duration * samplerate),
                   samplerate=samplerate,
                   channels=1,
                   dtype='float32')

sd.wait()

print("Recording finished.")

print("Audio data sample:")
print(recording[:10])