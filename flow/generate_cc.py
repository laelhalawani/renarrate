import os
from dotenv import load_dotenv
from google import genai
from .utils.srt_utils import clean_srt_text, parse_srt
load_dotenv()
client = genai.Client()

CREATE_CC_SRT = (
    "Transcribe for the following audio using the SRT format, break the text down into logical sentences up to two lines per . Count cues from 1 and use timestamps in format HH:MM:SS,mmm or MM:SS,mmm consistently across the SRT file. Output only the SRT file. \n"
)

FIX_SRT_TIMESTAMP = (
    "In the following SRT file, please fix the timestamps to adhere exactly to the HH:MM:SS,mmm or MM:SS,mmm format. Preserve all the text, cues numbers and timestamps' timing as is, adjust only the formatting where needed. Output only the updated SRT file. SRT to fix timestamps formatting:\n```srt\n{srt_text}\n````\n"
)
FIXING_RETRIES = 5

def generate_cc(audio_path: str, srt_save_path: str) -> None:
    """
    Generates closed captions (CC) in SRT format for the given audio file and saves them to the specified path.
    Args:
        audio_path (str): Path to the audio file to process.
        srt_save_path (str): Path where the generated SRT file will be saved.
    Returns:
        None
    """
    print(f"Uploading audio file for Gemini transcription: {audio_path}")
    uploaded_audio = client.files.upload(file=audio_path)
    print("Requesting CC generation from Gemini model...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[CREATE_CC_SRT, uploaded_audio],
    )
    if response.text:
        print("CC generation response received.")
        original_transcription = clean_srt_text(response.text)
        original_transcription = validate_and_fix_srt(original_transcription)
        
    print(f"Saving generated CC to: {srt_save_path}")
    with open(srt_save_path, "w", encoding="utf-8") as f:
        f.write(original_transcription if original_transcription is not None else "")
    print("CC generation complete.")


def validate_and_fix_srt(srt_text: str) -> str:
    """
    Prompts Gemini to fix SRT timestamps in the provided text.
    Args:
        srt_text (str): The SRT text to fix.   
    Returns:
        str: The SRT text with fixed timestamps.
    """
    print("Validating SRT timestamps...")
    attempts = 0
    while attempts < FIXING_RETRIES:
        try:
            srt_cues_list = parse_srt(srt_text)
            if srt_cues_list:
                return srt_text
        except Exception as e:
            print(f"Error parsing SRT: {e}, trying to fix with Gemini...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                FIX_SRT_TIMESTAMP.format(srt_text=srt_text),
            ],
        )
        fixed_srt_text = response.text 
        if fixed_srt_text:
            try:
                srt_cues_list = parse_srt(fixed_srt_text)
                if srt_cues_list:
                    return fixed_srt_text
            except Exception as e:
                print(f"Error parsing SRT after Gemini fix: {e}")
        attempts += 1
        print(f"Retrying SRT timestamp fix ({attempts}/{FIXING_RETRIES})...")
    raise RuntimeError("Failed to fix SRT timestamps after multiple attempts.")
