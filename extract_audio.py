import subprocess
import os

input_video = "input_video.mp4"
output_audio = "extracted_audio.wav"

if not os.path.exists(input_video):
    raise FileNotFoundError("input_video.mp4 not found!")

subprocess.run([
    "ffmpeg",
    "-y",
    "-i", input_video,
    "-vn",              # no video
    "-acodec", "pcm_s16le",
    "-ar", "16000",     # 16k sample rate (good for Whisper)
    "-ac", "1",         # mono
    output_audio
], check=True)

print("Audio extracted successfully!")
