import os
from moviepy import VideoFileClip, AudioFileClip
from settings import STORAGE_DIR

def merge_video_audio(
    video_no_audio_path: str,
    generated_narration_path: str,
    final_video_save_path: str
) -> None:
    """
    Merges a video file (without audio) and a generated narration audio file into a final video file.
    Args:
        video_no_audio_path (str): Path to the video file without audio.
        generated_narration_path (str): Path to the generated narration audio file.
        final_video_save_path (str): Path where the merged video will be saved.
    Returns:
        None
    """
    print(f"Merging video: {video_no_audio_path} with audio: {generated_narration_path}")
    video_clip = VideoFileClip(video_no_audio_path)
    new_audio_clip = AudioFileClip(generated_narration_path)
    video_clip.audio = new_audio_clip
    print(f"Saving final video to: {final_video_save_path}")
    video_clip.write_videofile(final_video_save_path, codec="libx264", audio_codec="aac")
    print("Merge complete.")
