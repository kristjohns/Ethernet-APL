# Ethernet-APL, a deep dive — and how it differs from CAN bus

![Poster](output/poster.jpg)

An animated, narrated engineering explainer (**48 min, 1080p60**) on **Ethernet-APL** (Advanced Physical
Layer), with **CAN bus** as the reference point throughout. It follows a single bit through the physical layer:
how it becomes a voltage, how that voltage travels down a kilometer of copper, and how the far end pulls it
back out of the noise. Along the way it covers the history behind each idea, from the 1858 Atlantic cable to
gigabit Ethernet.
Written for an engineer with a mechanical background and working knowledge of controls, signals and
electronics. Formulas are welcome; mechanical analogies are used wherever they carry real insight.

**Video (deep dive, 48 min):** stored as three parts, split at chapter boundaries, because GitHub limits single
files to 100 MB:
[part 1](output/parts/Ethernet-APL_deep-dive_part1.mp4) (intro to chapter 04),
[part 2](output/parts/Ethernet-APL_deep-dive_part2.mp4) (chapters 05–06: the wire, bits to symbols),
[part 3](output/parts/Ethernet-APL_deep-dive_part3.mp4) (chapters 07–11 and summary).
To join them into one file without re-encoding:

```bash
cd output/parts && printf "file '%s'\n" Ethernet-APL_deep-dive_part{1,2,3}.mp4 > list.txt \
  && ffmpeg -f concat -safe 0 -i list.txt -map 0 -c copy ../Ethernet-APL_deep-dive.mp4
```

The first, shorter version (17 min) is still here too: [`output/Ethernet-APL_vs_CAN-bus.mp4`](output/Ethernet-APL_vs_CAN-bus.mp4).

* chapter markers are embedded (skip between chapters in VLC, QuickTime, mpv …)
* soft English subtitles are embedded; a separate [`.srt`](output/Ethernet-APL_deep-dive.srt) is alongside
* two audio tracks: **Narration + music** (default) and **Narration only**

## Chapters

<!-- chapters:start -->
| Time | Chapter | Highlights |
|---|---|---|
| 00:00 | Intro | A radar level transmitter knows a lot but reports one number over 4–20 mA; the plan for the deep dive |
| 01:07 | 01 · The last kilometer | 4–20 mA live zero, HART FSK on the loop current, fieldbus, the four walls that kept Ethernet out of the field |
| 03:05 | 02 · One new layer | APL replaces only the physical layer: 10BASE-T1L + port profiles (IEC TS 63444) + 2-WISE (IEC TS 60079-47) |
| 04:29 | 03 · Our reference: CAN bus | Dominant/recessive, differential reception, bitwise arbitration, frame anatomy, bit rate × length ≈ constant, bit timing with time quanta, hard sync, resynchronisation and bit stuffing |
| 09:29 | 04 · From coax to one pair | Metcalfe's 1973 coax “ether”, CSMA/CD and the 64-byte slot time (CAN's round trip, paid per frame), switches and full duplex, fifty years of Ethernet PHYs; APL's trunk-and-spur topology |
| 12:42 | 05 · The wire is a waveguide | The 1858 Atlantic cable and Kelvin's law of squares (Fourier's heat equation), Heaviside's telegrapher's equations → the wave equation, mass–spring chain ≡ LC ladder, c = 1/√(L′C′), Z₀ = √(L′/C′), water hammer, reflections, skin effect (δ = 34 µm at 3.75 MHz), cable loss, intersymbol interference, why twisting works |
| 22:36 | 06 · From bits to symbols | Nyquist, Hartley and Shannon; Manchester vs PAM-2/3/4 at 10 Mbit/s; 4B3T and running disparity; baseline wander; the 33-bit scrambler (period ≈ 14 min); the complete transmitter |
| 29:17 | 07 · Two directions, one pair | Superposition on a linear line, the telephone hybrid, the transceiver hybrid with replica network, a 50 dB echo budget, the LMS echo canceller converging, why the two scramblers differ, the family tree from 1960 to 2019 |
| 34:40 | 08 · Inside the receiver | Receive chain, cursors, FFE vs DFE, Lucky's adaptive equalizer, the eye opening, slicer and Q-function (20 dB for 10⁻⁹), the clock-recovery PLL as a control loop, loop timing, auto-negotiation and training |
| 40:44 | 09 · Power on the same pair | Frequency separation of DC power and data, inductor and capacitor impedances, I²R and P_max = V²/4R, power budgets |
| 42:44 | 10 · Intrinsic safety | Fire triangle, zones, spark energy vs minimum ignition energy, ia/ib/ic, entity calculation vs 2-WISE port profiles |
| 44:34 | 11 · Head to head | Bandwidth per device, rate–distance, frames and addressing, 1 MB transfer times, system and physical-layer tables |
| 47:00 | Summary | Party line vs private line; a century of ideas in one chip; from the sensor to the cloud |
<!-- chapters:end -->

All facts and figures are sourced in [`docs/research_notes.md`](docs/research_notes.md);
the full narration is in [`docs/transcript.md`](docs/transcript.md) and the plan in
[`docs/storyboard.md`](docs/storyboard.md).

## What is simulated, and what is simplified

* **Computed, not hand-drawn:** the cable's pulse response (insertion loss k₁√f + k₂f scaled to the 25.6 dB budget
  at 3.75 MHz, with its minimum phase), the closed and equalised eye diagrams (least-squares FFE/DFE), the LMS echo
  canceller converging, the timing loop settling, the skin-effect current density (exact Bessel solution), the
  scrambler sequences and spectra. The models live in `video/apl/dsp.py`.
* **Illustrative:** the 4B3T table on screen is a DC-balanced code of the same kind, not the IEEE 802.3cg table; the
  echo budget (≈ 50 dB) is a worked example, not a requirement from the standard; the echo path (reflections at
  300 m, 700 m and the far end) and the noise levels are chosen for clarity; some small signals are drawn larger and
  labelled so on screen.
* CAN length limits are typical values (sources quote 25–40 m at 1 Mbit/s); the intrinsic-safety chapter explains the
  concept and is not design guidance.

## How it is made

* **Animation:** [Manim Community](https://www.manim.community/) 0.22 (Cairo renderer), one Python scene per section in
  `video/scenes/`, shared building blocks in `video/apl/`: palette and typography, devices, cables, circuit symbols,
  a perspective-projected 3D twisted pair (`widgets.py`), the journey map, name cards, scopes, eye diagrams and
  timelines (`phy.py`), and the signal models (`dsp.py`).
* **Narration:** [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) neural TTS (ONNX, voice `af_heart`),
  synthesised sentence by sentence. `video/apl/narration.py` keeps the animation in sync with the voice
  (`with self.voice("..."): ...` blocks and `{tag}` markers in the text), applies a pronunciation dictionary for
  acronyms, names and years, and logs subtitle cues.
* **Sound:** a procedural ambient pad with convolution reverb, sidechain-ducked under the voice, plus soft whooshes
  under chapter cards (`video/audio/music.py`); EBU R128 loudness normalisation to −16 LUFS.
* **Finishing:** a radial glow and faint dot grid blended in with *lighten* (lifts only the background, never the
  content), x264 encode with keyframes at chapter starts, chapters and subtitles muxed by `video/build.py`.
* **Icons:** [Tabler Icons](https://tabler.io/icons) (MIT, see `assets/icons/LICENSE-tabler-icons.txt`).

## Rebuild

Requirements: Python 3.11+, `manim`, `kokoro-onnx`, `soundfile`, `scipy`, `pillow`, a LaTeX installation with
`dvisvgm` (packages `cmbright`, `siunitx`), `ffmpeg`, and the Kokoro model files in `build/models/`
(`kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub release `model-files-v1.0`).

```bash
cd video
python3 build.py all -q l -j 4      # quick 480p15 preview
python3 build.py all -q h -j 4      # 1080p60 master (≈ 2–3 h on 4 cores)
python3 build.py parts -q h         # split the master at chapters 05 and 07 for git
python3 build.py assemble -q h --no-music   # single-track, narration-only variant
```

Outputs go to `output/`; intermediate renders, TTS cache and logs to `build/` (git-ignored).
