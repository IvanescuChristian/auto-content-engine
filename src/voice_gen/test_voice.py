"""
test_voice.py — Testeaza vocea Kokoro af_heart
Ruleaza: python test_voice.py
Prima rulare descarca modelul (~300MB) automat de pe HuggingFace.
Output: fisiere .wav in folderul curent
"""
from kokoro import KPipeline
import soundfile as sf
import os

print("=" * 50)
print("  KOKORO TTS - TEST VOCE")
print("=" * 50)
print()

# Initializeaza pipeline-ul
# 'a' = American English, 'hexgrad/Kokoro-82M' = modelul
# Prima rulare descarca automat ~300MB
print("[1/3] Incarcare model (prima data descarca ~300MB)...")
pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')

# Text de test — calming narration
text = """
Take a deep breath. Let the tension leave your body.
Feel the warmth of the light surrounding you.
You are safe. You are calm. You are exactly where you need to be.
Every breath you take fills you with peace and clarity.
The world outside can wait. This moment is yours.
"""

# Genereaza audio
# voice='af_heart' = cea mai buna voce feminina calming (Grade A)
# speed=0.9 = putin mai lent decat normal, mai calming
print("[2/3] Generare audio cu af_heart (speed=0.9)...")
print()

output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)

all_audio = []
for i, (gs, ps, audio) in enumerate(pipeline(text, voice='af_heart', speed=0.9)):
    filepath = os.path.join(output_dir, f"test_{i}.wav")
    sf.write(filepath, audio, 24000)
    all_audio.append(audio)
    print(f"  Chunk {i}: \"{gs.strip()[:60]}...\"")
    print(f"           -> {filepath}")

# Concateneaza tot intr-un singur fisier
import numpy as np
silence = np.zeros(int(24000 * 0.4))  # 400ms pauza intre propozitii
combined = []
for i, chunk in enumerate(all_audio):
    combined.append(chunk)
    if i < len(all_audio) - 1:
        combined.append(silence)
combined = np.concatenate(combined)

full_path = os.path.join(output_dir, "test_FULL.wav")
sf.write(full_path, combined, 24000)
duration = len(combined) / 24000

print()
print(f"[3/3] GATA!")
print(f"  Fisier complet: {full_path} ({duration:.1f} secunde)")
print(f"  Deschide {full_path} si asculta!")
print()
print("Daca vocea suna bine, foloseste kokoro_narration.py pentru proiect.")
