from flow.download import download_video
from flow.separate import separate_audio
from flow.generate_cc import generate_cc
from flow.translate_cc import translate_transcription
from flow.renarrate import generate_narration
from flow.merge import merge_video_audio
from flow.models.video_paths import VideoProcessingPaths
from flow.tts.gemini_voices import select_voice_by_name as select_gemini_voice
from flow.tts.elevenlabs_voices import select_voice_by_name as select_elevenlabs_voice
from flow.models.voices import Voice
from flow.utils.convert import convert_video
from flow.utils.languages import select_language_by_name
from settings import STORAGE_DIR
import os


def run_pipeline(video_url: str, target_language: str, voice:Voice) -> VideoProcessingPaths:
    """
    Runs the full video processing pipeline: download, separate audio, generate CC, translate CC, generate narration, and merge.
    Args:
        video_url (str): The URL of the video to process.
        target_language (str): The language to translate the CC into.
    Returns:
        str: Path to the final processed video file.
    """
    processing_paths = VideoProcessingPaths(base_dir=STORAGE_DIR, create=True)

    # Step 1: Download video
    download_video(video_url, processing_paths.downloaded_video_path, processing_paths.video_info_path)

    # Step 2: Separate audio
    separate_audio(
        source_video_path=processing_paths.downloaded_video_path,
        audio_no_video_path=processing_paths.audio_no_video_path,
        video_no_audio_path=processing_paths.video_no_audio_path
    )

    # Step 3: Generate CC
    generate_cc(processing_paths.audio_no_video_path, processing_paths.generated_cc_path)

    # Step 4: Translate CC
    translate_transcription(
        original_cc_path=processing_paths.generated_cc_path,
        target_language=target_language,
        translated_cc_save_path=processing_paths.translated_cc_path
    )

    # Step 5: Renarrate
    # select voice
    generate_narration(
        translated_cc_path=processing_paths.translated_cc_path,
        generated_narration_save_path=processing_paths.generated_narration_path,
        voice=voice
    )

    # Step 6: Merge
    merge_video_audio(
        video_no_audio_path=processing_paths.video_no_audio_path,
        generated_narration_path=processing_paths.generated_narration_path,
        final_video_save_path=processing_paths.final_video_path
    )

    return processing_paths

if __name__ == "__main__":
    # Example usage
    video_url = "https://www.youtube.com/watch?v=tqPQB5sleHY"
    target_language = select_language_by_name("Polish")
    gemini_voice = select_gemini_voice("Orus")
    elevenlabs_voice = select_elevenlabs_voice("Daniel")
    paths = run_pipeline(video_url, target_language, elevenlabs_voice)
    convert_video(paths.downloaded_video_path, "mp4")
    convert_video(paths.final_video_path, "mp4") 