"""Fill the chapter table in README.md from build/assembly_<q>/chapters.json:  python3 tools/readme_chapters.py h"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
q = sys.argv[1] if len(sys.argv) > 1 else "h"

HIGHLIGHTS = {
    "Intro": "A radar level transmitter knows a lot but reports one number over 4–20 mA; the plan for the deep dive",
    "01": "4–20 mA live zero, HART FSK on the loop current, fieldbus, the four walls that kept Ethernet out of the field",
    "02": "APL replaces only the physical layer: 10BASE-T1L + port profiles (IEC TS 63444) + 2-WISE (IEC TS 60079-47)",
    "03": "Dominant/recessive, differential reception, bitwise arbitration, frame anatomy, bit rate × length ≈ constant, "
          "bit timing with time quanta, hard sync, resynchronisation and bit stuffing",
    "04": "Metcalfe's 1973 coax “ether”, CSMA/CD and the 64-byte slot time (CAN's round trip, paid per frame), switches and "
          "full duplex, fifty years of Ethernet PHYs; APL's trunk-and-spur topology",
    "05": "The 1858 Atlantic cable and Kelvin's law of squares (Fourier's heat equation), Heaviside's telegrapher's equations "
          "→ the wave equation, mass–spring chain ≡ LC ladder, c = 1/√(L′C′), Z₀ = √(L′/C′), water hammer, reflections, "
          "skin effect (δ = 34 µm at 3.75 MHz), cable loss, intersymbol interference, why twisting works",
    "06": "Nyquist, Hartley and Shannon; Manchester vs PAM-2/3/4 at 10 Mbit/s; 4B3T and running disparity; baseline wander; "
          "the 33-bit scrambler (period ≈ 14 min); the complete transmitter",
    "07": "Superposition on a linear line, the telephone hybrid, the transceiver hybrid with replica network, a 50 dB echo "
          "budget, the LMS echo canceller converging, why the two scramblers differ, the family tree from 1960 to 2019",
    "08": "Receive chain, cursors, FFE vs DFE, Lucky's adaptive equalizer, the eye opening, slicer and Q-function (20 dB for "
          "10⁻⁹), the clock-recovery PLL as a control loop, loop timing, auto-negotiation and training",
    "09": "Frequency separation of DC power and data, inductor and capacitor impedances, I²R and P_max = V²/4R, power budgets",
    "10": "Fire triangle, zones, spark energy vs minimum ignition energy, ia/ib/ic, entity calculation vs 2-WISE port profiles",
    "11": "Bandwidth per device, rate–distance, frames and addressing, 1 MB transfer times, system and physical-layer tables",
    "Summary": "Party line vs private line; a century of ideas in one chip; from the sensor to the cloud",
}

info = json.loads((ROOT / "build" / f"assembly_{q}" / "chapters.json").read_text())
rows = []
for c in info["chapters"]:
    m, s = divmod(int(c["time"]), 60)
    key = c["title"][:2] if c["title"][:2].isdigit() else c["title"]
    rows.append(f"| {m:02d}:{s:02d} | {c['title']} | {HIGHLIGHTS.get(key, '')} |")
readme = ROOT / "README.md"
text = readme.read_text()
block = "<!-- chapters:start -->\n| Time | Chapter | Highlights |\n|---|---|---|\n" + "\n".join(rows) + "\n<!-- chapters:end -->"
text = re.sub(r"<!-- chapters:start -->.*?<!-- chapters:end -->", block, text, flags=re.S)
total = info["total"]
text = re.sub(r"\*\*\d+ min, 1080p60\*\*", f"**{round(total / 60)} min, 1080p60**", text)
readme.write_text(text)
print(f"README updated: {len(rows)} chapters, {total / 60:.1f} min")
