import sys
from gtts import gTTS

lang = sys.argv[1]

with open("translated.txt", "r", encoding="utf-8") as f:
    text = f.read()

tts = gTTS(text=text, lang=lang)
tts.save("translated_audio.mp3")

print("Audio generated")
