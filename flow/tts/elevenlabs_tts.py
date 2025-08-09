from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from typing import List, Optional
from flow.models.voices import ElevenLabsVoice
import os

load_dotenv()
elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)




def tts_bytes_for_text(text: str, voice:ElevenLabsVoice, target_secs: Optional[float]) -> bytes:
    """
    Call ElevenAPI TTS for a single cue of text and return PCM bytes.
    """

    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=voice.id,
        model_id="eleven_turbo_v2_5",
        output_format="pcm_24000",
    )
    # The SDK yields chunks; collect them into a single bytes object. (docs show iteration)
    # https://elevenlabs.io/docs/cookbooks/text-to-speech/streaming
    buf = bytearray()
    for chunk in audio:
        if chunk:
            # Some versions yield memoryview objects; ensure bytes.
            buf.extend(bytes(chunk))
    data = bytes(buf)
    if not data:
        raise RuntimeError("ElevenLabs TTS returned no audio.")
    return data