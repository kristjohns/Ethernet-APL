# Storyboard — "Ethernet-APL, a deep dive (and how it differs from CAN bus)"

Audience: engineer with an MSc in mechanical engineering, working knowledge of controls, signals and
electronics, comfortable with maths. Tone: precise, visual, no marketing. Mechanical analogies wherever they
carry real insight (mass–spring chain, water hammer, soil temperature, dashpot, control loops).
Colour code throughout: **CAN = amber**, **APL = cyan**, power = yellow, hazard = orange, far end = violet,
losses = orange/red, magnetic field = blue, history = copper/blue cards.

The deep-dive edition keeps the first video's story (four walls → one new layer → CAN as reference → APL) and
inserts four chapters that follow a single bit through the physical layer, plus more history. A recurring
"journey map" (transmitter stack → 1 km pair → receiver stack) opens chapters 05–08 and closes chapter 08.

| # | Scene (file) | Key idea | Signature animation |
|---|---|---|---|
| Intro | `s00_cold_open.py` | A smart instrument reports one number; this time we go down to the physics | Radar tank, 4–20 mA collapse, 3D twisted pair, chips "bits → volts / waves on a wire / receivers" |
| 01 | `s01_four_walls.py` | Why Ethernet stopped at the control room | Live zero, HART FSK, data-rate bars, four walls |
| 02 | `s02_what_is_apl.py` | APL is *only* a new physical layer | Stack swaps its bottom layer; 10BASE-T1L + port profiles + 2-WISE |
| 03 | `s03_can_physical.py` | Dominant/recessive, differential signalling | Transceiver output stage, CAN_H/CAN_L/V_diff |
| 03 | `s04_can_arbitration.py` | Wired-AND arbitration, frame anatomy | Three nodes racing bit by bit; frame to scale |
| 03 | `s05_can_length.py` | Arbitration ties bit time to round trip | Pulse racing against the sample point; rate–length chart |
| 03 | `s06_can_bit_timing.py` | CAN recovers timing from occasional edges | 16 time quanta (SYNC/PROP/PHASE1/PHASE2), hard sync, resync, stuff bit |
| 04 | `s07_ethernet_history.py` | Ethernet was a bus too; switches + full duplex removed the round-trip limit | 1973 coax "ether", collision, 64-byte slot time diagram, star switch, 1973–2019 PHY timeline |
| 04 | `s08_apl_topology.py` | Point-to-point, trunk & spur | Bus dissolves into a star; plant map with zones |
| 05 | `s09_telegraph.py` | The wire is a distributed system: Kelvin's diffusion vs Heaviside's waves | Journey map; 1858 Atlantic cable; RC ladder ≡ heat equation; heat soaking along a bar; law of squares t = R′C′x²/6; Whitehouse quote; mirror galvanometer; telegrapher's equations → wave equation; RC vs LC lanes; 13 kHz crossover chart (HART / H1 / APL bands) |
| 05 | `s10_waves.py` | Waves, Z₀, reflections | Mass–spring chain driving an LC ladder in sync; c = 1/√(L′C′) = 2×10⁸ m/s; 37.5 symbols in flight both ways; edge charging the line → Z₀ = √(L′/C′) = 100 Ω; water hammer (Joukowsky); open/short/matched reflections; CAN vs APL termination; small echoes from connectors |
| 05 | `s11_losses.py` | Loss, skin effect, ISI, interference | R and G glowing; exponential decay; soil temperature wave vs current density in an 18 AWG cross-section (exact Bessel solution, δ = 34 µm, R/R_DC = 7.7); IL = k₁√f + k₂f with 25.6 dB at 3.75 MHz; one symbol through 1 km (computed minimum-phase response); convolution; closed eye; Faraday loops cancelling in a twisted pair |
| 06 | `s12_signalling_limits.py` | Nyquist, Hartley, Shannon: the two knobs | Sinc pulses with zero crossings; level ladders; noisy levels; C = B log₂(1 + S/N) |
| 06 | `s13_line_codes.py` | Why PAM-3 / 4B3T at 7.5 MBd | Manchester spectrum vs cable loss; PAM-2/3/4 table (Nyquist, loss, level spacing); 4B3T mapping, 16 vs 27, mirror codes, running sum; baseline wander through AC coupling |
| 06 | `s14_scrambler.py` | Scrambling, and the complete transmitter | Idle pattern → spectral lines; 33-bit LFSR with taps 13/33 shifting live; XOR identity; period 2³³−1; master/slave polynomials; transmit chain with signal snapshots, 100 Ω source, ±1.2 V / ±0.5 V |
| 07 | `s15_hybrid.py` | Full duplex on one linear pair | d'Alembert superposition; telephone hybrid and echo; transceiver hybrid with replica network and node scopes; echo budget ≈ 50 dB |
| 07 | `s16_echo_canceller.py` | Adaptive echo cancellation | Echo impulse response (leakage + reflections at 3/7/10 µs); tapped delay line, multiplier-free; LMS weights converging (simulated) with residual-echo curve; why scramblers must differ; 1960–2019 family tree; nonlinear vs linear medium |
| 08 | `s17_equalizer.py` | Equalisation | Receive chain with DFE and clock loops; cursors; FFE inverse filter and noise boost; DFE waterfall (tails subtracted); Lucky 1965; eyes: closed → short FFE → FFE+DFE (simulated) |
| 08 | `s18_clock_recovery.py` | Decisions and the recovered clock | Slicer with Gaussian tails, Q-function, 10⁻⁹ → 20 dB; PLL block diagram, H(s), phase error settling, sampling instant moving into the eye; CAN vs APL timing; loop timing |
| 08 | `s19_link_up.py` | Start-up and the journey of one bit | Auto-negotiation pages; training timeline with checkmarks; LINK UP; bit travelling through the journey map |
| 09 | `s20_power_data.py` | Power on the same pair | Spectrum DC vs data; coupling network with animated currents; |Z_L| ≈ 5.2 kΩ, |Z_C| ≈ 0.2 Ω; I²R vs voltage, P_max = V²/4R; power budgets |
| 10 | `s21_intrinsic_safety.py` | Energy limitation and 2-WISE | Fire triangle, zones, spark energy vs MIE, ia/ib/ic, port profiles |
| 11 | `s22_head_to_head.py` | Side-by-side comparison | Bandwidth, rate–distance, frames, 1 MB race, system table, physical-layer table, where each shines |
| Summary | `s23_outro.py` | Party line vs private line; a century of ideas in one chip | Recap panels, history cards → PHY chip, sensor-to-cloud packet, end card |

Shared building blocks: `video/apl/phy.py` (journey map, name cards, scopes, RLGC slice, eyes, timelines) and
`video/apl/dsp.py` (cable model with minimum-phase response, 4B3T, LFSR, LMS echo canceller, FFE/DFE design,
timing loop). Every waveform marked as "simulated" on screen is computed from these models.

Narration is generated from the text inside each scene (Kokoro TTS, voice `af_heart`); the final transcript is
written to `docs/transcript.md` and `output/*.srt` by `video/build.py`.
