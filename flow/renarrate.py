import os
import math
from dotenv import load_dotenv
from google import genai
from google.genai import types
import wave
from typing import List, Optional
import ffmpeg  # pip install ffmpeg-python
from moviepy import AudioFileClip, CompositeAudioClip
import time
from flow.utils.srt_utils import parse_srt
from flow.tts.gemini_tts import tts_bytes_for_text as gemini_tts_bytes_for_text
from flow.tts.elevenlabs_tts import tts_bytes_for_text as elevenlabs_tts_bytes_for_text
from flow.models.voices import GeminiVoice, Voice, ElevenLabsVoice

load_dotenv()
client = genai.Client()

RETRIES = 10
RETRY_DELAY_S = 30


def wave_file(
    filename: str,
    pcm: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2
) -> None:
    """
    Save PCM audio data to a WAV file.
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def _decompose_atempo_factor(f: float) -> List[float]:
    """
    Decompose a tempo factor into a product of factors inside [0.5, 2.0] so we can
    chain 'atempo' filters when necessary.
    """
    if f <= 0 or math.isinf(f) or math.isnan(f):
        raise ValueError(f"Invalid atempo factor: {f}")

    factors: List[float] = []
    while f > 2.0:
        factors.append(2.0)
        f /= 2.0
    while f < 0.5:
        factors.append(0.5)
        f /= 0.5  # equivalent to f *= 2
    if not (0.98 <= f <= 1.02):
        factors.append(f)
    return factors

def _time_stretch_wav_to_duration(
    in_path: str, out_path: str, target_secs: float, sample_rate: int = 24000
) -> None:
    """
    Pitch-preserving time-stretch to a specific duration using FFmpeg 'atempo'.
    """
    if target_secs <= 0:
        raise ValueError("target_secs must be > 0")

    probe = ffmpeg.probe(in_path)
    streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if not streams:
        raise ValueError(f"No audio stream found in {in_path}")
    # Duration can be missing on some PCM WAVs; fall back to format duration if needed.
    src_dur_str = streams[0].get("duration")
    if src_dur_str is None:
        src_dur_str = probe.get("format", {}).get("duration")
    if src_dur_str is None:
        raise ValueError("Unable to determine source duration for tempo adjustment.")
    src_dur = float(src_dur_str)

    # Tempo factor: >1.0 -> faster (shorter); <1.0 -> slower (longer)
    atempo = src_dur / target_secs
    chain = _decompose_atempo_factor(atempo)

    stream = ffmpeg.input(in_path)
    # ✅ Correct usage: chain filters on the stream (module-level ffmpeg.audio does not exist)
    for f in chain:
        stream = stream.filter("atempo", f)  # e.g., .filter('atempo', 2.0)
    out = ffmpeg.output(stream, out_path, acodec="pcm_s16le", ac=1, ar=sample_rate).overwrite_output()
    out.run(quiet=True)

def generate_narration(
    translated_cc_path: str,
    generated_narration_save_path: str,
    voice: Voice,
    audio_fps: int = 24000,
    max_pct_deviation: float = 0.06,  # 6% tolerance before DSP
    min_abs_deviation: float = 0.06   # ~60 ms absolute tolerance
) -> None:
    """
    Generate narration aligned to SRT timings by synthesizing one clip per cue.
    1) Prompt TTS with a per-cue pace hint ("~X seconds").
    2) If still off, time-stretch (pitch-preserving) to the cue window using FFmpeg 'atempo'.
    3) Place each clip at cue start; trim overrun with 'subclipped' to avoid overlap.
    """
    with open(translated_cc_path, "r", encoding="utf-8") as f:
        translated_srt = f.read()
    cues = parse_srt(translated_srt)
    if not cues:
        raise ValueError("No SRT cues parsed from translated captions.")

    tmp_dir = os.path.join(os.path.dirname(generated_narration_save_path), "tts_fragments")
    os.makedirs(tmp_dir, exist_ok=True)

    fragment_paths: List[str] = []
    for cue in cues:
        text_for_tts = cue.text.replace("\n", " ").strip()
        if not text_for_tts:
            continue
        window = max(0.0, cue.end - cue.start)
        target_secs = max(window - 0.08, 0.15) if window > 0 else None

        attempts = 0
        while attempts < RETRIES:

            try:
                if isinstance(voice, GeminiVoice):
                    tts_bytes = gemini_tts_bytes_for_text(text_for_tts, voice, target_secs)
                    voice_name = voice.name
                elif isinstance(voice, ElevenLabsVoice):
                    tts_bytes = elevenlabs_tts_bytes_for_text(text_for_tts, voice, target_secs)
                    voice_name = voice.name
                print(f"TTS cue {cue.index} [{cue.start:.3f}–{cue.end:.3f}s], target≈{(target_secs or 0):.2f}s, voice={voice_name}")
                pcm_bytes = tts_bytes
            except Exception as e:
                attempts += 1
                print(f"  ! TTS failed for cue {cue.index} (attempt {attempts}/{RETRIES}): {e}")
                if attempts >= RETRIES:
                    raise RuntimeError(f"TTS failed after {RETRIES} attempts for cue {cue.index}.")
                print(f"  Retrying in {RETRY_DELAY_S} seconds...")
                time.sleep(RETRY_DELAY_S)
                continue

        frag_path = os.path.join(tmp_dir, f"cue_{cue.index:05d}.wav")
        wave_file(frag_path, pcm_bytes, channels=1, rate=audio_fps, sample_width=2)

        # Tempo-fit to window if outside tolerances
        if window > 0:
            try:
                with AudioFileClip(frag_path) as m:
                    dur = float(m.duration)
                deviation = abs(dur - window)
                if (deviation > min_abs_deviation) and (deviation / max(window, 1e-6) > max_pct_deviation):
                    adjusted = os.path.join(tmp_dir, f"cue_{cue.index:05d}_fit.wav")
                    print(f"  - Adjusting tempo with ffmpeg atempo: current {dur:.3f}s -> target {window:.3f}s")
                    _time_stretch_wav_to_duration(frag_path, adjusted, window, sample_rate=audio_fps)
                    os.replace(adjusted, frag_path)
            except Exception as e:
                print(f"  ! Tempo adjustment failed for cue {cue.index}: {e}")

        fragment_paths.append(frag_path)

    # Composite: place each fragment at its start time, trim any overrun
    print("Compositing per-cue audio onto timeline...")
    audio_clips = []
    idx_to_path = {}
    for p in fragment_paths:
        try:
            name = os.path.basename(p)
            idx = int(name.split('_')[1].split('.')[0])
            idx_to_path[idx] = p
        except Exception:
            pass

    for cue in cues:
        p = idx_to_path.get(cue.index)
        if not p:
            continue
        clip = AudioFileClip(p)
        window = max(0.0, cue.end - cue.start)
        if window > 0 and clip.duration > window:
            clip = clip.subclipped(0, window)
        clip = clip.with_start(cue.start)
        audio_clips.append(clip)

    if not audio_clips:
        raise ValueError("No audio clips generated from TTS.")

    composite = CompositeAudioClip(audio_clips)
    print(f"Writing composite narration to: {generated_narration_save_path}")
    composite.write_audiofile(generated_narration_save_path, fps=audio_fps, nbytes=2)

    # Cleanup
    composite.close()
    for c in audio_clips:
        try:
            c.close()
        except Exception:
            pass

    print("Narration generation complete.")
