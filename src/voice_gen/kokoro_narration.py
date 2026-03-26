"""
voice_gen/kokoro_narration.py — Genereaza narration audio cu Kokoro TTS
Inlocuieste gTTS. Se apeleaza din gui/main.py sau direct.

Folosire din alt script:
    from voice_gen.kokoro_narration import generate_voice
    generate_voice("Your text here", output_path="video_final.wav")

Folosire CLI:
    python -m voice_gen.kokoro_narration --file script.txt -o narration.wav --preset calm
"""
import os
import re
import sys
import numpy as np

# ── SETARI VOCE ──────────────────────────────────────────────
VOICE_PRESETS = {
    "calm":       {"voice": "af_heart", "speed": 0.85, "lang": "a", "pause": 0.5},
    "narration":  {"voice": "af_heart", "speed": 0.90, "lang": "a", "pause": 0.4},
    "storytell":  {"voice": "af_bella", "speed": 0.95, "lang": "a", "pause": 0.35},
    "educational":{"voice": "af_bella", "speed": 1.00, "lang": "a", "pause": 0.3},
    "british":    {"voice": "bf_emma",  "speed": 0.90, "lang": "b", "pause": 0.4},
}

# ── SMART TEXT SPLITTING ─────────────────────────────────────
MIN_WORDS = 15
MAX_WORDS = 70

def smart_split(text):
    """Sparge textul in chunk-uri optime pt Kokoro (15-70 cuvinte)."""
    text = text.strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    chunks = []
    buffer = ""

    for para in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            test = f"{buffer} {sentence}".strip() if buffer else sentence
            word_count = len(test.split())
            if word_count <= MAX_WORDS:
                buffer = test
            else:
                if buffer and len(buffer.split()) >= MIN_WORDS:
                    chunks.append(buffer)
                    buffer = sentence
                elif buffer:
                    chunks.append(test)
                    buffer = ""
                else:
                    parts = sentence.split(', ')
                    sub_buffer = ""
                    for part in parts:
                        sub_test = f"{sub_buffer}, {part}".strip(', ') if sub_buffer else part
                        if len(sub_test.split()) > MAX_WORDS:
                            if sub_buffer:
                                chunks.append(sub_buffer)
                            sub_buffer = part
                        else:
                            sub_buffer = sub_test
                    if sub_buffer:
                        buffer = sub_buffer

    if buffer:
        if len(buffer.split()) < MIN_WORDS and chunks:
            chunks[-1] = f"{chunks[-1]} {buffer}"
        else:
            chunks.append(buffer)

    return chunks


# ── FUNCTIA PRINCIPALA — apelata din gui/main.py ────────────
def generate_voice(text, output_path="video_final.wav", preset="narration",
                   voice=None, speed=None, lang=None, pause_seconds=None):
    """
    Genereaza audio WAV din text folosind Kokoro TTS.
    
    Args:
        text:           Scriptul narration (string)
        output_path:    Unde salveaza WAV-ul (default: video_final.wav)
        preset:         "calm", "narration", "storytell", "educational", "british"
        voice/speed/lang/pause_seconds: Override manual (ignora preset)
    
    Returns:
        output_path daca reuseste, None daca esueaza
    """
    import soundfile as sf
    from kokoro import KPipeline

    # Aplica preset, apoi override-uri
    p = VOICE_PRESETS.get(preset, VOICE_PRESETS["narration"])
    v = voice or p["voice"]
    s = speed or p["speed"]
    l = lang or p["lang"]
    pause = pause_seconds or p["pause"]

    print(f"[Kokoro] Voice: {v} | Speed: {s} | Lang: {l} | Preset: {preset}")
    print(f"[Kokoro] Incarcare model...")
    pipeline = KPipeline(lang_code=l, repo_id='hexgrad/Kokoro-82M')

    chunks = smart_split(text)
    print(f"[Kokoro] Text spart in {len(chunks)} chunk-uri")

    all_audio = []
    silence = np.zeros(int(24000 * pause))

    for idx, chunk in enumerate(chunks):
        word_count = len(chunk.split())
        print(f"  [{idx+1}/{len(chunks)}] ({word_count} cuv) \"{chunk[:60]}...\"")

        chunk_audio = []
        for i, (gs, ps, audio) in enumerate(pipeline(chunk, voice=v, speed=s)):
            chunk_audio.append(audio)

        if chunk_audio:
            combined_chunk = np.concatenate(chunk_audio)
            all_audio.append(combined_chunk)
            if idx < len(chunks) - 1:
                all_audio.append(silence)

    if not all_audio:
        print("[Kokoro] EROARE: Nu s-a generat audio!")
        return None

    full_audio = np.concatenate(all_audio)
    sf.write(output_path, full_audio, 24000)

    duration = len(full_audio) / 24000
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n[Kokoro] GATA! {output_path}")
    print(f"  Durata: {duration:.1f}s | Size: {size_kb:.0f} KB | 24kHz WAV")
    return output_path


# ── CLI (rulare directa) ────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Kokoro TTS Narration Generator")
    parser.add_argument("--text", type=str, help="Text direct")
    parser.add_argument("--file", type=str, help="Fisier .txt cu scriptul")
    parser.add_argument("--output", "-o", type=str, default="narration.wav")
    parser.add_argument("--preset", choices=list(VOICE_PRESETS.keys()), default="narration")
    parser.add_argument("--voice", type=str)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--lang", type=str)
    parser.add_argument("--pause", type=float)
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"EROARE: {args.file} nu exista!"); sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Foloseste --text sau --file"); sys.exit(1)

    generate_voice(
        text=text, output_path=args.output, preset=args.preset,
        voice=args.voice, speed=args.speed, lang=args.lang,
        pause_seconds=args.pause
    )
