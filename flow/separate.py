from moviepy import VideoFileClip

def separate_audio(
    source_video_path: str,
    audio_no_video_path: str,
    video_no_audio_path: str
) -> None:
    """
    Separates the audio from a video file, saving the audio and the video without audio to specified paths.
    Args:
        source_video_path (str): Path to the source video file.
        audio_no_video_path (str): Path where the extracted audio will be saved.
        video_no_audio_path (str): Path where the video without audio will be saved.
    Returns:
        None
    Raises:
        ValueError: If the video does not contain an audio track.
    """
    print(f"Loading video file: {source_video_path}")
    video_clip = VideoFileClip(source_video_path)
    if video_clip.audio is not None:
        print(f"Extracting audio to: {audio_no_video_path}")
        video_clip.audio.write_audiofile(audio_no_video_path)
    else:
        raise ValueError("No audio track found in video.")
    print(f"Saving video without audio to: {video_no_audio_path}")
    video_clip.without_audio().write_videofile(video_no_audio_path, codec="libx264", audio=False)
    print("Separation complete.")
