# Research notes — Ethernet-APL vs. CAN bus

Fact base for the video. Every number used on screen or in the narration is listed
here with its source. Where sources disagree, the value used in the video is marked
**(used)** and the spread is noted.

---

## 1. Context: field communication before Ethernet-APL

| Technology | Signalling | Data rate | Notes |
|---|---|---|---|
| 4–20 mA loop | Analog DC current | 1 value per pair | Loop-powered; device must live on < 3.6 mA (~40 mW budget, e.g. 10 V × 4 mA) [ADI, TI] |
| HART | Bell 202 FSK superimposed on 4–20 mA, ±0.5 mA; 1200 Hz = "1", 2200 Hz = "0" | 1200 bit/s | Late 1980s; needs ≥ 250 Ω loop resistance [HART/Bell 202 refs] |
| FOUNDATION Fieldbus H1 / PROFIBUS PA | IEC 61158-2 MBP (Manchester, bus powered) | 31.25 kbit/s, shared | Segment ≤ 1900 m incl. spurs (Type A cable); ≤ 32 devices (practically 10–12) [FF H1 refs, TI DAC874xH] |
| 100BASE-TX Ethernet | 2 pairs (1000BASE-T: 4 pairs) | 100 Mbit/s | 100 m channel limit |

Why plain Ethernet never reached the instruments ("four walls"):
1. **Distance** – 100 m limit vs. hundreds of metres in plants.
2. **Wires** – 2 or 4 pairs vs. installed 2-wire field cable.
3. **Power** – field devices are powered over their signal pair.
4. **Explosion protection** – intrinsic safety needs energy-limited circuits.

## 2. Ethernet-APL — what it is

* "Advanced Physical Layer": a physical layer for Ethernet for the process industries,
  built on **IEEE 802.3cg-2019 10BASE-T1L** plus APL port profiles and the 2-WISE
  intrinsic-safety concept [Wikipedia "Advanced Physical Layer"; APL project press releases].
* Developed by the **APL Project**: FieldComm Group, ODVA, OPC Foundation and
  PROFIBUS & PROFINET International (PI), with 12 industry partners; project completion
  announced 2022 after "almost 4 years" [ODVA/automation.com press release, Aug 2022].
* Standards:
  * **IEEE 802.3cg-2019**, Clause 146 = 10BASE-T1L PHY.
  * **IEC TS 60079-47:2021** (published 2021-02) = 2-WISE, *2-Wire Intrinsically Safe Ethernet* [IEC webstore].
  * **IEC TS 63444:2023** (published 2023-11) = Ethernet-APL port profile specification; Ed. 2 (2026) renamed
    "Ethernet-APL / Ethernet-SPE profile specification" [IEC webstore, VDE preview].
* Protocol-agnostic: PROFINET, EtherNet/IP, HART-IP, OPC UA, Modbus TCP — even at the
  same time on one network — plus IT protocols (HTTP, FTP…) [ARC, Control Global, P+F FAQ].

### Topology and limits
* Point-to-point links joined by switches; trunk-and-spur architecture.
* **APL power switch** (safe area/control room cabinet): connects to plant Ethernet, feeds the trunk.
* **Trunk**: up to **1000 m**, **2.4 Vpp**, carries power + data; e.g. Ex eb (increased safety) for Zone 1 [R. Stahl engineering process paper; APL Engineering Guideline].
* **Field switch** (Zone 1 or Zone 2): trunk-powered or auxiliary-powered; typically 8–16 spur ports [P+F, Softing, Moxa datasheets].
* **Spur**: up to **200 m** (cable category IV), **1.0 Vpp**, intrinsically safe (Ex ia up to Zone 0) [Guideline V1.11; P+F].
* Reference cable: **fieldbus Type A cable** (IEC 61158-2), shielded twisted pair,
  100 Ω ± 20 % (100 kHz – 20 MHz); wire sizes 26 AWG – 14 AWG; existing Type A cable can often be reused [R. Stahl; E+H].
* Segment explosion protection level = lowest-rated 2-WISE port on it (e.g. ia device on ic port → ic) [APL guideline DE V1.14].

### Power
* Trunk power classes (max 50 V): **Class 3 ≥ 57.5 W** (46 V × 1.25 A) and **Class 4 ≥ 92 W** (46 V × 2 A) at the source;
  cable losses reduce what reaches the field switches (~36 W for Class 3 in an IEEE example) [IEEE 802.3 PDCC slides, Graber 2023].
* Spur power classes (15 V max PSE): **Class A ≈ 0.54 W**, **Class C ≈ 1.1 W** (Class B ≈ 1.16 W added in 2026 Ed. 2) [R. Stahl; PDCC slides; SPE app note].
* Port profile examples: switch spur ports **SPAA**, **SPCC**; device port **SLAA** connects to SPAA or SPCC [Yokogawa ROTAMASS manual; E+H TMT86 TI].
* Compare: 4–20 mA device ≈ 40 mW → APL gives > 10× more power per device ("more than half a watt or even more than one watt") [ADI blog; Control Global].

## 3. 10BASE-T1L physical layer (IEEE 802.3cg Clause 146)

* **10 Mbit/s, full duplex, one balanced twisted pair**, point-to-point (no multidrop).
* **PAM-3** (three levels) at **7.5 MBd**; Nyquist **3.75 MHz**; typically < 10 MHz bandwidth [IEEE 802.3cg tutorial; ADI; Murray IEEE 802.3dg].
* **4B3T** coding: 4 scrambled bits → 3 ternary symbols with running disparity → DC-free [P802.3cg D2.0].
  (16 of 27 ternary triplets needed → spare codes for DC balance.) 7.5 MBd × 4/3 = 10 Mbit/s.
* Scrambler (draft text: 1 + x¹³ + x³³).
* **Echo cancellation** for full duplex on one pair; no FEC; reach **1000 m on 18 AWG**; in practice up to ~2000 m depending on noise [802.3cg tutorial; Murray; ZHAW].
* Transmit amplitude: **1.0 Vpp** (base) or **2.4 Vpp** (optional, long reach) [TI SNLA360; ADI].
* Insertion-loss limit for 2.4 Vpp ≈ **25.6 dB at 3.75 MHz** (≈ 1000 m of AWG18) [IEEE 802.3cg link segment refs].
* Low-power PHYs: ADIN1100 ≈ 39 mW (1.0 Vpp, dual supply), 81 mW (2.4 Vpp) [ADI datasheet PrG].
* Single Pair Ethernet family: 10BASE-T1S (short-reach, multidrop, ~15–25 m), 10BASE-T1L (long reach),
  100BASE-T1 (802.3bw, automotive 15 m), 1000BASE-T1; 100BASE-T1L (802.3dg, ≥ 500 m) in progress.

## 4. Intrinsic safety and 2-WISE

* Explosion needs fuel + oxidiser + ignition source; IS removes the ignition source by energy limitation.
* Zones (gas): Zone 0 continuous/long periods; Zone 1 likely in normal operation; Zone 2 not likely/short periods.
* Gas groups and approx. minimum ignition energy: IIA (propane) ≈ 260 µJ, IIB (ethylene) ≈ 95 µJ,
  **IIC (hydrogen) ≈ 19–20 µJ** [Energy Institute table].
* Protection levels: **ia** = safe with 2 faults (Zone 0), **ib** = 1 fault (Zone 1), **ic** = normal operation (Zone 2).
* Stored energy: E_C = ½ C V², E_L = ½ L I².
* **2-WISE (IEC TS 60079-47)**: based on IEC 60079-11 / -25 and the FISCO idea; universal IS parameter limits for APL ports
  (source Po ≤ 5.32 W, Uo 17.5 V class values appear in datasheets); interconnection of 2-WISE ports without calculating
  entity parameters — check atmosphere suitability and protection level (ia/ib/ic) only [IEC; R. Stahl FAQ; P+F datasheets].

## 5. CAN bus (reference technology)

* Bosch, presented Feb **1986** at SAE congress Detroit; first controllers 1987 (Intel 82526, Philips 82C200);
  CAN 2.0A/B 1991; first production car Mercedes W140 (1991); **ISO 11898** 1993 [CiA history; Wikipedia].
* Physical layer ISO 11898-2: twisted pair, **120 Ω** characteristic impedance, terminated at both ends.
* **Recessive**: drivers off, both lines ≈ 2.5 V, V_diff ≈ 0. **Dominant**: CAN_H ≈ 3.5 V, CAN_L ≈ 1.5 V, V_diff ≈ 2 V.
  Receiver: < 0.5 V → recessive, > 0.9 V → dominant [TI SN65HVD23x; Kvaser; Vector].
* Dominant overwrites recessive (wired-AND) → **non-destructive bitwise arbitration** (CSMA/CR); lowest ID wins.
* Classic data frame: SOF 1, ID 11 (29 ext.), RTR 1, IDE 1, r0 1, DLC 4, data 0–64 bits, CRC 15, CRC delimiter 1, ACK 1,
  ACK delimiter 1, EOF 7, IFS 3 → 111 bits for 8 data bytes (+ up to 24 stuff bits = 135); stuff bit after 5 equal bits.
  Effective payload efficiency ≈ 47–58 %.
* Content addressing: identifier names the message, not a node; every node filters.
* **Rate vs length**: round trip (≈ 5 ns/m cable + transceiver loop delay) must fit before the sample point.
  ≈ 40 m @ 1 Mbit/s (ISO 11898-2 nominal; CiA practical 25–30 m), 100 m @ 500 kbit/s, 250 m @ 250 kbit/s,
  500 m @ 125 kbit/s, 1 km @ 50 kbit/s, 5 km @ 10 kbit/s → bit rate × length ≈ 40–60 Mbit/s·m [ADI, CiA, Schneider, onsemi].
* **CAN FD**: up to 64 data bytes, data phase bit rate switching (typ. 2–5, up to 8 Mbit/s) — possible because only one
  node transmits after arbitration. **CAN XL** (ISO 11898-1:2024): 1–2048 bytes, up to 20 Mbit/s [CiA, Ixxat, Fraunhofer].
* Power is not part of CAN (DeviceNet/CANopen cables add separate supply pairs). No standardised plug-and-play IS concept.

## 6. Numbers used in the comparison chapter

* Transfer of 1 MB (8 Mbit), raw rate, best case:
  HART 1.2 kbit/s → 6667 s ≈ **1 h 51 min**; FF H1 31.25 kbit/s → 256 s ≈ **4 min 16 s**;
  CAN 1 Mbit/s at ~53 % efficiency → ≈ **15 s**; APL 10 Mbit/s at ~95 % efficiency (TCP/IP, 1500 B frames) → ≈ **0.84 s**.
* Frame time on the wire: CAN 8-byte frame at 1 Mbit/s = 111–135 µs; Ethernet minimum frame (64 B + 8 B preamble +
  12 B IFG = 672 bits) at 10 Mbit/s = 67.2 µs; maximum frame (1518 B + 20 B) = 1.23 ms.
* Speed–distance product: CAN ≈ 50 Mbit/s·m; 10BASE-T1L 10 Mbit/s × 1000 m = 10 000 Mbit/s·m (≈ 200×).
* Bits in flight: 1000 m × 5 ns/m = 5 µs ≈ 37 symbols on the wire per direction (APL) vs. 0.2 bit for 40 m CAN at 1 Mbit/s.

---

## Sources

* Wikipedia — Advanced Physical Layer: https://en.wikipedia.org/wiki/Advanced_Physical_Layer
* APL Engineering Guideline V1.11: https://www.ethernet-apl.org/wp-content/uploads/2022/08/APLEngineeringGuidelineV111_1.11.pdf
* APL Engineering Guideline (DE) V1.14: https://www.ethernet-apl.org/wp-content/uploads/APL-Engineering-Guideline-V114-DE_1.14.pdf
* Ethernet-APL "Ethernet to the field" white paper: https://www.ethernet-apl.org/wp-content/uploads/2022/08/Ethernet-APL_Ethernet-To-The-Field_EN_FINAL_June-2021.pdf
* APL project completed (ODVA): https://www.odva.org/news/apl-project-successfully-completed-ethernet-apl-is-here/
* IEC TS 63444:2023: https://webstore.iec.ch/en/publication/73387
* IEC TS 60079-47:2021: https://webstore.iec.ch/en/publication/64292
* IEEE 802.3cg tutorial (Jan 2019): https://www.ieee802.org/3/cg/public/Jan2019/Tutorial_cg_0119_final.pdf
* IEEE 802.3 PDCC — Ethernet-APL power classes (Graber, 2023): https://www.ieee802.org/3/ad_hoc/PDCC/public/2023/graber_PDCC_01_03292023.pdf
* Murray et al., IEEE P802.3dg 100BASE-T1L PHY: https://www.ieee802.org/3/dg/public/May_2022/Murray_3dg_01a_01242024.pdf
* TI SNLA360 (SPE in building automation): https://www.ti.com/lit/pdf/snla360
* ADI — The new 10BASE-T1L standard: https://www.analog.com/en/resources/technical-articles/the-new-10base-t1l-standard.html
* ADI — Configure CAN bit timing: https://www.analog.com/en/resources/analog-dialogue/articles/configure-can-bit-timing.html
* ADI EngineerZone — 10BASE-T1L powering field instruments: https://ez.analog.com/ez-blogs/b/engineerzone-spotlight/posts/10base-t1l-makes-powering-intelligent-field-instruments-painless
* R. Stahl — 13 questions on Ethernet-APL: https://r-stahl.com/en/global/blog/post-detail/13-questions-13-answers-ethernet-apl-is-the-future/
* R. Stahl — The Ethernet-APL engineering process: https://r-stahl.com/en/global/blog/post-detail/the-ethernet-apl-engineering-process/
* R. Stahl — Ethernet-APL ready for practical use: https://r-stahl.com/en/global/blog/post-detail/ethernet-apl-ready-for-practical-use/
* Pepperl+Fuchs — Ethernet-APL: https://pepperl-fuchs.com/global/en/ethernet-apl.htm
* Control Global — Ethernet-APL safe and efficient communication: https://www.controlglobal.com/network/industrial-networks/article/55290947/ethernet-apl-safe-and-efficient-communication-for-hazardous-areas
* Yokogawa ROTAMASS PROFINET over APL manual: https://web-material3.yokogawa.com/IM%2001U10B00-11EN-R_ADD%20PROFINET%20over%20APL_EN.pdf
* CiA — History of CAN technology: https://www.can-cia.org/can-knowledge/can/can-history
* CiA — CAN XL: https://www.can-cia.org/can-knowledge/can-xl
* Wikipedia — CAN bus: https://en.wikipedia.org/wiki/CAN_bus
* TI SN65HVD23x datasheet (CAN thresholds): https://www.ti.com/document-viewer/SN65HVD234-Q1/datasheet/application-and-implementation
* Kvaser — The CAN bus: https://kvaser.com/?p=18332
* Wikipedia — Foundation Fieldbus H1: https://en.wikipedia.org/wiki/Foundation_Fieldbus_H1
* Energy Institute — ignition energies: https://www.energyinst.org/?a=25610

---

## 7. Deep dive: the physics and signal processing of the link

### Transmission-line physics (chapter 05)
* **Kelvin (William Thomson), 1855**, "On the theory of the electric telegraph": a submarine cable as distributed R and C
  → diffusion equation ∂v/∂t = (1/R′C′) ∂²v/∂x² (the form of Fourier's heat equation). Pulse response at distance x:
  v ∝ t^(−3/2)·exp(−R′C′x²/4t), peak at **t = R′C′x²/6** → "law of squares" (delay ∝ length²).
* **1858 transatlantic cable** (Valentia, Ireland – Trinity Bay, Newfoundland): Queen Victoria's 98-word message took
  ≈ 16 h (partly operational problems); chief electrician Wildman Whitehouse called Kelvin's theory "a fiction of the
  schools", drove the cable with induction coils of ≈ 2,000 V; insulation failed after about three weeks.
  1866 cable (Great Eastern) succeeded; signals read with Kelvin's mirror galvanometer (invented 1858).
* **Heaviside, 1880s**: telegrapher's equations with R′, L′, G′, C′; distortionless condition R′/L′ = G′/C′ (1887);
  loading coils (Pupin patent 1899/1900, Campbell at AT&T). For ωL′ ≫ R′, ωC′ ≫ G′ → wave equation, d'Alembert (1747)
  solution v = f(x − ct) + g(x + ct), **c = 1/√(L′C′)**, **Z₀ = √(L′/C′)**.
* Cable model used on screen: Z₀ = 100 Ω, v = 2×10⁸ m/s (≈ ⅔ c, 5 ns/m) → L′ = Z₀/v = 0.5 µH/m, C′ = 1/(Z₀v) = 50 pF/m.
  1 km = 5 µs = 37.5 symbols at 7.5 MBd. 18 AWG loop resistance ≈ 42 Ω/km (Type A spec 44 Ω/km) → R′ = ωL′ at
  f ≈ R′/(2πL′) ≈ **13 kHz** (diffusion below, waves above). HART (1.2/2.2 kHz) is in the RC regime — consistent with
  HART's cable rule being an RC time constant limit; FF H1 (31.25 kHz) is near the crossover.
* Reflection coefficient Γ = (Z_L − Z₀)/(Z_L + Z₀): open +1, short −1, matched 0. Joukowsky (water hammer)
  Δp = ρ·a·Δv is the hydraulic analogue of V = Z₀·I.
* **Skin effect**: δ = √(2ρ/(ωμ)); copper (ρ = 1.72×10⁻⁸ Ω·m): δ = 66 µm at 1 MHz, **34 µm at 3.75 MHz**.
  Exact round-wire result (Bessel functions) for 18 AWG (r = 0.51 mm): R_ac/R_dc = 1.48 at 100 kHz, 4.1 at 1 MHz,
  **7.7 at 3.75 MHz**. Same diffusion maths as the damping of the daily temperature wave in soil (damping depth
  √(2α/ω) ≈ 12 cm for α ≈ 5×10⁻⁷ m²/s).
* Low-loss attenuation α ≈ R′/(2Z₀) + G′Z₀/2. Insertion-loss model used on screen IL(f) = 11.5·√f + 0.9·f dB/km
  (f in MHz), scaled to the 10BASE-T1L budget of **25.6 dB at 3.75 MHz** for 1 km (amplitude ÷ 19); gives 30.2 dB at
  5 MHz, 20.4 dB at 2.5 MHz, 45 dB at 10 MHz.
* Pulse response computed as the minimum-phase response of that magnitude (real cepstrum): one 133 ns symbol comes out
  with ≈ 17 % peak height and a tail lasting ≈ 70 symbols (to 1 %); post-cursors h₁/h₀ ≈ 0.73, h₂/h₀ ≈ 0.49 …

### Signalling theory and line codes (chapter 06)
* **Nyquist 1928** ("Certain topics in telegraph transmission theory"): ≤ 2B independent pulses per second in bandwidth B;
  sinc pulses give zero ISI at the sampling instants. **Hartley 1928** ("Transmission of information"): log M per pulse.
  **Shannon 1948** ("A mathematical theory of communication"): C = B log₂(1 + S/N). All at Bell Labs / AT&T.
* 10 Mbit/s options: Manchester (10BASE-T, 1990): energy ≈ 5–10 MHz → 30–45 dB per km. PAM-2 at 10 MBd: Nyquist 5 MHz,
  30.2 dB. **PAM-3 (4B3T) at 7.5 MBd: 3.75 MHz, 25.6 dB.** PAM-4 at 5 MBd: 2.5 MHz, 20.4 dB but ⅓ level spacing.
* 4B3T: 16 of 27 triplets; mirror-image codes chosen by a running digital sum → DC-free. A 4B3T code (MMS43) was used on
  the ISDN U interface in Germany in the 1980s (120 kBd, 160 kbit/s gross, echo-cancelled, several km). The on-screen
  table is illustrative, not the IEEE 802.3cg table.
* Baseline wander: the data path is AC-coupled (coupling capacitors, transformers, PoDL network) = high-pass; DC content
  makes the levels drift relative to the slicer thresholds.
* Scramblers: side-stream LFSR, master **1 + x¹³ + x³³**, slave **1 + x²⁰ + x³³** (reciprocal polynomials, same as
  1000BASE-T). Both verified primitive here (2³³ − 1 = 7 · 23 · 89 · 599479) → period 8 589 934 591 bits ≈ 14.3 min at
  10 Mbit/s. Different polynomials keep the two directions uncorrelated.
* Transmit amplitude: 2.4 Vpp (±1.2 V, trunk / long reach) or 1.0 Vpp (±0.5 V, IS spur); 100 Ω source impedance.

### Full duplex, echo cancellation (chapter 07)
* Telephone hybrids separate send and receive on a two-wire line; long-distance circuits use four wires with amplifiers,
  hybrid imbalance → echo (Campbell proposed four-wire repeater circuits in 1912, BSTJ 1935).
* Echo budget used on screen: own signal 2.4 Vpp; far end after 25.6 dB ≈ 0.13 Vpp; slicer needs ≈ 20 dB SNR + margin →
  residual echo ≈ 50 dB below own transmission (illustrative budget, ≈ 300× in amplitude).
* LMS: **Widrow & Hoff, 1960** (Stanford, ADALINE): h ← h + μ·e·a. Echo cancellers: Kelly, Logan and Sondhi at Bell Labs in
  the 1960s for satellite circuits (≈ 0.5–0.6 s echo delay). Same principle in ISDN (1980s), 1000BASE-T (1999),
  100BASE-T1 (2015), 10BASE-T1L (2019).
* LMS simulation on screen: 80 symbol-spaced taps, echo path = hybrid leakage + reflections at 300 m (3 µs), 700 m
  (7 µs) and the far end (10 µs = 75 symbols); gear-shifted μ; residual echo ≈ −50 dB after ≈ 50 000 symbols.

### Receiver (chapter 08)
* Equalisation: FFE (linear, boosts high frequencies and noise) + DFE (subtracts tails of past decisions, no noise
  enhancement, error propagation). **Lucky, 1965**, BSTJ 44: automatic/adaptive equalisation for data over telephone lines.
* Slicer: PAM-3 thresholds at ±d/2; P_s ≈ (4/3)·Q(d/2σ); 10⁻⁹ → d/2σ ≈ 6.0 → SNR ≈ 19.9 dB (20.4 dB at 10⁻¹⁰).
  10BASE-T1L has no FEC.
* Clock recovery: PLL (timing detector → PI loop filter → NCO), closed loop H(s) = (K_p s + K_i)/(s² + K_p s + K_i).
  Loop timing: the slave transmits on the clock recovered from the master (as in 1000BASE-T/10GBASE-T: echo
  cancellation needs TX and RX on the same clock); IEEE 802.3cg contributions assumed ≈ 5 ppm oscillator offsets and a
  silent slave until its clock is acquired.
* Start-up: auto-negotiation (Clause 98, low-speed differential-Manchester pages) resolves amplitude (2.4/1.0 Vpp) and
  master/slave; training: master sends scrambled idles, slave locks clock/equaliser/descrambler, then transmits; link up
  when both local receivers report OK.

### Ethernet history (chapter 04)
* Metcalfe memo at Xerox PARC, 22 May 1973; experimental Ethernet 2.94 Mbit/s on coax; DIX 10 Mbit/s 1980; IEEE 802.3
  approved 1983 (10BASE5). CSMA/CD slot time 512 bit times = 51.2 µs at 10 Mbit/s = 64-byte minimum frame, sized for a
  ≈ 2.5 km collision domain with repeaters. 10BASE-T 1990 (Manchester, 2 pairs), 100BASE-TX 1995 (4B5B + MLT-3),
  full duplex IEEE 802.3x (1997), 1000BASE-T 1999 (PAM-5, 4 pairs, hybrids + echo cancellation), 100BASE-T1 2015
  (single pair, PAM-3), 10BASE-T1L 2019.

### Power (chapter 09)
* Typical PoDL coupling: 220 µH inductors, 220 nF capacitors (ADI reference designs); |Z_L| = 2π·3.75 MHz·220 µH ≈ 5.2 kΩ,
  |Z_C| = 1/(2π·3.75 MHz·220 nF) ≈ 0.19 Ω. P_loss = (P/V)²·R_loop; P_max = V²/(4R_loop) at 50 % efficiency.
* 10BASE-T1L PHY power: ADIN1100 ≈ 39 mW (1.0 Vpp) / 81 mW (2.4 Vpp).

### Additional sources
* Wikipedia — Transatlantic telegraph cable; Telegrapher's equations; Oliver Heaviside; Skin effect; Nyquist–Shannon;
  Hybrid transformer; Man Mohan Sondhi; Ethernet; CSMA/CD.
* Bell Labs BSTJ brief — A self-adaptive echo canceller (Sondhi): https://www.nokia.com/bell-labs/publications-and-media/publications/bstj-briefs-a-self-adaptive-echo-canceller/
* BSTJ 1935 (four-wire circuits, Campbell 1912): https://www.worldradiohistory.com/Archive-Bell-System-Technical-Journal/30s/Bell-1935d.o.pdf
* IEEE 802.3cg contributions (Graber, 2018–2019) on 10BASE-T1L start-up and clocking: https://www.ieee802.org/3/cg/public/
* 10GBASE-T loop timing (IEEE 802.3an): https://www.ieee802.org/3/an/public/nov04/powell_1_1104.pdf
* CSMA/CD slot time: https://classes.engineering.wustl.edu/~jain/cse473-09/ftp/ethernet.pdf
