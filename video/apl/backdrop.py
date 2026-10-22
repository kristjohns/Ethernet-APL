"""Backdrop applied in post: a radial glow (+ faint dot grid) blended with *lighten*.

Blending max(frame, backdrop) in RGB lifts only pixels darker than the
backdrop, i.e. the flat background.  Diagrams, text and panels are brighter
and stay untouched, and background-coloured masking shapes blend in too.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .style import ROOT

BG_RGB = np.array([10, 15, 30], dtype=np.float32)       # style.BG
GLOW_RGB = np.array([16, 26, 50], dtype=np.float32)     # centre of the glow (still darker than PANEL)
DOT_RGB = np.array([17, 25, 46], dtype=np.float32)


def make(width=1920, height=1080, path: Path | None = None) -> Path:
    path = path or ROOT / "build" / f"backdrop_{width}x{height}.png"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = (x - width * 0.5) / (width * 0.5)
    ny = (y - height * 0.45) / (height * 0.5)
    r = np.sqrt(nx ** 2 * 0.8 + ny ** 2 * 1.2)
    w = np.clip(1 - r / 1.25, 0, 1) ** 1.8
    img = BG_RGB[None, None, :] + (GLOW_RGB - BG_RGB)[None, None, :] * w[..., None]
    step = width / 14.2222 * 0.5          # dot every 0.5 Manim units
    gx = np.abs((x - width / 2) / step - np.round((x - width / 2) / step)) * step
    gy = np.abs((y - height / 2) / step - np.round((y - height / 2) / step)) * step
    dot = np.clip(1.4 - np.sqrt(gx ** 2 + gy ** 2) / (width / 1920), 0, 1) * np.clip(1 - r / 1.1, 0, 1)
    img = np.maximum(img, BG_RGB + (DOT_RGB - BG_RGB) * dot[..., None])
    Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8)).save(path)
    return path
