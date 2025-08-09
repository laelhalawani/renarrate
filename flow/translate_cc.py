import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

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
        model="gemini-2.5-flash", contents=[f"Translate the following text to {target_language}: {original_transcription}"]
    )
    translated_text = response.text
    print(f"Saving translated CC to: {translated_cc_save_path}")
    with open(translated_cc_save_path, "w", encoding="utf-8") as f:
        f.write(translated_text if translated_text is not None else "")
    print("Translation complete.")
