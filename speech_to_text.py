import whisper
import os

# Force CPU
model = whisper.load_model("base", device="cpu")

audio_file = "extracted_audio.wav"

if not os.path.exists(audio_file):
    raise FileNotFoundError("extracted_audio.wav not found!")

result = model.transcribe(audio_file)

segments = result["segments"]

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisec = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millisec:03}"

with open("subtitles.srt", "w", encoding="utf-8") as f:
    for i, segment in enumerate(segments, start=1):
        start = format_time(segment["start"])
        end = format_time(segment["end"])
        text = segment["text"].strip()

        f.write(f"{i}\n")
        f.write(f"{start} --> {end}\n")
        f.write(f"{text}\n\n")

print("Subtitles.srt generated successfully!")
