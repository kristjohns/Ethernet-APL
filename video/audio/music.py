"""Procedural ambient music bed + transition whooshes (no samples, fully reproducible).

A slow four-chord pad (D major / B minor colours) built from detuned additive
voices, low-passed, given a synthetic convolution reverb and sidechain-ducked
under the narration so it never competes with the voice.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48000

# chord voicings (Hz) — Dmaj9, Bm9, Gmaj9, Asus2(add E)
CHORDS = [
    [146.83, 220.00, 277.18, 329.63, 369.99],
    [123.47, 185.00, 220.00, 277.18, 293.66],
    [98.00, 146.83, 185.00, 220.00, 246.94],
    [110.00, 164.81, 246.94, 277.18, 329.63],
]
CHORD_LEN = 9.0     # seconds per chord
XFADE = 4.5         # crossfade between chords


def _voice(freq, n, t, rng, detune_cents):
    out = np.zeros((2, n), dtype=np.float32)
    for ch, sign in enumerate((-1, 1)):
        f = freq * 2 ** (sign * detune_cents / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        trem = 1 + 0.18 * np.sin(2 * np.pi * rng.uniform(0.05, 0.12) * t + rng.uniform(0, 6.28))
        s = np.sin(2 * np.pi * f * t + ph) + 0.22 * np.sin(4 * np.pi * f * t + 2 * ph) + 0.06 * np.sin(6 * np.pi * f * t + 3 * ph)
        out[ch] = (s * trem).astype(np.float32)
    return out


def pad(duration, seed=3):
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    mix = np.zeros((2, n), dtype=np.float32)
    k = 0
    start = 0.0
    while start < duration:
        notes = CHORDS[k % len(CHORDS)]
        seg_len = CHORD_LEN + XFADE
        a = int(start * SR)
        b = min(n, int((start + seg_len) * SR))
        if b <= a:
            break
        t = np.arange(b - a) / SR
        env = np.ones_like(t)
        fa = int(XFADE * SR)
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, min(fa, len(t))))
        env[: len(ramp)] = ramp
        env[-len(ramp):] = np.minimum(env[-len(ramp):], ramp[::-1])
        seg = np.zeros((2, b - a), dtype=np.float32)
        for i, f in enumerate(notes):
            seg += _voice(f, b - a, t, rng, detune_cents=3 + 2 * i) * (0.9 if i else 0.75) / len(notes)
        # sub drone one octave below the chord root
        root = notes[0] / 2
        seg += 0.35 * np.sin(2 * np.pi * root * t)[None, :].astype(np.float32)
        # airy upper voice: the top two chord tones an octave up, slow swell
        for j, f in enumerate(notes[-2:]):
            sw = 0.5 - 0.5 * np.cos(2 * np.pi * t / (seg_len * (1.0 + 0.37 * j)))
            seg += (0.10 * sw * np.sin(2 * np.pi * 2 * f * t + j))[None, :].astype(np.float32)
        mix[:, a:b] += seg * env[None, :]
        start += CHORD_LEN
        k += 1
    # warm it up: gentle low-pass
    bl, al = signal.butter(2, 2400 / (SR / 2), btype="low")
    mix = signal.lfilter(bl, al, mix, axis=1).astype(np.float32)
    # synthetic stereo reverb (exponentially decaying noise, RT60 ~ 3.2 s)
    ir_len = int(3.2 * SR)
    tt = np.arange(ir_len) / SR
    decay = np.exp(-6.9 * tt / 3.2)
    ir = np.stack([rng.standard_normal(ir_len) * decay, rng.standard_normal(ir_len) * decay]).astype(np.float32)
    bh, ah = signal.butter(1, 4500 / (SR / 2), btype="low")
    ir = signal.lfilter(bh, ah, ir, axis=1)
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    wet = np.stack([signal.oaconvolve(mix[c], ir[c])[:n] for c in range(2)]).astype(np.float32)
    out = 0.65 * mix + 0.55 * wet
    return out / (np.max(np.abs(out)) + 1e-9)


def whoosh(length=1.1, seed=0):
    """Band-passed noise sweep with a soft swell — used under chapter cards."""
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, dtype=np.float32)
    hop = 512
    zi = None
    for i in range(0, n, hop):
        frac = i / n
        fc = 250 * (14 ** frac)  # 250 Hz -> 3.5 kHz
        b, a = signal.butter(2, [fc * 0.7 / (SR / 2), min(0.99, fc * 1.4 / (SR / 2))], btype="band")
        chunk = noise[i:i + hop]
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, chunk, zi=zi)
        out[i:i + hop] = y
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2.2
    out *= env
    out /= np.max(np.abs(out)) + 1e-9
    pan = np.linspace(-0.6, 0.6, n)
    return np.stack([out * (1 - pan) / 2 * 2, out * (1 + pan) / 2 * 2]) * 0.5


def duck_gain(narration, depth_db=-8.0, attack=0.06, release=0.7):
    """Sidechain gain curve from the narration envelope (mono, SR)."""
    win = int(0.03 * SR)
    env = np.sqrt(signal.oaconvolve(narration.astype(np.float64) ** 2, np.ones(win) / win, mode="same").clip(0))
    thr = 0.02 * (np.max(env) + 1e-9)
    active = (env > thr).astype(np.float64)
    # asymmetric smoothing (attack / release) on a decimated grid for speed
    dec = 240
    a_s = active[::dec]
    g = np.zeros_like(a_s)
    ka = np.exp(-dec / (attack * SR))
    kr = np.exp(-dec / (release * SR))
    y = 0.0
    for i, x in enumerate(a_s):
        k = ka if x > y else kr
        y = k * y + (1 - k) * x
        g[i] = y
    g = np.interp(np.arange(len(narration)), np.arange(len(g)) * dec, g)
    return 10 ** (depth_db * g / 20)
