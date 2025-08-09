import os
from dotenv import load_dotenv
from google import genai
from .utils.srt_utils import clean_srt_text
load_dotenv()
client = genai.Client()

TRANSLATE_SRT_INSTRUCTION = (
    "Translate the following SRT subtitles to the {target_lang} language while preserving the exact numbers, timestamps and linebreaks.\n"
    "Subtitles to translate:\n```srt\n{subtitles}\n```"
)

def translate_transcription(
    original_cc_path: str,
    target_language: str,
    translated_cc_save_path: str
) -> None:
    """
    Translates a closed caption (CC) file to the specified target language and saves the result.
    Args:
        original_cc_path (str): Path to the original CC file.
        target_language (str): Language to translate the CC into.
        translated_cc_save_path (str): Path where the translated CC file will be saved.
    Returns:
        None
    """
    with open(original_cc_path, "r", encoding="utf-8") as f:
        original_transcription = f.read()
    print(f"Translating CC from {original_cc_path} to {target_language}...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[TRANSLATE_SRT_INSTRUCTION.format(target_lang=target_language, subtitles=original_transcription)],
    )
    translated_text = clean_srt_text(response.text) if response.text else ""
    print(f"Saving translated CC to: {translated_cc_save_path}")
    with open(translated_cc_save_path, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print("Translation complete.")
