# Ethernet-APL, explained — and how it differs from CAN bus

An animated, narrated engineering explainer (≈ 17 min, 1080p60) on **Ethernet-APL**
(Advanced Physical Layer), using **CAN bus** as the reference point throughout.
Written for an engineer with a mechanical background and working knowledge of
controls, signals and electronics.

**Video:** `output/Ethernet-APL_vs_CAN-bus.mp4` (soft English subtitles and chapter
markers are embedded; a separate `.srt` is alongside).

## What it covers

| # | Chapter | Highlights |
|---|---|---|
| — | Intro | A radar level transmitter knows a lot but reports one number over 4–20 mA |
| 01 | The last kilometer | 4–20 mA live zero, HART FSK riding on the loop current, fieldbus, the four walls that kept Ethernet out of the field |
| 02 | One new layer | APL replaces only the physical layer; 10BASE-T1L + port profiles (IEC TS 63444) + 2-WISE (IEC TS 60079-47) |
| 03 | Our reference: CAN bus | Dominant/recessive, the transceiver output stage, differential reception (ΔP-transmitter analogy), bitwise arbitration, frame anatomy, bit stuffing, why bit rate × length ≈ constant |
| 04 | Inside Ethernet-APL | Point-to-point trunk-and-spur topology, full duplex on one pair with echo cancellation, PAM-3 / 4B3T at 7.5 MBd, spectrum vs. cable loss and equalised eye diagrams, power and data on the same pair |
| 05 | Intrinsic safety | Fire triangle, zones, spark energy vs. minimum ignition energy, ia/ib/ic, entity calculation vs. 2-WISE port profiles |
| 06 | Head to head | Bandwidth per device, rate–distance chart, frames and addressing, 1 MB transfer times, summary table, where each technology belongs |

All facts and figures are sourced in [`docs/research_notes.md`](docs/research_notes.md);
the full narration is in [`docs/transcript.md`](docs/transcript.md) and the plan in
[`docs/storyboard.md`](docs/storyboard.md).

## How it is made

* **Animation:** [Manim Community](https://www.manim.community/) 0.22 (Cairo renderer), one
  Python scene per section in `video/scenes/`, shared building blocks in `video/apl/`.
* **Narration:** [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) neural TTS (ONNX,
  voice `af_heart`), synthesised sentence by sentence. `video/apl/narration.py` keeps
  animations in sync with the voice (`with self.voice("..."): ...`, `{tag}` markers inside the
  text), applies a pronunciation dictionary for acronyms, and logs subtitle cues.
* **Music:** a procedural ambient pad with convolution reverb, sidechain-ducked under the voice
  (`video/audio/music.py`); loudness normalised to −16 LUFS.
* **Icons:** [Tabler Icons](https://tabler.io/icons) (MIT, see `assets/icons/LICENSE-tabler-icons.txt`).

## Rebuild

Requirements: Python 3.11+, `manim`, `kokoro-onnx`, `soundfile`, `scipy`, a LaTeX
installation with `dvisvgm` (packages: `cmbright`, `siunitx`), `ffmpeg`, and the Kokoro model
files in `build/models/` (`kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub
release `model-files-v1.0`).

```bash
cd video
python3 build.py all -q h -j 4      # render all scenes at 1080p60 and assemble
python3 build.py all -q l -j 4      # quick 480p15 preview
python3 build.py assemble -q h --no-music   # voice-only mix
```

Outputs go to `output/`; intermediate renders, TTS cache and logs to `build/` (git-ignored).
