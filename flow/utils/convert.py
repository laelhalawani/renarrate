from moviepy import VideoFileClip
import os

def convert_video(source_path: str, converted_save_path_or_ext: str) -> None:
    """
    Converts a video file to the format specified by the extension or path using moviepy.
    If converted_save_path_or_ext is an extension (e.g. '.mp4', 'mp4'), saves to source_path with new extension.
    If it's a full path, saves to that path.
    Args:
        source_path (str): Path to the source video file.
        converted_save_path_or_ext (str): Extension ('.ext' or 'ext') or full path to save the converted video.
    Returns:
        None
    """
    # Determine if input is extension or path
    ext_candidate = converted_save_path_or_ext.lower().lstrip('.')
    # If input contains a path separator or ends with a known video extension, treat as path
    if os.path.sep in converted_save_path_or_ext or os.path.splitext(converted_save_path_or_ext)[1]:
        save_path = converted_save_path_or_ext
        ext = os.path.splitext(save_path)[1].lower().lstrip('.')
        if not ext:
            raise ValueError(f"No extension found in save path: {save_path}")
    else:
        # Treat as extension
        ext = ext_candidate
        base, _ = os.path.splitext(source_path)
        save_path = f"{base}.{ext}"
    print(f"Converting {source_path} to {save_path} (format: {ext})")
    video_clip = VideoFileClip(source_path)
    video_clip.write_videofile(save_path)
    print(f"Conversion complete: {save_path}")
