import re
from dataclasses import dataclass
from typing import List

# Accept standard "HH:MM:SS,mmm" and your colon variant "HH:MM:SS:mmm",
# plus common shortened forms without hours: "MM:SS,mmm" or "MM:SS:mmm",
# and even bare "SS,mmm" in case the model emits that.
_FULL_RE = re.compile(
    r"^(?P<h>\d{1,2}):(?P<m>\d{1,2}):(?P<s>\d{1,2})[,.:](?P<ms>\d{3})$"
)
_MMSS_RE = re.compile(
    r"^(?P<m>\d{1,2}):(?P<s>\d{1,2})[,.:](?P<ms>\d{3})$"
)
_SS_RE = re.compile(
    r"^(?P<s>\d{1,2})[,.:](?P<ms>\d{3})$"
)

def _ts_to_seconds(ts: str) -> float:
    """
    Parse SRT-like timestamps. Supports:
      - HH:MM:SS,mmm or HH:MM:SS:mmm
      - MM:SS,mmm or MM:SS:mmm
      - SS,mmm or SS:mmm
    Returns total seconds as float.
    """
    ts = ts.strip()

    m = _FULL_RE.match(ts)
    if m:
        h = int(m.group("h"))
        mi = int(m.group("m"))
        s = int(m.group("s"))
        ms = int(m.group("ms"))
        return h * 3600 + mi * 60 + s + ms / 1000.0

    m = _MMSS_RE.match(ts)
    if m:
        mi = int(m.group("m"))
        s = int(m.group("s"))
        ms = int(m.group("ms"))
        return mi * 60 + s + ms / 1000.0

    m = _SS_RE.match(ts)
    if m:
        s = int(m.group("s"))
        ms = int(m.group("ms"))
        return s + ms / 1000.0

    raise ValueError(f"Invalid SRT timestamp: {ts!r}")

@dataclass
class SRTCue:
    index: int
    start: float
    end: float
    text: str

def parse_srt(srt_text: str) -> List[SRTCue]:
    """
    Minimal SRT parser for well-formed blocks.
    Accepts timestamps in HH:MM:SS,mmm / HH:MM:SS:mmm and shorter variants.
    """
    # Normalize line endings and trim
    s = srt_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not s:
        return []

    # Blocks are separated by blank lines
    blocks = re.split(r"\n\s*\n", s)
    cues: List[SRTCue] = []

    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip() != ""]
        if len(lines) < 3:
            continue

        # 1) cue index
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        # 2) timing line
        times_line = lines[1]
        if "-->" not in times_line:
            continue
        start_str, end_str = [p.strip() for p in times_line.split("-->")]

        # 3) text
        text = "\n".join(lines[2:])

        # parse timestamps
        start = _ts_to_seconds(start_str)
        end = _ts_to_seconds(end_str)
        cues.append(SRTCue(index=index, start=start, end=end, text=text))

    return cues

def clean_srt_text(text: str) -> str:
    """
    Cleans up SRT text by removing leading/trailing whitespace and ensuring
    no empty lines between cues. As well as removing markdown's triple backtick lines.
    """
    # Remove markdown code block lines
    text = re.sub(r"^```srt\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```$", "", text, flags=re.MULTILINE)
    return text.strip()