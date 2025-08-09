import yt_dlp
import uuid
import os
from .models import VideoInfo

def download_video(video_url: str, downloaded_video_save_path: str, video_info_save_path: str) -> VideoInfo:
    """
    Downloads a video from the given URL and saves it to the specified path as an MKV file.
    Also saves the video info as JSON using the VideoInfo.to_dict method.
    Args:
        video_url (str): The URL of the video to download.
        downloaded_video_save_path (str): The path where the downloaded video will be saved.
        video_info_save_path (str): The path where the video info JSON will be saved.
    Returns:
        VideoInfo: Metadata and info about the downloaded video.
    Raises:
        ValueError: If the video cannot be downloaded or info cannot be extracted.
    """
    if not downloaded_video_save_path.lower().endswith('.mkv'):
        print(f"downloaded_video_save_path does not end with .mkv, appending .mkv to: {downloaded_video_save_path}")
        downloaded_video_save_path += '.mkv'
    save_dir = os.path.dirname(downloaded_video_save_path)
    print(f"Ensuring save directory exists: {save_dir}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"Downloading video from URL: {video_url}")
    ydl_opts = {
        'format': 'bv*[height=720]+ba/b[height<=720]/b',
        'format_sort': ['res:720', 'fps:30', 'vcodec:h264'],
        'merge_output_format': 'mkv',
        'outtmpl': downloaded_video_save_path,
        'noplaylist': True,
        'prefer_ffmpeg': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
    if info_dict is None:
        print(f"Failed to download or extract video info for: {video_url}")
        raise ValueError("Failed to download or extract video info.")
    print(f"Video downloaded and info extracted. Saving path: {downloaded_video_save_path}")
    info_dict['downloaded_file'] = downloaded_video_save_path
    video_info = VideoInfo.from_dict(info_dict)
    # Save video info as JSON
    import json
    with open(video_info_save_path, "w", encoding="utf-8") as f:
        json.dump(video_info.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"Video info saved to: {video_info_save_path}")
    print(f"Returning VideoInfo object.")
    return video_info
