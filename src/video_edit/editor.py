import os
import random
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip

def create_video():
    audio_path = "video_final.mp3"
    pool_dir = "assets/curated_pool"
    music_path = "assets/music/background.mp3"
    output_path = "final_video.mp4"
    
    SCENE_DURATION = 25
    VIDEO_SIZE = (1920, 1080)

    if not os.path.exists(audio_path):
        raise FileNotFoundError("Audio file missing.")
    
    if not os.path.exists(pool_dir) or not os.listdir(pool_dir):
        raise FileNotFoundError(f"Missing images in {pool_dir}")

    voice_clip = AudioFileClip(audio_path)
    total_duration = voice_clip.duration
    
    final_audio = voice_clip

    if os.path.exists(music_path):
        try:
            background_music = AudioFileClip(music_path).with_duration(total_duration)
            background_music = background_music.with_volume_scaled(0.15) 
            final_audio = CompositeAudioClip([voice_clip, background_music])
        except Exception:
            pass

    source_images = [os.path.join(pool_dir, img) for img in sorted(os.listdir(pool_dir)) if img.endswith(('jpg', 'png', 'jpeg'))]
    
    num_scenes_needed = int(total_duration / SCENE_DURATION) + 1

    clips = []
    
    for i in range(num_scenes_needed):
        img_path = source_images[i % len(source_images)]
        
        img_clip = ImageClip(img_path).resized(VIDEO_SIZE)
        
        current_scene_duration = SCENE_DURATION
        if i == num_scenes_needed - 1:
            current_scene_duration = total_duration - (i * SCENE_DURATION)
            if current_scene_duration <= 0: break

        img_clip = img_clip.with_duration(current_scene_duration)

        zoom_ratio = 0.08
        if i % 2 == 0:
            img_clip = img_clip.resized(lambda t: 1 + (zoom_ratio * t / current_scene_duration))
        else:
            img_clip = img_clip.resized(lambda t: (1 + zoom_ratio) - (zoom_ratio * t / current_scene_duration))
        
        final_clip = CompositeVideoClip([img_clip.with_position('center')], size=VIDEO_SIZE).with_duration(current_scene_duration)
        clips.append(final_clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.with_audio(final_audio)

    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", threads=4)
    return output_path