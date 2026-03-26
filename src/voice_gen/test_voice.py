from gtts import gTTS
import os

text_exemplu = "Salutare! Acesta este primul test pentru robotul de YouTube. Sper să iasă un video viral!"

tts = gTTS(text=text_exemplu, lang='ro')

output_path = "test_audio.mp3"
tts.save(output_path)

print(f"Succes! Fișierul a fost salvat ca: {output_path}")
