"""Contact sheet at chosen narration cues: python3 tools/cuesheet.py <Scene> <q> <name> idx1 idx2 ... (frame 2.5 s after each cue start)"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

scene, q, name, *idx = sys.argv[1:]
root = Path("/home/user/Ethernet-APL/build")
video = root / f"scenes_{q}" / f"{scene}.mp4"
cues = json.loads((root / f"scenes_{q}" / f"{scene}.json").read_text())["cues"]
out = root / "frames"
ims = []
for i in idx:
    if i.startswith("t"):
        t = float(i[1:])
    else:
        c = cues[int(i)]
        t = min(c["end"], c["start"] + 2.5)
    f = out / f"{name}_{i}.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(f)], check=True)
    if f.exists():
        ims.append(Image.open(f))
w, h = ims[0].size
rows = (len(ims) + 1) // 2
sheet = Image.new("RGB", (w * 2, h * rows))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % 2) * w, (k // 2) * h))
sheet.save(out / f"{name}_sheet.png")
print(out / f"{name}_sheet.png", len(cues), "cues")
