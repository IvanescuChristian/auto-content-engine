# Auto Content Engine

Engine automat de generat video content cu narration AI.

## Ce face proiectul
1. **Genereaza script** (text narration)
2. **Transforma textul in voce** (Kokoro TTS — voce feminina calming)
3. **Proxy rotation** pentru request-uri externe (proxy_api.py)

---

## Structura proiect
```
auto-content-engine/
├── kokoro_env/            ← Python 3.12 venv (NU se pune in git)
├── test_output/           ← WAV-uri generate de test (se creeaza singur)
├── proxy_api.py           ← Proxy scraper (multiple surse)
├── install_kokoro.bat     ← Script instalare (o singura data)
├── test_voice.py          ← Test rapid voce — ruleaza dupa instalare
├── kokoro_narration.py    ← Generator narration principal
└── README.md              ← Acest fisier
```

---

## Instalare (o singura data)

### Cerinte
- Windows 10/11
- Python 3.12 STABIL (NU beta, NU 3.13, NU 3.14)
- ~2.5GB spatiu disk (PyTorch + model)
- Internet la prima rulare

### Pas 1 — Python 3.12
- Descarca de la: https://www.python.org/downloads/release/python-3120/
- Scroll jos → **"Windows installer (64-bit)"**
- La instalare: **Customize installation** → bifezi tot → Install
- NU trebuie sa bifezi "Add to PATH"

### Pas 2 — espeak-ng
- Descarca de la: https://github.com/espeak-ng/espeak-ng/releases
- Ia fisierul **`.msi`** (ex: espeak-ng-20191129-b702b03-x64.msi)
- Instaleaza (Next → Next → Install)
- Deschide **CMD ca Administrator**:
```cmd
setx PATH "%PATH%;C:\Program Files\eSpeak NG" /M
```
- Inchide CMD-ul

### Pas 3 — Setup environment
Deschide **CMD** (nu PowerShell!) si ruleaza pe rand:
```cmd
cd /d "D:\Python projects\Auto_Content_Engine\auto-content-engine"
"C:\Users\massi\AppData\Local\Programs\Python\Python312\python.exe" -m venv kokoro_env
kokoro_env\Scripts\activate.bat
python -m pip install --upgrade pip
pip install kokoro>=0.9.4 soundfile
```

NOTA: `pip install` dureaza 5-15 minute (descarca PyTorch ~2GB).
E normal sa para ca sta blocat — lasa-l sa termine.

### Pas 4 — Test voce
```cmd
python test_voice.py
```
Prima rulare descarca modelul Kokoro (~300MB). Dupa aia merge offline.
Rezultat: `test_output\test_FULL.wav` — deschide si asculta.

---

## Cum generez audio narration

### Activare environment (de fiecare data cand deschizi CMD)
```cmd
cd /d "D:\Python projects\Auto_Content_Engine\auto-content-engine"
kokoro_env\Scripts\activate.bat
```
Trebuie sa vezi `(kokoro_env)` la inceputul liniei.

### Varianta 1 — Din text direct
```cmd
python kokoro_narration.py --text "Take a deep breath. You are safe. You are calm." -o narration.wav --preset calm
```

### Varianta 2 — Din fisier .txt (recomandat pentru scripturi lungi)
Creezi un fisier `script.txt` cu textul narration-ului, apoi:
```cmd
python kokoro_narration.py --file script.txt -o narration.wav --preset calm
```

### Ce parsezi in script.txt
Fisier text simplu, fiecare propozitie/paragraf pe linie noua:
```
Take a deep breath. Let the tension leave your body.
Feel the warmth of the light surrounding you.

You are safe. You are calm. You are exactly where you need to be.
Every breath you take fills you with peace and clarity.

The world outside can wait. This moment is yours.
Close your eyes and let the stillness embrace you.
```

Reguli:
- Scrie in engleza (modelul e antrenat pe engleza)
- Linie goala = pauza mai lunga intre paragrafe
- Nu pune instructiuni sau taguri — doar textul care se va auzi
- Propozitii de 10-30 cuvinte = calitate optima
- Script-ul `kokoro_narration.py` sparge automat textele prea lungi

### Output
- Format: **WAV 24kHz mono**
- Direct compatibil cu orice video editor (Premiere, DaVinci, CapCut, ffmpeg)
- Fara watermark, fara limite, fara costuri

### Preset-uri
| Preset       | Voce      | Viteza | Cand il folosesti              |
|--------------|-----------|--------|--------------------------------|
| `calm`       | af_heart  | 0.85   | Meditatie, relaxare, ASMR      |
| `narration`  | af_heart  | 0.90   | Narration standard video       |
| `storytell`  | af_bella  | 0.95   | Povestire, documentar          |
| `educational`| af_bella  | 1.00   | Tutorial, educational          |
| `british`    | bf_emma   | 0.90   | Accent britanic, formal        |

### Custom (fara preset)
```cmd
python kokoro_narration.py --file script.txt -o output.wav --voice af_heart --speed 0.88 --pause 0.5
```

Parametri:
- `--voice` — af_heart (calm), af_bella (rich), bf_emma (british)
- `--speed` — 0.80 (foarte lent) → 1.0 (normal) → 1.2 (rapid)
- `--pause` — pauza in secunde intre propozitii (default 0.4)
- `--lang` — a (american), b (british)

---

## Pipeline complet (cum se leaga totul)

```
[1. Script text]     Scrii/generezi textul narration in script.txt
        |
        v
[2. Kokoro TTS]      python kokoro_narration.py --file script.txt -o narration.wav
        |
        v
[3. Audio WAV]       narration.wav — gata de pus pe video
        |
        v
[4. Video edit]      Combini audio + imagini/video in editorul tau
```

Proxy-ul (proxy_api.py) se foloseste cand pipeline-ul va include
request-uri externe (gen API-uri de generare imagini, scraping, etc).
Kokoro TTS ruleaza 100% local — nu consuma proxy-uri.

---

## Troubleshooting

| Problema | Fix |
|----------|-----|
| numpy/torch build failed | Ai Python 3.13/3.14 sau beta. Trebuie Python 3.12 stabil |
| espeak-ng not found | Instaleaza MSI + adauga in PATH (vezi Pas 2) |
| activate.bat nu merge | Esti in PowerShell? Scrie `cmd` primul |
| Scripts disabled (PowerShell) | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| pip pare blocat la install | Normal, descarca ~2GB. Asteapta 5-15 min |
| Vocea se grabeste | Foloseste kokoro_narration.py (smart splitting automat) |
| Prima rulare lenta | Normal, descarca model 300MB. Dupa aia merge offline |

---

## Despre Kokoro TTS
- **82M parametri** — mic, rapid, ruleaza si pe CPU
- **Apache-2.0** — comercial OK, fara restrictii
- **#1 in TTS Arena** — calitate peste modele mult mai mari
- **100% offline** dupa prima descarcare
- GitHub: https://github.com/hexgrad/kokoro
- Model: https://huggingface.co/hexgrad/Kokoro-82M
