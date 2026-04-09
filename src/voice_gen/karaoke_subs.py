import re

# Culori ASS format: &HAABBGGRR& (BGR, nu RGB!)
COLOR_NORMAL = "&H00FFFFFF"    # alb
COLOR_HIGHLIGHT = "&H0000FFFF"  # galben (TikTok-style)

# --- DICTIONAR INVERS PENTRU AFISARE ---
# Transforma textul lung inapoi in prescurtari pentru ecran
REVERSE_DICT = {
    r'(?i)\bwould i be the asshole\b': 'WIBTA',
    r'(?i)\bam i the asshole\b': 'AITA',
    r'(?i)\btoday i messed up\b': 'TIFU',
    r'(?i)\bfor what it is worth\b': 'FWIW',
    r'(?i)\bin my opinion\b': 'IMO',
    r'(?i)\bin my humble opinion\b': 'IMHO',
    r'(?i)\bshaking my head\b': 'SMH',
    r'(?i)\bif i remember correctly\b': 'IIRC',
    r'(?i)\byou are the asshole\b': 'YTA',
    r'(?i)\bnot the asshole\b': 'NTA',
    r'(?i)\beveryone sucks here\b': 'ESH',
    r'(?i)\bno assholes here\b': 'NAH',
    r'(?i)\bthe original poster\b': 'OP',
    r'(?i)\bsignificant other\b': 'SO',
    r'(?i)\bmother in law\b': 'MIL',
    r'(?i)\bfather in law\b': 'FIL',
    r'(?i)\bbrother in law\b': 'BIL',
    r'(?i)\bsister in law\b': 'SIL',
    r'(?i)\bstay at home mom\b': 'SAHM',
    r'(?i)\bstay at home dad\b': 'SAHD',
    r'(?i)\bno contact\b': 'NC',
    r'(?i)\blow contact\b': 'LC',
    r'(?i)\bsoon to be ex\b': 'STBX',
    r'(?i)\bedited to add\b': 'ETA',
}

# --- TIMING WEIGHTS ---
# Pacalim sistemul ca abrevierea are lungimea textului rostit
# WIBTA = "would i be the asshole" (22 chars)
SPOKEN_WEIGHTS = {
    "WIBTA": 22, "AITA": 16, "TIFU": 17, "FWIW": 20, "IMO": 13, "IMHO": 20,
    "SMH": 15, "IIRC": 23, "YTA": 19, "NTA": 15, "ESH": 19, "NAH": 16,
    "OP": 19, "SO": 17, "MIL": 13, "FIL": 13, "BIL": 14, "SIL": 13,
    "SAHM": 16, "SAHD": 16, "NC": 10, "LC": 11, "STBX": 13, "ETA": 13
}

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def revert_text_for_display(text):
    for pattern, replacement in REVERSE_DICT.items():
        text = re.sub(pattern, replacement, text)
    return text

def get_word_weight(word):
    clean_w = re.sub(r'[^A-Z]', '', word.upper())
    return SPOKEN_WEIGHTS.get(clean_w, len(word))


def generate_karaoke_ass(chunk_timings, output_ass="short_subs.ass",
                         font_size=65, highlight_color=None,
                         is_vertical=True, words_per_group=5):
    """ Varianta Word-by-Word care respecta prescurtarile """
    if highlight_color is None:
        highlight_color = COLOR_HIGHLIGHT

    if is_vertical:
        res_x, res_y = 1080, 1920
        margin_v = 800
    else:
        res_x, res_y = 1920, 1080
        margin_v = 100

    header = f"""[Script Info]
Title: Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {res_x}
PlayResY: {res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{COLOR_NORMAL},{highlight_color},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogues = []

    for chunk in chunk_timings:
        if isinstance(chunk, dict):
            chunk_text = chunk.get("text", "")
            chunk_start = float(chunk.get("start", 0.0))
            chunk_end = float(chunk.get("end", 0.0))
        else:
            chunk_start, chunk_end, chunk_text = chunk
            chunk_start = float(chunk_start)
            chunk_end = float(chunk_end)

        # Traducem inapoi in abrevieri pt ecran
        chunk_text = revert_text_for_display(chunk_text)

        words = chunk_text.strip().split()
        if not words:
            continue

        chunk_duration = chunk_end - chunk_start
        # Calculam "greutatea" totala a chunk-ului
        total_weight = max(1, sum(get_word_weight(w) for w in words))

        word_timings = []
        current_time = chunk_start
        for word in words:
            weight = get_word_weight(word)
            word_dur = (weight / total_weight) * chunk_duration
            word_dur = max(0.15, word_dur)
            word_timings.append((current_time, current_time + word_dur, word))
            current_time += word_dur

        if word_timings:
            scale = chunk_duration / (current_time - chunk_start)
            adjusted = []
            t = chunk_start
            for _, _, w in word_timings:
                weight = get_word_weight(w)
                dur = (weight / total_weight) * chunk_duration
                dur = max(0.15, dur) * scale
                adjusted.append((t, t + dur, w))
                t += dur
            word_timings = adjusted

        for group_start_idx in range(0, len(word_timings), words_per_group):
            group = word_timings[group_start_idx:group_start_idx + words_per_group]
            if not group:
                continue

            group_words = [w for _, _, w in group]

            for word_idx, (w_start, w_end, word) in enumerate(group):
                parts = []
                for j, gw in enumerate(group_words):
                    if j == word_idx:
                        parts.append(f"{{\\c{highlight_color}}}{gw}{{\\c{COLOR_NORMAL}}}")
                    else:
                        parts.append(gw)

                text = " ".join(parts)
                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)

                dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header)
        for line in dialogues:
            f.write(line + "\n")

    print(f"[Karaoke] Generated {len(dialogues)} dialogue lines -> {output_ass}")
    return output_ass


def generate_karaoke_simple(chunk_timings, output_ass="short_subs.ass",
                             font_size=65, highlight_color=None,
                             is_vertical=True, words_per_group=5):
    """ Varianta Smooth Fill (\kf) care respecta prescurtarile """
    if highlight_color is None:
        highlight_color = COLOR_HIGHLIGHT

    if is_vertical:
        res_x, res_y = 1080, 1920
        margin_v = 800  
    else:
        res_x, res_y = 1920, 1080
        margin_v = 100

    header = f"""[Script Info]
Title: Karaoke Subtitles Smooth
ScriptType: v4.00+
WrapStyle: 1
PlayResX: {res_x}
PlayResY: {res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{highlight_color},{COLOR_NORMAL},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogues = []

    for chunk in chunk_timings:
        if isinstance(chunk, dict):
            chunk_text = chunk.get("text", "")
            chunk_start = float(chunk.get("start", 0.0))
            chunk_end = float(chunk.get("end", 0.0))
        else:
            chunk_start, chunk_end, chunk_text = chunk
            chunk_start = float(chunk_start)
            chunk_end = float(chunk_end)

        # Traducem inapoi in abrevieri pt ecran
        chunk_text = revert_text_for_display(chunk_text)

        words = chunk_text.strip().split()
        if not words:
            continue

        chunk_duration = chunk_end - chunk_start
        total_weight = max(1, sum(get_word_weight(w) for w in words))

        word_timings = []
        current_time = chunk_start
        for word in words:
            weight = get_word_weight(word)
            dur = (weight / total_weight) * chunk_duration
            dur = max(0.15, dur)
            word_timings.append((current_time, current_time + dur, word))
            current_time += dur

        if word_timings:
            scale = chunk_duration / (current_time - chunk_start)
            adjusted = []
            t = chunk_start
            for _, _, w in word_timings:
                weight = get_word_weight(w)
                dur = (weight / total_weight) * chunk_duration
                dur = max(0.15, dur) * scale
                adjusted.append((t, t + dur, w))
                t += dur
            word_timings = adjusted

        for group_start_idx in range(0, len(word_timings), words_per_group):
            group = word_timings[group_start_idx:group_start_idx + words_per_group]
            if not group:
                continue

            group_start = group[0][0]
            group_end = group[-1][1]

            kf_parts = []
            for w_start, w_end, word in group:
                dur_cs = int((w_end - w_start) * 100) 
                dur_cs = max(1, dur_cs) 
                kf_parts.append(rf"{{\kf{dur_cs}}}{word}")

            text = " ".join(kf_parts)
            start_str = format_ass_time(group_start)
            end_str = format_ass_time(group_end)

            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header)
        for line in dialogues:
            f.write(line + "\n")

    print(f"[Karaoke] Generated {len(dialogues)} smooth lines -> {output_ass}")
    return output_ass