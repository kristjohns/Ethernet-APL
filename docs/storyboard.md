# Storyboard — "Ethernet-APL, explained (and how it differs from CAN bus)"

Audience: engineer with an MSc in mechanical engineering and working knowledge of
controls, signals and electronics. Tone: precise, visual, no marketing.
Colour code throughout: **CAN = amber**, **APL = cyan**, power = yellow,
hazard = orange, far-end signal = violet.

| # | Scene (file) | Key idea | Signature animation |
|---|---|---|---|
| 0 | Cold open (`s00_cold_open.py`) | A smart instrument knows a lot but reports one number at 1,200 bit/s | Radar pulses in a tank → rich data panel collapses into "12.00 mA"; slow field wire vs. 1 Gbit/s office link; 3D twisted-pair title |
| 1 | Four walls (`s01_four_walls.py`) | Why Ethernet stopped at the control room | 4–20 mA loop with live-zero wire break, HART FSK riding on the DC current, log-scale data-rate bars, four brick walls rising |
| 2 | What is APL (`s02_what_is_apl.py`) | APL is *only* a new physical layer | Walls crumble; network stack swaps its bottom layer; APL = 10BASE-T1L + port profiles + 2-WISE; spec cards |
| 3 | CAN physical (`s03_can_physical.py`) | Dominant/recessive, differential signalling | Transceiver output stage with termination; CAN_H/CAN_L/V_diff traces; common-mode noise cancels like a ΔP transmitter |
| 4 | CAN arbitration (`s04_can_arbitration.py`) | Wired-AND → non-destructive bitwise arbitration; frame anatomy | Three nodes racing bit by bit, losers dropping out; frame drawn to scale; bit stuffing |
| 5 | CAN length (`s05_can_length.py`) | Arbitration ties bit time to round-trip delay | Pulse racing to the far end and back against the sample point; log-log rate–length chart |
| 6 | APL topology (`s06_apl_topology.py`) | Point-to-point, switched, trunk & spur | Bus dissolves into a star; plant map with zones, power switch, 1000 m trunk, field switch, 200 m spurs |
| 7 | Full duplex (`s07_full_duplex.py`) | Both ends talk at once; echo cancellation | Waves travelling both ways and superposing; adaptive canceller subtracting its own echo; nonlinear vs. linear medium |
| 8 | PAM-3 / 4B3T (`s08_pam3.py`) | Keep frequencies low: 3 levels, 7.5 MBd | 4 bits → 3 ternary symbols; 16 vs 27 codes; running DC sum; spectrum vs. cable loss |
| 9 | Power + data (`s09_power_data.py`) | Frequency separation of DC power and data | Coupling network with inductors/capacitors and animated currents; filter view; power budgets |
| 10 | Intrinsic safety (`s10_intrinsic_safety.py`) | Energy limitation and 2-WISE | Fire triangle, zones, spark energy vs. MIE, ia/ib/ic, entity calculation vs. matching port profiles |
| 11 | Head to head (`s11_head_to_head.py`) | Side-by-side comparison | Shared vs. dedicated bandwidth, rate–distance chart with APL line, frames to scale, 1 MB transfer race, summary table |
| 12 | Outro (`s12_outro.py`) | Party line vs. private line | Recap of the four walls, packet from sensor to cloud, end card with sources |

Narration is generated from the text inside each scene (Kokoro TTS, voice `af_heart`);
the final transcript is written to `docs/transcript.md` and `output/*.srt` by `video/build.py`.
