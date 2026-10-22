"""Contact sheet of frames from a rendered scene: python3 tools/sheet.py <video> <name> t1 t2 ..."""
import subprocess
import sys
from pathlib import Path

from PIL import Image

video, name, *times = sys.argv[1:]
out = Path("/home/user/Ethernet-APL/build/frames")
out.mkdir(parents=True, exist_ok=True)
ims = []
for t in times:
    f = out / f"{name}_{t}.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", t, "-i", video, "-frames:v", "1", str(f)], check=True)
    ims.append(Image.open(f))
w, h = ims[0].size
rows = (len(ims) + 1) // 2
sheet = Image.new("RGB", (w * 2, h * rows))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % 2) * w, (i // 2) * h))
sheet.save(out / f"{name}_sheet.png")
print(out / f"{name}_sheet.png")
