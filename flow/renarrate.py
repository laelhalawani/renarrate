import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import wave
from settings import STORAGE_DIR

load_dotenv()
client = genai.Client()

def wave_file(
    filename: str,
    pcm: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2
) -> None:
    """
    Saves PCM audio data to a WAV file with the specified parameters.
    Args:
        filename (str): Path to the output WAV file.
        pcm (bytes): PCM audio data.
        channels (int): Number of audio channels.
        rate (int): Sample rate in Hz.
        sample_width (int): Sample width in bytes.
    Returns:
        None
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_narration(
    translated_cc_path: str,
    generated_narration_save_path: str,
    voice_name: str = "Kore"
) -> None:
    """
    Generates narration audio from a translated closed caption (CC) file and saves it as a WAV file.
    Args:
        translated_cc_path (str): Path to the translated CC file.
        generated_narration_save_path (str): Path where the generated narration WAV file will be saved.
        voice_name (str, optional): Name of the voice to use for narration. Defaults to "Kore".
    Returns:
        None
    """
    with open(translated_cc_path, "r", encoding="utf-8") as f:
        translated_text = f.read()
    print(f"Generating narration from translated CC: {translated_cc_path} using voice: {voice_name}")
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=translated_text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        )
    )
    candidates = getattr(response, "candidates", None)
    if candidates and len(candidates) > 0 and getattr(candidates[0], "content", None):
        parts = getattr(candidates[0].content, "parts", None)
        if parts and len(parts) > 0:
            inline_data = getattr(parts[0], "inline_data", None)
            if inline_data is not None and hasattr(inline_data, "data"):
                new_audio_data = inline_data.data
                print(f"Saving generated narration to: {generated_narration_save_path}")
                wave_file(generated_narration_save_path, new_audio_data)
                print("Narration generation complete.")
                return
    print("Failed to generate narration.")
