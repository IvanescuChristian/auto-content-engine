"""
main_shorts_local.py — GUI pt Shorts/TikTok:
  Reddit stories + Medal.tv clips + Kokoro TTS + Karaoke subs
  Features: clip splitting, keyword search, text cleaning
NU se pune pe git (e in .gitignore).
"""
import tkinter as tk
from tkinter import messagebox, ttk
import os
import subprocess
import threading
import tempfile

from voice_gen.kokoro_narration import generate_voice, VOICE_PRESETS
from voice_gen.karaoke_subs import generate_karaoke_ass, generate_karaoke_simple
from voice_gen.tts_cleaner import clean_for_tts, split_into_parts
from shorts_gen.reddit import get_reddit_stories, format_story_for_tts
from videoclips_gen.medal_fetcher import fetch_gaming_clips, get_trending_clips, download_clips

BG_MAIN = "#0f0f1a"
BG_CARD = "#1a1a2e"
FG_TEXT = "#e0e0e0"
FG_DIM = "#888899"
ACCENT = "#e94560"
ACCENT_ACTIVE = "#c73050"
ACCENT2 = "#533483"
ACCENT2_ACTIVE = "#6a45a0"
ENTRY_BG = "#16213e"
ENTRY_FG = "#e0e0e0"

PREVIEW_TEXT = "The universe is vast and full of mysteries waiting to be discovered."

HIGHLIGHT_COLORS = {
    "🟡 Yellow": "&H0000FFFF",
    "🔴 Red":    "&H000000FF",
    "🟢 Green":  "&H0000FF00",
    "🔵 Cyan":   "&H00FFFF00",
    "🟠 Orange": "&H000080FF",
    "🟣 Pink":   "&H00FF00FF",
}

POPULAR_SUBS = [
    "AmItheAsshole", "tifu", "confession", "relationship_advice",
    "MaliciousCompliance", "pettyrevenge", "ProRevenge", "entitledparents",
    "TrueOffMyChest", "nosleep", "LetsNotMeet", "UnresolvedMysteries",
    "askreddit", "todayilearned", "Showerthoughts"
]

MEDAL_KEYWORDS = [
    "pvp", "montage", "parkour", "clutch", "ace", "headshot",
    "trickshot", "snipe", "flick", "wallbang", "collateral",
    "teamkill", "fail", "funny", "insane", "epic", "rage",
    "1v5", "1v4", "1v3", "deagle", "knife", "noscope",
    "speedrun", "world record", "glitch", "bug", "hack",
]


def cleanup():
    for f in ["short_audio.wav", "short_subs.ass", "short_subs.srt",
              "final_short.mp4", "temp_short_nosubs.mp4"]:
        if os.path.exists(f):
            os.remove(f)
    # Cleanup multi-part files
    for f in os.listdir('.'):
        if f.startswith('final_short_part') and f.endswith('.mp4'):
            os.remove(f)


def get_video_duration(path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path]
        return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
    except Exception:
        return 30.0


def preview_voice():
    voice = combo_voice.get()
    if voice not in VOICE_PRESETS:
        return
    def do_preview():
        root.after(0, lambda: btn_preview.config(text="Playing...", state=tk.DISABLED))
        tmp = os.path.join(tempfile.gettempdir(), "voice_preview.wav")
        try:
            audio_path, _ = generate_voice(PREVIEW_TEXT, output_path=tmp, preset=voice)
            if audio_path and os.path.exists(audio_path):
                import platform
                if platform.system() == "Windows":
                    import winsound
                    winsound.PlaySound(audio_path, winsound.SND_FILENAME)
                else:
                    os.system(f"aplay '{audio_path}' 2>/dev/null || afplay '{audio_path}' 2>/dev/null")
        except Exception as e:
            print(f"[Preview] Error: {e}")
        finally:
            root.after(0, lambda: btn_preview.config(text="▶ Preview", state=tk.NORMAL))
            try: os.remove(tmp)
            except: pass
    threading.Thread(target=do_preview, daemon=True).start()


# ── MEDAL KEYWORD SEARCH ────────────────────────────────────
def search_medal_clips(game_name, keywords, num_clips=5):
    """
    Cauta clipuri pe Medal dupa keywords.
    Combina game name + keywords in search query.
    """
    from videoclips_gen.medal_fetcher import resolve_api_key, find_game_id, fetch_json, load_proxies
    import requests

    api_key = resolve_api_key(game_name)
    if not api_key:
        return []

    headers = {"Authorization": api_key}
    proxies = load_proxies()
    all_clips = []

    for kw in keywords:
        query = f"{game_name} {kw}".strip()
        url = f"https://developers.medal.tv/v1/search?text={query}&limit=5"
        print(f"[Medal Search] '{query}'...")

        data, _, _ = fetch_json(url, headers, proxies, 0, 0)
        if data and "contentObjects" in data:
            all_clips.extend(data["contentObjects"])

    # Deduplicate
    seen = set()
    unique = []
    for c in all_clips:
        cid = c.get("contentId", "")
        if cid not in seen:
            seen.add(cid)
            unique.append(c)

    # Filter montages, short clips
    skip_words = ["montage", "edit", "intro", "cinematic", "trailer", "movavi", "filmora"]
    filtered = [c for c in unique
                if not any(w in c.get("contentTitle", "").lower() for w in skip_words)
                and 5 <= c.get("videoLengthSeconds", 0) <= 60]

    if not filtered:
        filtered = unique

    filtered.sort(key=lambda c: c.get("contentViews", 0), reverse=True)
    return download_clips(filtered, max_clips=num_clips)


# ── VIDEO ASSEMBLER ──────────────────────────────────────────
def create_short_video(clip_paths, audio_path, ass_path, output="final_short.mp4", is_vertical=True):
    from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
    voice = AudioFileClip(audio_path)
    total_duration = voice.duration

    clips = []
    total_clip_dur = 0
    for path in clip_paths:
        try:
            clip = VideoFileClip(path).without_audio()
            clip = clip.resized(height=1080)
            
            clips.append(clip)
            total_clip_dur += clip.duration
        except Exception as e:
            print(f"  [Skip] {path}: {e}")

    if not clips:
        return False, "No valid clips"

    if total_clip_dur < total_duration:
        clips = clips * (int(total_duration / total_clip_dur) + 1)

    video = concatenate_videoclips(clips, method="compose")
    video = video.subclipped(0, min(total_duration, video.duration))
    video = video.with_audio(voice)

    temp_path = "temp_short_nosubs.mp4"
    video.write_videofile(temp_path, fps=30, codec="libx264", audio_codec="aac",
                          bitrate="8000k", threads=4)

    ass_abs = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")

    if is_vertical:
        vf = f"crop=ih*(9/16):ih,scale=1080:1920,subtitles='{ass_abs}'"
    else:
        vf = f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,subtitles='{ass_abs}'"

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", temp_path, "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", "-b:v", "8000k", output]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if result.returncode == 0:
        return True, output
    else:
        return False, f"FFmpeg failed: {result.stderr[:200]}"


# ── PIPELINE ─────────────────────────────────────────────────
def run_pipeline(story, game_name, voice_preset, is_vertical, highlight_color,
                 sub_style, words_per_group, clip_mode, medal_keywords, do_split):
    try:
        cleanup()

        # Clean text for TTS
        raw_script = format_story_for_tts(story)
        script = clean_for_tts(raw_script)
        print(f"[TTS Clean] {len(raw_script)} -> {len(script)} chars")

        # Split into parts if needed
        if do_split:
            parts = split_into_parts(script, max_seconds=58)
        else:
            parts = [(1, script)]

        total_parts = len(parts)
        if total_parts > 1:
            print(f"[Split] Story split into {total_parts} parts")

        for part_num, part_text in parts:
            part_suffix = f"_part{part_num}" if total_parts > 1 else ""
            audio_file = f"short_audio{part_suffix}.wav"
            ass_file = f"short_subs{part_suffix}.ass"
            out_file = f"final_short{part_suffix}.mp4"

            if total_parts > 1:
                # Add "Follow for part X" at the end
                if part_num < total_parts:
                    part_text += f". Follow for part {part_num + 1}."
                root.after(0, lambda p=part_num: status_label.config(
                    text=f"Part {p}/{total_parts}: Voice..."))
            else:
                root.after(0, lambda: status_label.config(text="1/4: Voice..."))

            # 1. Voice
            audio_path, timings = generate_voice(part_text, output_path=audio_file,
                                                  preset=voice_preset)
            if not audio_path:
                root.after(0, lambda: messagebox.showerror("Error", "Voice failed!"))
                return

            # 2. Karaoke subs
            root.after(0, lambda: status_label.config(text=f"Karaoke subs..."))
            if sub_style == "Word-by-word":
                generate_karaoke_ass(timings, output_ass=ass_file, font_size=65,
                                      highlight_color=highlight_color,
                                      is_vertical=is_vertical,
                                      words_per_group=words_per_group)
            else:
                generate_karaoke_simple(timings, output_ass=ass_file, font_size=65,
                                         highlight_color=highlight_color,
                                         is_vertical=is_vertical,
                                         words_per_group=words_per_group)

            # 3. Medal clips
            audio_dur = get_video_duration(audio_path)
            num_clips = max(2, int(audio_dur / 15) + 2)
            root.after(0, lambda n=num_clips: status_label.config(
                text=f"Downloading {n} clips..."))

            if clip_mode == "Keyword" and medal_keywords:
                clip_paths = search_medal_clips(game_name, medal_keywords, num_clips)
            else:
                clip_paths = fetch_gaming_clips(game_name, num_clips)

            if not clip_paths:
                root.after(0, lambda: messagebox.showerror("Error",
                    f"No clips for '{game_name}'"))
                return

            # 4. Assemble
            root.after(0, lambda: status_label.config(text="Rendering..."))
            success, msg = create_short_video(clip_paths, audio_path, ass_file,
                                               output=out_file, is_vertical=is_vertical)
            if not success:
                root.after(0, lambda m=msg: messagebox.showerror("Error", m))
                return

        # Done
        root.after(0, lambda: status_label.config(text="Done!"))
        if total_parts > 1:
            files = ", ".join(f"final_short_part{i}.mp4" for i in range(1, total_parts + 1))
            root.after(0, lambda: messagebox.showinfo("Success",
                f"{total_parts} parts generated!\n{files}"))
        else:
            root.after(0, lambda: messagebox.showinfo("Success",
                "Short done! → final_short.mp4"))

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
        root.after(0, lambda: status_label.config(text="Error"))
    finally:
        root.after(0, lambda: btn_generate.config(state=tk.NORMAL))


# ── STORY PICKER ─────────────────────────────────────────────
def fetch_and_pick():
    btn_generate.config(state=tk.DISABLED)
    subreddit = entry_subreddit.get().strip() or "AmItheAsshole"
    game = entry_game.get().strip()
    voice = combo_voice.get()
    is_vertical = var_format.get() == "Vertical"
    h_color = HIGHLIGHT_COLORS.get(combo_highlight.get(), "&H0000FFFF")
    sub_style = combo_sub_style.get()
    wpg = int(spin_wpg.get())
    clip_mode = combo_clip_mode.get()
    do_split = var_split.get()

    # Medal keywords
    medal_kws = []
    if clip_mode == "Keyword":
        raw = entry_keywords.get().strip()
        if raw:
            medal_kws = [k.strip() for k in raw.split(",") if k.strip()]
        else:
            messagebox.showwarning("Warning", "Enter keywords for Medal search!")
            btn_generate.config(state=tk.NORMAL)
            return

    if not game:
        messagebox.showwarning("Warning", "Enter a game name!")
        btn_generate.config(state=tk.NORMAL)
        return

    def fetch():
        root.after(0, lambda: status_label.config(text=f"Fetching r/{subreddit}..."))
        stories = get_reddit_stories(subreddit=subreddit, limit=10)
        if not stories:
            root.after(0, lambda: messagebox.showerror("Error", f"No stories in r/{subreddit}"))
            root.after(0, lambda: btn_generate.config(state=tk.NORMAL))
            return
        root.after(0, lambda: show_picker(stories, game, voice, is_vertical,
                                           h_color, sub_style, wpg, clip_mode,
                                           medal_kws, do_split))

    threading.Thread(target=fetch, daemon=True).start()


def show_picker(stories, game, voice, is_vertical, h_color, sub_style, wpg,
                clip_mode, medal_kws, do_split):
    win = tk.Toplevel(root)
    win.title("Pick a Story")
    win.geometry("550x450")
    win.configure(bg=BG_MAIN)

    tk.Label(win, text="Pick a story:", font=("Segoe UI", 12, "bold"),
             bg=BG_MAIN, fg=FG_TEXT).pack(pady=(15, 5))

    frame = tk.Frame(win, bg=BG_MAIN)
    frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    sb = tk.Scrollbar(frame)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    lb = tk.Listbox(frame, width=70, height=15, font=("Segoe UI", 10),
                     bg=BG_CARD, fg=FG_TEXT, selectbackground=ACCENT,
                     selectforeground="white", borderwidth=0, yscrollcommand=sb.set)
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.config(command=lb.yview)

    for s in stories:
        words = len(s['body'].split())
        est = int(words / 2.5)
        parts_est = max(1, est // 58)
        tag = f"[{est}s"
        if parts_est > 1 and do_split:
            tag += f", {parts_est} parts"
        tag += "]"
        lb.insert(tk.END, f"{tag} {s['title'][:65]}")

    def on_select():
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Pick a story!"); return
        win.destroy()
        threading.Thread(target=run_pipeline,
                         args=(stories[sel[0]], game, voice, is_vertical,
                               h_color, sub_style, wpg, clip_mode,
                               medal_kws, do_split), daemon=True).start()

    win.protocol("WM_DELETE_WINDOW", lambda: [win.destroy(), btn_generate.config(state=tk.NORMAL)])
    tk.Button(win, text="Generate Short", font=("Segoe UI", 11, "bold"),
              bg=ACCENT, fg="white", activebackground=ACCENT_ACTIVE,
              cursor="hand2", relief="flat", padx=20, pady=8,
              command=on_select).pack(pady=10)


def show_sub_picker():
    win = tk.Toplevel(root)
    win.title("Subreddits")
    win.geometry("300x420")
    win.configure(bg=BG_MAIN)
    tk.Label(win, text="Pick:", font=("Segoe UI", 11, "bold"),
             bg=BG_MAIN, fg=FG_TEXT).pack(pady=(10, 5))
    for sub in POPULAR_SUBS:
        tk.Button(win, text=f"r/{sub}", font=("Segoe UI", 10), anchor="w",
                  padx=15, pady=3, bg=BG_CARD, fg=FG_TEXT,
                  activebackground=ACCENT, activeforeground="white",
                  cursor="hand2", width=30, relief="flat",
                  command=lambda s=sub: [win.destroy(), entry_subreddit.delete(0, tk.END),
                                          entry_subreddit.insert(0, s)]).pack(pady=1, padx=15)


def show_keyword_picker():
    win = tk.Toplevel(root)
    win.title("Medal Keywords")
    win.geometry("300x500")
    win.configure(bg=BG_MAIN)
    tk.Label(win, text="Pick keywords:", font=("Segoe UI", 11, "bold"),
             bg=BG_MAIN, fg=FG_TEXT).pack(pady=(10, 5))
    tk.Label(win, text="Click to add (comma-separated)", font=("Segoe UI", 8),
             bg=BG_MAIN, fg=FG_DIM).pack()

    for kw in MEDAL_KEYWORDS:
        tk.Button(win, text=kw, font=("Segoe UI", 10), anchor="w",
                  padx=15, pady=2, bg=BG_CARD, fg=FG_TEXT,
                  activebackground=ACCENT2, activeforeground="white",
                  cursor="hand2", width=25, relief="flat",
                  command=lambda k=kw: add_keyword(k)).pack(pady=1, padx=15)

def add_keyword(kw):
    current = entry_keywords.get().strip()
    if current:
        existing = [k.strip().lower() for k in current.split(",")]
        if kw.lower() not in existing:
            entry_keywords.delete(0, tk.END)
            entry_keywords.insert(0, f"{current}, {kw}")
    else:
        entry_keywords.insert(0, kw)


def on_clip_mode_change(*args):
    mode = combo_clip_mode.get()
    if mode == "Keyword":
        kw_frame.pack(after=combo_clip_mode.master, fill=tk.X, pady=(4, 0))
    else:
        kw_frame.pack_forget()


# ── GUI ──────────────────────────────────────────────────────
def run():
    global root, btn_generate, btn_preview, combo_voice
    global entry_subreddit, entry_game, entry_keywords, var_format, status_label
    global combo_highlight, combo_sub_style, spin_wpg
    global combo_clip_mode, kw_frame, var_split

    root = tk.Tk()
    root.title("Shorts Generator (Local)")
    root.geometry("490x850")
    root.resizable(False, True)
    root.configure(bg=BG_MAIN)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TCombobox', fieldbackground=BG_CARD, background=ENTRY_BG,
                     foreground=FG_TEXT, borderwidth=0)
    style.map('TCombobox', fieldbackground=[('readonly', BG_CARD)])

    fl = ("Segoe UI", 10, "bold")
    fe = ("Segoe UI", 10)
    fh = ("Segoe UI", 8)

    # Scrollable
    outer = tk.Frame(root, bg=BG_MAIN)
    outer.pack(fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(outer, bg=BG_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    content = tk.Frame(canvas, bg=BG_MAIN)
    cw = canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
    content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    # Header
    hdr = tk.Frame(content, bg=BG_MAIN)
    hdr.pack(fill=tk.X, pady=(10, 5))
    tk.Label(hdr, text="⚡ SHORTS GENERATOR", font=("Segoe UI", 15, "bold"),
             bg=BG_MAIN, fg=FG_TEXT).pack()
    tk.Label(hdr, text="Reddit + Medal + Kokoro + Karaoke",
             font=("Segoe UI", 9), bg=BG_MAIN, fg=ACCENT).pack()

    # ── STORY ──
    c1 = tk.Frame(content, bg=BG_CARD, padx=15, pady=10,
                  highlightthickness=1, highlightbackground="#2a2a4a")
    c1.pack(fill=tk.X, padx=15, pady=4)
    tk.Label(c1, text="📖 STORY", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 4))

    r1 = tk.Frame(c1, bg=BG_CARD)
    r1.pack(fill=tk.X, pady=2)
    tk.Label(r1, text="Subreddit:", font=fl, bg=BG_CARD, fg=FG_TEXT).pack(side=tk.LEFT)
    entry_subreddit = tk.Entry(r1, font=fe, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat",
                                insertbackground=FG_TEXT, highlightthickness=1,
                                highlightbackground="#2a2a4a", highlightcolor=ACCENT)
    entry_subreddit.insert(0, "AmItheAsshole")
    entry_subreddit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 5))
    tk.Button(r1, text="📋", font=("Segoe UI", 10), bg=ACCENT2, fg="white",
              cursor="hand2", relief="flat", padx=6, command=show_sub_picker).pack(side=tk.RIGHT)

    # Split toggle
    var_split = tk.BooleanVar(value=True)
    tk.Checkbutton(c1, text="Auto-split long stories (Follow for part 2...)",
                   variable=var_split, font=fh, bg=BG_CARD, fg=FG_TEXT,
                   selectcolor=BG_CARD, activebackground=BG_CARD).pack(anchor="w", pady=(4, 0))

    # ── BACKGROUND ──
    c2 = tk.Frame(content, bg=BG_CARD, padx=15, pady=10,
                  highlightthickness=1, highlightbackground="#2a2a4a")
    c2.pack(fill=tk.X, padx=15, pady=4)
    tk.Label(c2, text="🎮 CLIPS", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 4))

    r2 = tk.Frame(c2, bg=BG_CARD)
    r2.pack(fill=tk.X, pady=2)
    tk.Label(r2, text="Game:", font=fl, bg=BG_CARD, fg=FG_TEXT, width=7, anchor="w").pack(side=tk.LEFT)
    entry_game = tk.Entry(r2, font=fe, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat",
                           insertbackground=FG_TEXT, highlightthickness=1,
                           highlightbackground="#2a2a4a", highlightcolor=ACCENT)
    entry_game.insert(0, "Minecraft")
    entry_game.pack(side=tk.LEFT, fill=tk.X, expand=True)

    r3 = tk.Frame(c2, bg=BG_CARD)
    r3.pack(fill=tk.X, pady=2)
    tk.Label(r3, text="Mode:", font=fl, bg=BG_CARD, fg=FG_TEXT, width=7, anchor="w").pack(side=tk.LEFT)
    combo_clip_mode = ttk.Combobox(r3, values=["Trending", "Keyword"],
                                    state="readonly", font=fe)
    combo_clip_mode.set("Trending")
    combo_clip_mode.pack(side=tk.LEFT, fill=tk.X, expand=True)
    combo_clip_mode.bind("<<ComboboxSelected>>", on_clip_mode_change)

    # Keyword search frame (hidden by default)
    kw_frame = tk.Frame(c2, bg=BG_CARD)
    kw_r = tk.Frame(kw_frame, bg=BG_CARD)
    kw_r.pack(fill=tk.X, pady=2)
    tk.Label(kw_r, text="Keywords:", font=fl, bg=BG_CARD, fg=FG_TEXT).pack(side=tk.LEFT)
    entry_keywords = tk.Entry(kw_r, font=fe, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat",
                               insertbackground=FG_TEXT, highlightthickness=1,
                               highlightbackground="#2a2a4a", highlightcolor=ACCENT)
    entry_keywords.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
    tk.Button(kw_r, text="🏷️", font=("Segoe UI", 10), bg=ACCENT2, fg="white",
              cursor="hand2", relief="flat", padx=6,
              command=show_keyword_picker).pack(side=tk.RIGHT)
    tk.Label(kw_frame, text="comma-separated: pvp, clutch, ace...",
             font=fh, bg=BG_CARD, fg=FG_DIM).pack(anchor="w")

    # ── FORMAT ──
    c3 = tk.Frame(content, bg=BG_CARD, padx=15, pady=10,
                  highlightthickness=1, highlightbackground="#2a2a4a")
    c3.pack(fill=tk.X, padx=15, pady=4)
    tk.Label(c3, text="📐 FORMAT", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 4))
    fmt = tk.Frame(c3, bg=BG_CARD)
    fmt.pack(fill=tk.X)
    var_format = tk.StringVar(value="Vertical")
    tk.Radiobutton(fmt, text="TikTok 9:16", variable=var_format, value="Vertical",
                   bg=BG_CARD, fg=FG_TEXT, selectcolor=BG_CARD, font=fe).pack(side=tk.LEFT)
    tk.Radiobutton(fmt, text="YouTube 16:9", variable=var_format, value="Landscape",
                   bg=BG_CARD, fg=FG_TEXT, selectcolor=BG_CARD, font=fe).pack(side=tk.LEFT, padx=15)

    # ── SUBTITLES ──
    c5 = tk.Frame(content, bg=BG_CARD, padx=15, pady=10,
                  highlightthickness=1, highlightbackground="#2a2a4a")
    c5.pack(fill=tk.X, padx=15, pady=4)
    tk.Label(c5, text="✨ KARAOKE", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 4))

    rs1 = tk.Frame(c5, bg=BG_CARD)
    rs1.pack(fill=tk.X, pady=2)
    tk.Label(rs1, text="Style:", font=fl, bg=BG_CARD, fg=FG_TEXT, width=7, anchor="w").pack(side=tk.LEFT)
    combo_sub_style = ttk.Combobox(rs1, values=["Word-by-word", "Smooth fill"],
                                    state="readonly", font=fe)
    combo_sub_style.set("Word-by-word")
    combo_sub_style.pack(side=tk.LEFT, fill=tk.X, expand=True)

    rs2 = tk.Frame(c5, bg=BG_CARD)
    rs2.pack(fill=tk.X, pady=2)
    tk.Label(rs2, text="Color:", font=fl, bg=BG_CARD, fg=FG_TEXT, width=7, anchor="w").pack(side=tk.LEFT)
    combo_highlight = ttk.Combobox(rs2, values=list(HIGHLIGHT_COLORS.keys()),
                                    state="readonly", font=fe)
    combo_highlight.set("🟡 Yellow")
    combo_highlight.pack(side=tk.LEFT, fill=tk.X, expand=True)

    rs3 = tk.Frame(c5, bg=BG_CARD)
    rs3.pack(fill=tk.X, pady=2)
    tk.Label(rs3, text="Words:", font=fl, bg=BG_CARD, fg=FG_TEXT, width=7, anchor="w").pack(side=tk.LEFT)
    spin_wpg = tk.Spinbox(rs3, from_=3, to=8, width=5, font=fe,
                           bg=ENTRY_BG, fg=ENTRY_FG, buttonbackground=BG_CARD)
    spin_wpg.delete(0, tk.END)
    spin_wpg.insert(0, "5")
    spin_wpg.pack(side=tk.LEFT)
    tk.Label(rs3, text="per screen", font=fh, bg=BG_CARD, fg=FG_DIM).pack(side=tk.LEFT, padx=8)

    # ── VOICE ──
    c4 = tk.Frame(content, bg=BG_CARD, padx=15, pady=10,
                  highlightthickness=1, highlightbackground="#2a2a4a")
    c4.pack(fill=tk.X, padx=15, pady=4)
    tk.Label(c4, text="🎙️ VOICE", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 4))
    rv = tk.Frame(c4, bg=BG_CARD)
    rv.pack(fill=tk.X, pady=2)
    combo_voice = ttk.Combobox(rv, values=list(VOICE_PRESETS.keys()),
                                state="readonly", font=fe)
    combo_voice.set(list(VOICE_PRESETS.keys())[0])
    combo_voice.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    btn_preview = tk.Button(rv, text="▶ Preview", font=("Segoe UI", 9, "bold"),
                             bg=ACCENT2, fg="white", activebackground=ACCENT2_ACTIVE,
                             cursor="hand2", relief="flat", padx=8,
                             command=preview_voice)
    btn_preview.pack(side=tk.RIGHT)

    # ── GENERATE ──
    btn_generate = tk.Button(content, text="Fetch Stories & Generate",
                              font=("Segoe UI", 13, "bold"),
                              bg=ACCENT, fg="white", activebackground=ACCENT_ACTIVE,
                              relief="flat", cursor="hand2", pady=12,
                              command=fetch_and_pick)
    btn_generate.pack(fill=tk.X, padx=15, pady=(10, 5))

    status_label = tk.Label(content, text="Ready", font=("Segoe UI", 10),
                             bg=BG_MAIN, fg=FG_DIM)
    status_label.pack(pady=3)

    tk.Label(content, text="Reddit → Clean → Kokoro → Medal → Karaoke → FFmpeg",
             font=fh, bg=BG_MAIN, fg=FG_DIM).pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    run()
