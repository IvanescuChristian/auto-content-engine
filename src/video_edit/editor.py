import os
import random
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip

VIDEO_SIZE = (1920, 1080)

def apply_ken_burns_no_bars(clip, duration, video_size=VIDEO_SIZE):
    """
    Ken Burns effect care GARANTEAZA full-screen fara black bars.
    Functioneaza pe orice imagine — portrait, landscape, patrat.
    Strategia: scale to COVER (nu contain), apoi crop centrat.
    """
    zoom_ratio = 0.06
    
    # Calculeaza scale factor ca sa ACOPERE tot frame-ul
    # (ca CSS background-size: cover)
    w, h = clip.w, clip.h
    target_w, target_h = video_size
    
    scale_w = target_w / w
    scale_h = target_h / h
    # Ia maximul ca sa acopere tot + extra pt zoom headroom
    base_scale = max(scale_w, scale_h) * (1.15 + zoom_ratio)
    
    # Aplica scale
    scaled = clip.resized(base_scale)
    scaled = scaled.with_duration(duration)
    
    # Ken Burns: zoom in sau zoom out
    if random.random() > 0.5:
        animated = scaled.resized(lambda t: 1 + (zoom_ratio * t / duration))
    else:
        animated = scaled.resized(lambda t: (1 + zoom_ratio) - (zoom_ratio * t / duration))
    
    # Crop centrat la exact 1920x1080
    final = animated.cropped(
        width=target_w, height=target_h,
        x_center=animated.w / 2, y_center=animated.h / 2
    )
    
    return final


def create_video(scene_duration=25):
    """
    Asambleaza video final din audio + imagini.
    """
    # Kokoro WAV, fallback MP3
    audio_path = "video_final.wav"
    if not os.path.exists(audio_path):
        audio_path = "video_final.mp3"

    pool_dir = "assets/curated_pool"
    music_path = "assets/music/background.mp3"
    output_path = "final_video.mp4"

    if not os.path.exists(audio_path):
        raise FileNotFoundError("Audio file missing. Run voice generation first.")

    if not os.path.exists(pool_dir) or not os.listdir(pool_dir):
        raise FileNotFoundError(f"No images in {pool_dir}. Run downloader first.")

    print(f"Preparing audio from {audio_path}...")
    voice_clip = AudioFileClip(audio_path)
    total_duration = voice_clip.duration
    final_audio = voice_clip

    # Background music (optional)
    if os.path.exists(music_path):
        try:
            background_music = AudioFileClip(music_path).with_duration(total_duration)
            background_music = background_music.with_volume_scaled(0.15)
            final_audio = CompositeAudioClip([voice_clip, background_music])
            print("Background music mixed.")
        except Exception:
            pass

    # Sorteaza imaginile
    source_images = sorted([
        os.path.join(pool_dir, img) for img in os.listdir(pool_dir)
        if img.lower().endswith(('jpg', 'png', 'jpeg'))
    ])

    num_scenes = int(total_duration / scene_duration) + 1
    print(f"Total: {total_duration:.0f}s | {scene_duration}s/scene | {num_scenes} scenes | {len(source_images)} images")

    clips = []
    for i in range(num_scenes):
        img_path = source_images[i % len(source_images)]
        img_clip = ImageClip(img_path)

        current_duration = scene_duration
        if i == num_scenes - 1:
            current_duration = total_duration - (i * scene_duration)
            if current_duration <= 0:
                break

        print(f"  Scene {i+1}: {os.path.basename(img_path)} ({img_clip.w}x{img_clip.h}) -> {current_duration:.1f}s")
        cinematic_clip = apply_ken_burns_no_bars(img_clip, current_duration)
        clips.append(cinematic_clip)

    print("Assembling final video...")
    video = concatenate_videoclips(clips, method="compose")
    video = video.with_audio(final_audio)

    print("Rendering final_video.mp4 ...")
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", threads=4)
    print(f"DONE! Output: {output_path}")
    return output_path
