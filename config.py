"""
config.py — Incarca API keys din .env
Folosire:
    from config import GEMINI_API_KEY
"""
import os

def load_env(filepath=".env"):
    """Incarca variabile din .env in os.environ"""
    if not os.path.exists(filepath):
        print(f"[Config] ATENTIE: {filepath} nu exista!")
        print(f"[Config] Copiaza .env.example -> .env si pune cheile tale.")
        return
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Incarca automat la import
load_env()

# Export keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY or GEMINI_API_KEY == "PUNE_CHEIA_TA_AICI":
    print("[Config] ATENTIE: GEMINI_API_KEY nu e setat in .env!")
