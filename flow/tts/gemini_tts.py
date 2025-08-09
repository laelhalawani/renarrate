
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Optional
from flow.models.voices import GeminiVoice

load_dotenv()
client = genai.Client()

def tts_bytes_for_text(text: str, voice:GeminiVoice, target_secs: Optional[float]) -> bytes:
    """
    Call Gemini TTS for a single cue of text and return PCM bytes.
    Provide a gentle natural-language pacing hint targeting ~target_secs.
    """
    if target_secs and target_secs > 0:
        guidance = (
            f"Read this text fairly fast, but clearly and naturally, aiming for about {target_secs:.2f} seconds of audio. "
        )
    else:
        guidance = "Read this text fairly fast, but clearly and naturally."

    prompt = f"{guidance}\n\n{text}"

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice.id
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
                return inline_data.data
    raise RuntimeError("Failed to synthesize TTS for a cue.")