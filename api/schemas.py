from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field

# Request models

TTSProvider = Literal["elevenlabs", "gemini"]


class RenarrateRequest(BaseModel):
    """
    Incoming job creation request for /renarrate.
    - yt_video_url: any public YouTube URL (yt-dlp will handle it)
    - target_language: free-form name like "Polish", "pl-PL", or "Polish (Poland)".
      We'll resolve it to your internal code via select_language_by_name.
    - tts_provider: defaults to elevenlabs; can be "gemini"
    - voice_name: optional provider-specific friendly name, e.g. "Daniel" (ElevenLabs) or "Orus" (Gemini)
    """
    yt_video_url: HttpUrl = Field(..., description="YouTube video URL")
    target_language: str = Field(..., description="Target language name (e.g., 'Polish')")
    tts_provider: TTSProvider = Field("elevenlabs", description="TTS provider to use")
    voice_name: Optional[str] = Field(None, description="Voice display name for the provider")


# Response models

class EnqueueResponse(BaseModel):
    job_id: str
    status: Literal["PENDING"] = "PENDING"


class StatusResponse(BaseModel):
    job: Dict[str, Any]
