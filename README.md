# Ethernet-APL, explained — and how it differs from CAN bus

![Poster](output/poster.jpg)

An animated, narrated engineering explainer (**17 min, 1080p60**) on **Ethernet-APL**
(Advanced Physical Layer), using **CAN bus** as the reference point throughout.
Written for an engineer with a mechanical background and working knowledge of
controls, signals and electronics.

**Video:** [`output/Ethernet-APL_vs_CAN-bus.mp4`](output/Ethernet-APL_vs_CAN-bus.mp4)

* chapter markers are embedded (skip between chapters in VLC, QuickTime, mpv …)
* soft English subtitles are embedded; a separate [`.srt`](output/Ethernet-APL_vs_CAN-bus.srt) is alongside
* two audio tracks: **Narration + music** (default) and **Narration only**

## Chapters

| Time | Chapter | Highlights |
|---|---|---|
| 00:00 | Intro | A radar level transmitter knows a lot but reports one number over 4–20 mA |
| 00:57 | 01 · The last kilometer | 4–20 mA live zero, HART FSK riding on the loop current, fieldbus, the four walls that kept Ethernet out of the field |
| 02:56 | 02 · One new layer | APL replaces only the physical layer; 10BASE-T1L + port profiles (IEC TS 63444) + 2-WISE (IEC TS 60079-47) |
| 04:20 | 03 · Our reference: CAN bus | Dominant/recessive and the transceiver output stage, differential reception (ΔP-transmitter analogy), bitwise arbitration, frame anatomy, bit stuffing, why bit rate × length ≈ constant, CAN FD |
| 08:07 | 04 · Inside Ethernet-APL | Point-to-point trunk-and-spur topology, full duplex on one pair with echo cancellation, PAM-3 / 4B3T at 7.5 MBd, spectrum vs. cable loss and equalised eye diagrams, power and data on the same pair |
| 12:26 | 05 · Intrinsic safety | Fire triangle, zones, spark energy vs. minimum ignition energy, ia/ib/ic, entity calculation vs. 2-WISE port profiles |
| 14:16 | 06 · Head to head | Bandwidth per device, rate–distance chart, frames and addressing, 1 MB transfer times, summary table, where each technology belongs |
| 16:19 | Summary | Party line vs. private line; from the sensor to the cloud |

All facts and figures are sourced in [`docs/research_notes.md`](docs/research_notes.md);
the full narration is in [`docs/transcript.md`](docs/transcript.md) and the plan in
[`docs/storyboard.md`](docs/storyboard.md).

Notes on simplifications: the 4B3T code table on screen is an illustrative DC-balanced
code (not the IEEE 802.3cg table); CAN length limits are typical values (sources quote
25–40 m at 1 Mbit/s); far-end signal amplitudes in the echo-cancellation animation are
exaggerated for visibility (labelled on screen); the intrinsic-safety chapter explains the
concept and is not design guidance.

## How it is made

* **Animation:** [Manim Community](https://www.manim.community/) 0.22 (Cairo renderer), one
  Python scene per section in `video/scenes/`, shared building blocks in `video/apl/`
  (palette and typography, devices, cables, circuit symbols, a perspective-projected 3D twisted
  pair, packet flows).
* **Narration:** [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) neural TTS (ONNX,
  voice `af_heart`), synthesised sentence by sentence. `video/apl/narration.py` keeps the
  animation in sync with the voice (`with self.voice("..."): ...` blocks and `{tag}` markers in
  the text), applies a pronunciation dictionary for acronyms and years, and logs subtitle cues.
* **Sound:** a procedural ambient pad with convolution reverb, sidechain-ducked under the voice,
  plus soft whooshes under chapter cards (`video/audio/music.py`); EBU R128 loudness
  normalisation to −16 LUFS.
* **Finishing:** a radial glow and faint dot grid blended in with *lighten* (lifts only the
  background, never the content), x264 encode, chapters and subtitles muxed by `video/build.py`.
* **Icons:** [Tabler Icons](https://tabler.io/icons) (MIT, see `assets/icons/LICENSE-tabler-icons.txt`).

## Rebuild

Requirements: Python 3.11+, `manim`, `kokoro-onnx`, `soundfile`, `scipy`, `pillow`, a LaTeX
installation with `dvisvgm` (packages `cmbright`, `siunitx`), `ffmpeg`, and the Kokoro model
files in `build/models/` (`kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub
release `model-files-v1.0`).

```bash
cd video
python3 build.py all -q l -j 4      # quick 480p15 preview (~6 min on 4 cores)
python3 build.py all -q h -j 4      # 1080p60 master (~45 min on 4 cores)
python3 build.py assemble -q h --no-music   # single-track, narration-only variant
```

Outputs go to `output/`; intermediate renders, TTS cache and logs to `build/` (git-ignored).
