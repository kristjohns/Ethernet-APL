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
