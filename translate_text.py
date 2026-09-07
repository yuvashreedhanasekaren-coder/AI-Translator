import sys
from deep_translator import GoogleTranslator

lang = sys.argv[1]

with open("transcript.txt", "r", encoding="utf-8") as f:
    text = f.read()

translated = GoogleTranslator(source='auto', target=lang).translate(text)

with open("translated.txt", "w", encoding="utf-8") as f:
    f.write(translated)

print("Translation complete")
