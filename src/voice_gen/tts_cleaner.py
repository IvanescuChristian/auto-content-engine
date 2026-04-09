"""
tts_cleaner.py — Curata textul inainte de TTS (Kokoro).
Scoate caractere speciale, formatari Reddit, markdown, etc.
Kokoro citeste ciudat: \\ / | @ # $ ( ) [ ] { } * ~ ` etc.

Locatie: src/voice_gen/tts_cleaner.py
"""
import re


def clean_for_tts(text):
    """
    Curata textul complet pt TTS. Apeleaza inainte de generate_voice().
    """
    text = strip_markdown(text)
    text = strip_reddit_formatting(text)
    text = strip_special_chars(text)
    text = fix_punctuation(text)
    text = expand_common_abbreviations(text)
    text = normalize_whitespace(text)
    return text.strip()


def strip_markdown(text):
    """Scoate formatari Markdown/Gemini."""
    # Headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bold/italic
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    # Code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Blockquotes
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # List bullets
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text


def strip_reddit_formatting(text):
    """Scoate formatari specifice Reddit."""
    # Reddit quotes
    text = re.sub(r'^&gt;\s*', '', text, flags=re.MULTILINE)
    # Subreddit links
    text = re.sub(r'r/(\w+)', r'\1 subreddit', text)
    # User links
    text = re.sub(r'u/(\w+)', r'\1', text)
    # Edit notes
    text = re.sub(r'(?i)\bEDIT\s*\d*\s*:', 'Edit:', text)
    # TL;DR
    text = re.sub(r'(?i)TL;?DR\s*:?', 'In short,', text)
    # AITA / AITAH
    text = re.sub(r'\bAITA[H]?\b', 'Am I the asshole', text)
    # NTA, YTA, ESH, NAH
    text = re.sub(r'\bNTA\b', 'not the asshole', text)
    text = re.sub(r'\bYTA\b', 'you are the asshole', text)
    text = re.sub(r'\bESH\b', 'everyone sucks here', text)
    text = re.sub(r'\bNAH\b', 'no assholes here', text)
    # SO, FIL, MIL, BIL, SIL
    text = re.sub(r'\bSO\b', 'significant other', text)
    text = re.sub(r'\bFIL\b', 'father in law', text)
    text = re.sub(r'\bMIL\b', 'mother in law', text)
    text = re.sub(r'\bBIL\b', 'brother in law', text)
    text = re.sub(r'\bSIL\b', 'sister in law', text)
    return text


def strip_special_chars(text):
    """Scoate caractere pe care Kokoro le citeste ciudat."""
    # Backslash, pipes, tildes
    text = text.replace('\\n', ' ')
    text = text.replace('\\r', ' ')
    text = text.replace('\\t', ' ')
    text = text.replace('\\', ' ')
    text = text.replace('|', ', ')
    text = text.replace('~', ' ')
    text = text.replace('`', '')

    # Brackets, braces, angle brackets — scoate complet
    text = re.sub(r'[\[\]{}<>]', '', text)

    # Paranteze — pastreaza continutul, scoate parantezele
    text = re.sub(r'\(([^)]*)\)', r', \1, ', text)

    # Simboluri pe care le citeste literal
    text = text.replace('@', ' at ')
    text = text.replace('#', ' ')
    text = text.replace('$', ' dollars ')
    text = text.replace('%', ' percent ')
    text = text.replace('&', ' and ')
    text = text.replace('^', ' ')
    text = text.replace('*', '')
    text = text.replace('+', ' plus ')
    text = text.replace('=', ' equals ')

    # Underscores (des in Reddit usernames)
    text = text.replace('_', ' ')

    # Slash-uri — inlocuieste cu "or" sau spatiu
    text = re.sub(r'(\w)\s*/\s*(\w)', r'\1 or \2', text)  # "him/her" -> "him or her"
    text = text.replace('/', ' ')

    # Emoji unicode — scoate
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
                  r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
                  r'\U00002702-\U000027B0\U000024C2-\U0001F251'
                  r'\U0001f900-\U0001f9FF\U0001FA00-\U0001FA6F'
                  r'\U0001FA70-\U0001FAFF\U00002600-\U000026FF]+', '', text)

    return text


def fix_punctuation(text):
    """Repara punctuatia ca Kokoro sa nu faca pauze ciudate."""
    # Puncte multiple -> un singur punct
    text = re.sub(r'\.{2,}', '.', text)
    # Exclamari/intrebari multiple -> una
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    # Virgule multiple
    text = re.sub(r',{2,}', ',', text)
    # Semicolon -> virgula (Kokoro nu face pauza buna pe ;)
    text = text.replace(';', ',')
    # Colon la inceputul propozitiei -> virgula
    text = re.sub(r':\s+', ', ', text)
    # Dash-uri lungi -> virgula
    text = re.sub(r'\s*[—–-]{2,}\s*', ', ', text)
    text = re.sub(r'\s*—\s*', ', ', text)
    text = re.sub(r'\s*–\s*', ', ', text)
    # Quotes — scoate ghilimelele, pastreaza textul
    text = text.replace('"', '')
    text = text.replace('"', '')
    text = text.replace('"', '')
    text = text.replace("'", "'")  # smart quotes -> normal
    text = text.replace("'", "'")
    # Curata spatii inainte de punctuatie
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    return text


def expand_common_abbreviations(text):
    """Expandeaza abrevieri comune care suna ciudat citite literal."""
    abbrevs = {
        r'\bw/\b': 'with',
        r'\bw/o\b': 'without',
        r'\bb/c\b': 'because',
        r'\bb4\b': 'before',
        r'\bidk\b': "I don't know",
        r'\bimo\b': 'in my opinion',
        r'\bimho\b': 'in my humble opinion',
        r'\bbtw\b': 'by the way',
        r'\bfyi\b': 'for your information',
        r'\bsmh\b': 'shaking my head',
        r'\btbh\b': 'to be honest',
        r'\bngl\b': 'not gonna lie',
        r'\bafaik\b': 'as far as I know',
        r'\biirc\b': 'if I remember correctly',
        r'\bpov\b': 'point of view',
        r'\bdm\b': 'direct message',
        r'\bgf\b': 'girlfriend',
        r'\bbf\b': 'boyfriend',
        r'\bex\b': 'ex',
        r'\baka\b': 'also known as',
        r'\betc\b': 'etcetera',
        r'\bvs\b': 'versus',
        r'\byr\b': 'year',
        r'\byrs\b': 'years',
        r'\bhr\b': 'hour',
        r'\bhrs\b': 'hours',
        r'\bmin\b': 'minute',
        r'\bmins\b': 'minutes',
        r'\bnum\b': 'number',
        r'\binfo\b': 'information',
        r'\bconvo\b': 'conversation',
        r'\bcomms\b': 'communications',
    }
    for pattern, replacement in abbrevs.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def normalize_whitespace(text):
    """Curata spatii in exces."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n ', '\n', text)
    # Scoate linii goale repetate
    lines = [l.strip() for l in text.split('\n')]
    lines = [l for l in lines if l]
    return '\n'.join(lines)


def split_into_parts(text, max_seconds=58, words_per_second=2.5):
    """
    Sparge textul in parti pt multi-part shorts.
    max_seconds: durata maxima per parte (58s pt TikTok < 60s)
    
    Returns: lista de parti [(part_num, text), ...]
    """
    max_words = int(max_seconds * words_per_second)
    words = text.split()

    if len(words) <= max_words:
        return [(1, text)]

    parts = []
    part_num = 1
    i = 0

    while i < len(words):
        # Ia max_words cuvinte
        chunk_words = words[i:i + max_words]
        chunk = ' '.join(chunk_words)

        # Incearca sa taie la ultima propozitie completa
        last_period = max(chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
        if last_period > len(chunk) * 0.5:
            chunk = chunk[:last_period + 1]
            words_used = len(chunk.split())
        else:
            words_used = len(chunk_words)

        parts.append((part_num, chunk.strip()))
        part_num += 1
        i += words_used

    return parts
