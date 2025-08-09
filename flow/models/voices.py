from dataclasses import dataclass
from typing import Optional, Literal

Provider = Literal["gemini", "elevenlabs"]


@dataclass
class Voice:
    """
    Base voice descriptor. Subclasses add provider-specific fields.
    """
    provider: Provider
    name: str # Name of the voice.
    id: str  # For ElevenLabs, this is the voice ID; for Gemini, it's the voice name.
    description: Optional[str] = None


@dataclass
class GeminiVoice(Voice):
    """
    Voice descriptor for Gemini TTS.
    """
    

    def __init__(
        self,
        name: str,
        id: str,
        description: Optional[str] = None,
    ):
        super().__init__(provider="gemini", name=name, id=id, description=description)
        self.name = name
        self.id = id  # For Gemini, this is the voice name.
        self.description = description

@dataclass
class ElevenLabsVoice(Voice):
    """
    Voice descriptor for ElevenLabs TTS.
    """
    def __init__(
        self,
        name: str,
        id: str,
        description: Optional[str] = None,
    ):
        super().__init__(provider="elevenlabs", name=name, id=id, description=description)
        self.name = name
        self.id = id  # For ElevenLabs, this is the voice ID.
        self.description = description
