import os
from dotenv import load_dotenv
from google import genai
from .utils.srt_utils import clean_srt_text
load_dotenv()
client = genai.Client()

STRICT_SRT_INSTRUCTION = (
    "Generate CC for the following audio using the SRT format. Count numbers from 1 and use timestamps in format HH:MM:SS:mmm or MM:SS:mmm consistently across the SRT file. Output only the SRT file. \n"
)

def generate_cc(audio_path: str, srt_save_path: str) -> None:
    """
    Generates closed captions (CC) in SRT format for the given audio file and saves them to the specified path.
    Args:
        audio_path (str): Path to the audio file to process.
        srt_save_path (str): Path where the generated SRT file will be saved.
    Returns:
        None
    """
    print(f"Uploading audio file: {audio_path}")
    uploaded_audio = client.files.upload(file=audio_path)
    print("Requesting CC generation from Gemini model...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[STRICT_SRT_INSTRUCTION, uploaded_audio],
    )
    original_transcription = clean_srt_text(response.text) if response.text else ""
    print(f"Saving generated CC to: {srt_save_path}")
    with open(srt_save_path, "w", encoding="utf-8") as f:
        f.write(original_transcription if original_transcription is not None else "")
    print("CC generation complete.")
