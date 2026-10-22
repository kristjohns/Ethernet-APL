"""Narration engine: Kokoro neural TTS, scene synchronisation, subtitle cues.

Usage inside a scene that mixes in :class:`NarratedScene`::

    with self.voice("First sentence. {walls}Four walls stood in the way.") as v:
        self.play(FadeIn(title))
        v.wait_until("walls")          # block until that sentence starts
        self.play(Create(walls), run_time=v.until_end())

* Narration is synthesised one sentence at a time, so the start of every
  sentence is known exactly.  ``{tag}`` markers name a moment; a marker
  inside a sentence is placed proportionally to the spoken text before it.
* Audio is cached by content hash in ``build/tts``; editing one sentence only
  re-synthesises that sentence.
* Every sentence is logged as a subtitle cue in ``build/cues/<Scene>.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from .style import ROOT

BUILD = ROOT / "build"
TTS_CACHE = BUILD / "tts"
CUES_DIR = BUILD / "cues"
MODELS = Path(os.environ.get("APL_TTS_MODELS", BUILD / "models"))

VOICE = os.environ.get("APL_VOICE", "af_heart")
SPEED = float(os.environ.get("APL_SPEED", "1.0"))
SR = 24000
SENTENCE_GAP = 0.42  # pause between sentences inside one voice block [s]

_NUM = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _two(n: int) -> str:
    if n < 20:
        return _NUM[n]
    t, u = divmod(n, 10)
    return _TENS[t] + ("" if u == 0 else "-" + _NUM[u])


def _year(y: int) -> str:
    """1858 -> 'eighteen fifty-eight', 1907 -> 'nineteen oh-seven', 2019 -> 'twenty nineteen'."""
    hi, lo = divmod(y, 100)
    if y in (2000,):
        return "two thousand"
    if 2001 <= y <= 2009:
        return "two thousand " + _NUM[lo]
    if lo == 0:
        return _two(hi) + " hundred"
    return _two(hi) + " " + (("oh-" + _NUM[lo]) if lo < 10 else _two(lo))


def _decade(y: int) -> str:
    """1880 -> 'eighteen-eighties'."""
    hi, lo = divmod(y, 100)
    word = _two(lo)
    word = word[:-1] + "ies" if word.endswith("y") else word + "s"
    return _two(hi) + "-" + word


# Display text -> what the TTS should say.  Checked against the espeak-ng
# phonemes Kokoro produces (e.g. "APL" alone is read as "apple").
SPEECH_RULES: list[tuple[str, str]] = [
    (r"Ethernet-APL", "Ethernet A-P-L"),
    (r"\bAPL\b", "A-P-L"),
    (r"100BASE-TX", "one hundred base T X"),
    (r"10BASE-T1L", "ten base T one L"),
    (r"10BASE-T1S", "ten base T one S"),
    (r"IEEE 802\.3cg", "I triple E eight oh two dot three C G"),
    (r"IEC TS 63444", "I-E-C T-S six three four four four"),
    (r"IEC TS 60079-47", "I-E-C T-S six oh oh seven nine, part forty-seven"),
    (r"\bIEC\b", "I-E-C"),
    (r"EtherNet/IP", "Ethernet I-P"),
    (r"HART-IP", "HART I-P"),
    (r"OPC UA", "O-P-C U-A"),
    (r"\bODVA\b", "O-D-V-A"),
    (r"PROFIBUS PA", "PROFIBUS P-A"),
    (r"Modbus TCP", "Modbus T-C-P"),
    (r"\bTCP\b", "T-C-P"),
    (r"\bUDP\b", "U-D-P"),
    (r"\bIP\b", "I-P"),
    (r"MAC address", "mac address"),
    (r"\bCRC\b", "C-R-C"),
    (r"\bCAN FD\b", "CAN F-D"),
    (r"\bCAN XL\b", "CAN X-L"),
    (r"\bH1\b", "H one"),
    (r"4B3T", "four B three T"),
    (r"2-WISE", "two-wise"),
    (r"\bEx ia\b", "ex i-A"),
    (r"'ia'", "i-A"),
    (r"\bZone 0\b", "Zone zero"),
    (r"\bZone 1\b", "Zone one"),
    (r"\bZone 2\b", "Zone two"),
    (r"\bISDN\b", "I-S-D-N"),
    (r"Joukowsky", "Zhukovsky"),
    (r"d'Alembert", "dah-lahm-bair"),
    (r"10BASE5", "ten base five"),
    (r"\bmu\b", "mew"),
    (r"\bXOR\b", "exclusive-or"),
    (r"\bFIR\b", "F-I-R"),
    (r"\bFFE\b", "F-F-E"),
    (r"\bDFE\b", "D-F-E"),
    (r"\bADC\b", "A-D-C"),
    (r"\bDAC\b", "D-A-C"),
    (r"\b(1[0-9])-gauge\b", lambda m: _NUM[int(m.group(1))] + "-gauge"),
    (r"\b(1[7-9]\d0)s\b", lambda m: _decade(int(m.group(1)))),
    (r"\b(1[7-9]\d\d|20[0-2]\d)\b(?![,.]\d)(?!\s?(?:m\b|meters|bytes|bits|km|V\b|volts|W\b|watts|Ω|ohms))", lambda m: _year(int(m.group(1)))),
    (r"\b1,200\b", "twelve hundred"),
    (r"\b2,200\b", "twenty-two hundred"),
    (r"4–20 mA", "four to twenty milliamp"),
    (r"(\d)\s?Mbit/s", r"\1 megabits per second"),
    (r"(\d)\s?kbit/s", r"\1 kilobits per second"),
    (r"(\d)\s?MBd", r"\1 megabaud"),
    (r"(\d)\s?MHz", r"\1 megahertz"),
    (r"(\d)\s?kHz", r"\1 kilohertz"),
    (r"(\d)\s?Vpp", r"\1 volts peak-to-peak"),
    (r"(\d)\s?µJ", r"\1 microjoules"),
    (r"(\d)\s?dB\b", r"\1 decibels"),
    (r"—", ", "),
    (r"–", " to "),
]


def to_speech(text: str) -> str:
    s = text
    for pat, rep in SPEECH_RULES:
        s = re.sub(pat, rep, s)
    return " ".join(s.split())


_TAG = re.compile(r"\{(\w+)\}")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\{A-Z0-9'\"“(])")


def split_sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    return [p for p in _SENT_SPLIT.split(text) if _TAG.sub("", p).strip()]


# ---------------------------------------------------------------- synthesis
_engine = None


def _kokoro():
    global _engine
    if _engine is None:
        from kokoro_onnx import Kokoro

        _engine = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
    return _engine


def synth(speech: str) -> np.ndarray:
    """Synthesise one sentence (cached)."""
    TTS_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{VOICE}|{SPEED}|{speech}".encode()).hexdigest()[:20]
    path = TTS_CACHE / f"{key}.wav"
    if not path.exists():
        audio, sr = _kokoro().create(speech, voice=VOICE, speed=SPEED, lang="en-us")
        assert sr == SR
        sf.write(path, audio, sr, subtype="PCM_16")
    audio, _ = sf.read(path, dtype="float32")
    return audio


@dataclass
class Sentence:
    text: str
    speech: str
    start: float
    end: float


@dataclass
class Narration:
    text: str
    sentences: list[Sentence] = field(default_factory=list)
    tags: dict[str, float] = field(default_factory=dict)
    duration: float = 0.0
    wav: Path | None = None

    @classmethod
    def build(cls, text: str) -> "Narration":
        n = cls(text)
        t = 0.0
        pieces: list[np.ndarray] = []
        gap = np.zeros(int(SENTENCE_GAP * SR), dtype=np.float32)
        for i, raw in enumerate(split_sentences(text)):
            # segments between tags, to place mid-sentence tags proportionally
            segs = _TAG.split(raw)  # [text, tag, text, tag, text...]
            clean = "".join(segs[0::2]).strip()
            speech = to_speech(clean)
            audio = synth(speech)
            dur = len(audio) / SR
            if i:
                pieces.append(gap)
                t += SENTENCE_GAP
            total = max(len(speech), 1)
            consumed = ""
            for j in range(1, len(segs), 2):
                consumed += segs[j - 1]
                frac = len(to_speech(consumed.strip())) / total if consumed.strip() else 0.0
                n.tags[segs[j]] = t + dur * min(frac, 1.0)
            n.sentences.append(Sentence(clean, speech, t, t + dur))
            pieces.append(audio)
            t += dur
        n.duration = t
        joined = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
        key = hashlib.sha1(("|".join(s.speech for s in n.sentences) + f"|{SENTENCE_GAP}|{VOICE}|{SPEED}").encode()).hexdigest()[:20]
        n.wav = TTS_CACHE / f"block_{key}.wav"
        if not n.wav.exists():
            sf.write(n.wav, joined, SR, subtype="PCM_16")
        return n


# ---------------------------------------------------------------- scene sync
class VoiceBlock:
    def __init__(self, scene, narration: Narration):
        self.scene = scene
        self.n = narration
        self.t0 = scene.time

    @property
    def duration(self) -> float:
        return self.n.duration

    def elapsed(self) -> float:
        return self.scene.time - self.t0

    def until_end(self, minimum: float = 0.3) -> float:
        return max(minimum, self.n.duration - self.elapsed())

    def until(self, tag: str, minimum: float = 0.3) -> float:
        """Seconds from now until ``tag`` (at least ``minimum``) — handy as a run_time."""
        return max(minimum, self.n.tags[tag] - self.elapsed())

    def wait_until(self, tag: str) -> None:
        dt = self.n.tags[tag] - self.elapsed()
        if dt > 1 / 120:
            self.scene.wait(dt)

    def wait_end(self, pad: float = 0.0) -> None:
        dt = self.n.duration + pad - self.elapsed()
        if dt > 1 / 120:
            self.scene.wait(dt)


class NarratedScene:
    """Mixin: put it first in the bases, e.g. ``class S(NarratedScene, MovingCameraScene)``."""

    def setup(self):
        super().setup()
        self._cues = []
        self._chapters = []

    @contextmanager
    def voice(self, text: str, pad: float = 0.35, wait: bool = True):
        n = Narration.build(text)
        vb = VoiceBlock(self, n)
        self.add_sound(str(n.wav))
        for s in n.sentences:
            self._cues.append({"start": vb.t0 + s.start, "end": vb.t0 + s.end, "text": s.text})
        yield vb
        if wait:
            vb.wait_end(pad)

    def tear_down(self):
        super().tear_down()
        CUES_DIR.mkdir(parents=True, exist_ok=True)
        out = {"scene": type(self).__name__, "duration": self.time, "cues": self._cues, "chapters": self._chapters}
        (CUES_DIR / f"{type(self).__name__}.json").write_text(json.dumps(out, indent=1))
