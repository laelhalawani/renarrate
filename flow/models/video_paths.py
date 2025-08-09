from dataclasses import dataclass, field
from typing import Optional
import os
import uuid
from settings import STORAGE_DIR

@dataclass
class VideoProcessingPaths:
    """
    Helper class for managing all file paths used in video processing pipeline.
    Paths are constructed as base_dir/request_id/filename.ext.
    If request_id is not provided, a new UUID is generated.
    """
    base_dir: str
    request_id: Optional[str] = None
    create: bool = True

    def __post_init__(self):
        """
        Ensures request_id is set (generates one if not provided).
        Optionally creates the directory for the request if 'create' is True.
        """
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.create:
            os.makedirs(os.path.join(self.base_dir, str(self.request_id)), exist_ok=True)

    def _path(self, filename: str) -> str:
        """
        Constructs a full path for a given filename using base_dir and request_id.
        """
        assert self.request_id is not None
        return os.path.join(self.base_dir, self.request_id, filename)

    @property
    def downloaded_video_path(self):
        return self._path("original.mkv")

    @property
    def video_no_audio_path(self):
        return self._path("video_noaudio.mkv")

    @property
    def audio_no_video_path(self):
        return self._path("audio.wav")

    @property
    def generated_cc_path(self):
        return self._path("original_transcription.srt")

    @property
    def translated_cc_path(self):
        # Now an SRT, not a TXT, so we can preserve cue timings end-to-end.
        return self._path("translated_text.srt")

    @property
    def generated_narration_path(self):
        return self._path("new_audio.wav")

    @property
    def final_video_path(self):
        return self._path("final_video.mkv")

    @property
    def video_info_path(self):
        """
        Returns the path to the video info JSON file.
        """
        return self._path("info.json")
