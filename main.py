from flow.tts.gemini_voices import select_voice_by_name as select_gemini_voice
from flow.tts.elevenlabs_voices import select_voice_by_name as select_elevenlabs_voice
from flow.utils.convert import convert_video
from flow.utils.languages import select_language_by_name
from pipeline import run_pipeline

if __name__ == "__main__":
    # Example usage
    video_url = "https://www.youtube.com/watch?v=imiAXNnzkAc"
    target_language = select_language_by_name("Polish")
    # gemini-tts is in preview mode, it has really limited rates on Tier 1 only 10 RPM, 
    # the system will be fine (will retry with 30sec delay for each fragment generation up to 5 times, but will be really slow)
    # uncomment below if you want to try
    # gemini_voice = select_gemini_voice("Orus") 
    elevenlabs_voice = select_elevenlabs_voice("Daniel")
    paths = run_pipeline(video_url, target_language, elevenlabs_voice)
    convert_video(paths.downloaded_video_path, "mp4")
    convert_video(paths.final_video_path, "mp4") 