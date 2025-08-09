import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

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
        model="gemini-2.5-flash", contents=["Generate CC for the following audio using the SRT format.", uploaded_audio]
    )
    original_transcription = response.text
    print(f"Saving generated CC to: {srt_save_path}")
    with open(srt_save_path, "w", encoding="utf-8") as f:
        f.write(original_transcription if original_transcription is not None else "")
    print("CC generation complete.")
