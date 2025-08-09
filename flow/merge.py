from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

def merge_video_audio(
    original_video_path: str,
    generated_narration_path: str,
    final_video_save_path: str,
    original_audio_volume_percentage: float = 0.0,
) -> None:
    """
    Mix the original video's audio (attenuated by a percentage) with the generated narration,
    then write a new video.

    Args:
        original_video_path: Path to the original video file (with its original audio).
        generated_narration_path: Path to the generated narration audio file.
        final_video_save_path: Path where the merged video will be saved.
        original_audio_volume_percentage: Linear gain for the original audio, in [0.0 .. 1.0].
            - 0.0 = mute original (full replace by narration)
            - 1.0 = keep original at its native loudness
            - e.g. 0.2 = keep 20% of original loudness (“TV-style ducking”)

    Behavior:
        - Uses MoviePy v2 APIs: `with_volume_scaled`, `CompositeAudioClip`, `with_audio`.
        - If original_audio_volume_percentage <= 0 or original audio is missing, narration replaces it.
    """
    # Clamp to [0, 1] and warn if out of range.
    if original_audio_volume_percentage < 0.0 or original_audio_volume_percentage > 1.0:
        print(
            f"original_audio_volume_percentage {original_audio_volume_percentage} is out of range; "
            "clamping to [0.0, 1.0]."
        )
        original_audio_volume_percentage = max(0.0, min(1.0, original_audio_volume_percentage))

    print(f"Merging (ducked original {original_audio_volume_percentage*100:.0f}%): {original_video_path} + VO {generated_narration_path}")

    # Load video and its original audio (if any)
    video_clip = VideoFileClip(original_video_path)
    base_audio = video_clip.audio

    # Load the generated narration at its native loudness
    narration_audio = AudioFileClip(generated_narration_path)

    # Build the final mixed track
    if base_audio is not None and original_audio_volume_percentage > 0.0:
        ducked = base_audio.with_volume_scaled(original_audio_volume_percentage)
        mixed_audio = CompositeAudioClip([ducked, narration_audio])
    else:
        # Replace original audio entirely
        mixed_audio = narration_audio

    # Attach mixed audio back to the video and write file
    out_clip = video_clip.with_audio(mixed_audio)
    print(f"Saving final video to: {final_video_save_path}")
    out_clip.write_videofile(final_video_save_path, codec="libx264", audio_codec="aac")

    # Cleanup
    for clip in (narration_audio, mixed_audio, video_clip, out_clip):
        try:
            clip.close()
        except Exception:
            pass

    print("Merge complete.")
