#!/usr/bin/env python3
"""Build the Ethernet-APL vs. CAN explainer.

    python3 build.py render   -q h -j 4          # render all scenes (parallel)
    python3 build.py assemble -q h               # concat + narration + music + subtitles
    python3 build.py all      -q h -j 4

Scenes render with isolated media dirs (Manim's text cache is not safe for
concurrent writers).  Outputs land in ../output/.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import numpy as np
import soundfile as sf

VIDEO = Path(__file__).resolve().parent
ROOT = VIDEO.parent
BUILD = ROOT / "build"
OUT = ROOT / "output"
sys.path.insert(0, str(VIDEO))

SCENES = [
    ("s00_cold_open", "ColdOpen"),
    ("s01_four_walls", "FourWalls"),
    ("s02_what_is_apl", "WhatIsAPL"),
    ("s03_can_physical", "CANPhysical"),
    ("s04_can_arbitration", "CANArbitration"),
    ("s05_can_length", "CANLength"),
    ("s06_apl_topology", "APLTopology"),
    ("s07_full_duplex", "FullDuplex"),
    ("s08_pam3", "PAM3"),
    ("s09_power_data", "PowerData"),
    ("s10_intrinsic_safety", "IntrinsicSafety"),
    ("s11_head_to_head", "HeadToHead"),
    ("s12_outro", "Outro"),
]
QUALITY = {"l": ("-ql", "480p15"), "m": ("-qm", "720p30"), "h": ("-qh", "1080p60"), "k": ("-qk", "2160p60")}
TITLE = "Ethernet-APL, explained — and how it differs from CAN bus"
STEM = "Ethernet-APL_vs_CAN-bus"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe_video(path: Path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
             "-of", "csv=p=0", str(path)])
    w, h, fps = r.stdout.strip().split(",")
    return int(w), int(h), fps


def probe_duration(path: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


# ---------------------------------------------------------------- render
def render_one(idx, file, scene, q, retries=1):
    flag, folder = QUALITY[q]
    media = BUILD / f"media_{q}" / file
    logs = BUILD / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    out = media / "videos" / file / folder / f"{scene}.mp4"
    dst = BUILD / f"scenes_{q}" / f"{idx:02d}_{scene}.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for attempt in range(retries + 1):
        r = subprocess.run(["manim", flag, "--media_dir", str(media), f"scenes/{file}.py", scene],
                           cwd=VIDEO, capture_output=True, text=True)
        (logs / f"{q}_{file}.log").write_text(r.stdout + r.stderr)
        if r.returncode == 0 and out.exists():
            shutil.copy2(out, dst)
            cue = BUILD / "cues" / f"{scene}.json"
            if cue.exists():
                shutil.copy2(cue, BUILD / f"scenes_{q}" / f"{idx:02d}_{scene}.json")
            return scene, time.time() - t0
        print(f"  ! {scene} failed (attempt {attempt + 1}), see logs/{q}_{file}.log", flush=True)
    raise RuntimeError(f"render failed: {scene}")


def cmd_render(args):
    sel = [(i, f, s) for i, (f, s) in enumerate(SCENES) if not args.scenes or s in args.scenes or f in args.scenes]
    # longest first for better packing on the worker pool
    weight = {"HeadToHead": 9, "FourWalls": 8, "IntrinsicSafety": 8, "CANArbitration": 7, "WhatIsAPL": 7}
    sel.sort(key=lambda x: -weight.get(x[2], 5))
    print(f"rendering {len(sel)} scenes at {QUALITY[args.quality][1]} with {args.jobs} workers", flush=True)
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(render_one, i, f, s, args.quality): s for i, f, s in sel}
        for fut in cf.as_completed(futs):
            scene, dt = fut.result()
            print(f"  ✓ {scene:16s} {dt / 60:5.1f} min", flush=True)


# ---------------------------------------------------------------- subtitles
def wrap_cue(text, width=42):
    """Split a sentence into subtitle chunks of at most two lines, at natural breaks."""
    limit = 2 * width
    if len(text) <= limit:
        return [text]
    words = text.split()
    best, best_score = None, None
    pos = 0
    for i in range(1, len(words)):
        left, right = " ".join(words[:i]), " ".join(words[i:])
        prev = words[i - 1]
        bonus = 0
        if prev.endswith((",", ";", ":")):
            bonus = 42
        elif prev in ("—", "–") or words[i] in ("—", "–"):
            bonus = 48
        elif words[i].lower() in ("and", "but", "so", "which", "while", "where", "with", "to", "that"):
            bonus = 15
        balance = -abs(len(left) - len(right))
        over = -1000 if max(len(left), len(right)) > limit and len(text) <= 2 * limit else 0
        score = balance + bonus + over
        if best_score is None or score > best_score:
            best, best_score = i, score
    left, right = " ".join(words[:best]), " ".join(words[best:])
    return wrap_cue(left, width) + wrap_cue(right, width)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(cues):
    out, n = [], 1
    for c in cues:
        parts = wrap_cue(c["text"])
        total = sum(len(p) for p in parts)
        t = c["start"]
        for p in parts:
            dur = (c["end"] - c["start"]) * len(p) / total
            body = "\n".join(textwrap.wrap(p, width=42))
            out.append(f"{n}\n{srt_time(t)} --> {srt_time(t + dur)}\n{body}\n")
            n += 1
            t += dur
    return "\n".join(out)


# ---------------------------------------------------------------- assemble
def cmd_assemble(args):
    from audio.music import SR, duck_gain, pad, whoosh

    q = args.quality
    sdir = BUILD / f"scenes_{q}"
    adir = BUILD / f"assembly_{q}"
    adir.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    files = [sdir / f"{i:02d}_{s}.mp4" for i, (_, s) in enumerate(SCENES)]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        sys.exit(f"missing renders: {missing}")
    durs = [probe_duration(f) for f in files]
    offsets = np.concatenate([[0], np.cumsum(durs)[:-1]])
    total = float(sum(durs))
    print(f"total duration {total / 60:.2f} min", flush=True)

    # 1) video track: lossless concat of identically-encoded segments
    lst = adir / "concat.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    video_only = adir / "video_only.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-an", "-c", "copy", str(video_only)])

    # 2) narration track: each scene's audio padded to its exact video length
    narr = np.zeros(int(round(total * SR)) + SR, dtype=np.float32)
    for f, off, d in zip(files, offsets, durs):
        wav = adir / (f.stem + ".wav")
        try:
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", str(SR), str(wav)])
            a, _ = sf.read(wav, dtype="float32")
        except subprocess.CalledProcessError:
            a = np.zeros(1, dtype=np.float32)
        a = a[: int(d * SR)]
        i0 = int(round(off * SR))
        narr[i0:i0 + len(a)] += a
    narr = narr[: int(round(total * SR))]

    # 3) cues & chapters
    cues, chapters = [], []
    for (_, s), off in zip(SCENES, offsets):
        j = json.loads((BUILD / "cues" / f"{s}.json").read_text())
        cues += [{"start": c["start"] + off, "end": c["end"] + off, "text": c["text"]} for c in j["cues"]]
        chapters += [{"time": c["time"] + off, "title": c["title"]} for c in j.get("chapters", [])]
    chapters.sort(key=lambda c: c["time"])

    # 4) music bed, ducked under the voice, plus whooshes under chapter cards
    n = len(narr)
    if args.no_music:
        bed = np.zeros((2, n), dtype=np.float32)
    else:
        bed = pad(total + 0.5)[:, :n]
        voice_rms = np.sqrt(np.mean(narr[np.abs(narr) > 0.01] ** 2)) if np.any(np.abs(narr) > 0.01) else 0.1
        bed_rms = np.sqrt(np.mean(bed ** 2))
        bed *= (voice_rms * 10 ** (-17 / 20)) / (bed_rms + 1e-9)   # bed sits ~17 dB under the voice
        bed *= duck_gain(narr, depth_db=-7.0)[None, :].astype(np.float32)
        fade_in, fade_out = int(3 * SR), int(6 * SR)
        bed[:, :fade_in] *= np.linspace(0, 1, fade_in)[None, :]
        bed[:, -fade_out:] *= np.linspace(1, 0, fade_out)[None, :] ** 1.5
        w = whoosh()
        for ch in chapters:
            if ch["time"] < 1.0:
                continue
            i0 = int((ch["time"] - 0.35) * SR)
            seg = w[:, : max(0, min(w.shape[1], n - i0))]
            bed[:, i0:i0 + seg.shape[1]] += seg * voice_rms * 10 ** (-20 / 20) / (np.sqrt(np.mean(w ** 2)) + 1e-9) * 0.35
    def normalise(stereo, name):
        """EBU R128 two-pass loudness normalisation to -16 LUFS / -1.5 dBTP."""
        raw = adir / f"{name}.wav"
        sf.write(raw, stereo.T, SR, subtype="FLOAT")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True)
        m = json.loads(r.stderr[r.stderr.rfind("{"): r.stderr.rfind("}") + 1])
        out = adir / f"{name}_norm.wav"
        af = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
              "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**m)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", af, "-ar", str(SR), str(out)])
        return out

    voice_only = normalise(narr[None, :], "mix_voice")          # mono: no downmix gain surprises
    norm_wav = voice_only if args.no_music else normalise(np.stack([narr, narr]) + bed, "mix_music")

    # 6) subtitles, chapters, transcript
    srt = OUT / f"{STEM}.srt"
    srt.write_text(build_srt(cues))
    meta = adir / "chapters.txt"
    lines = [";FFMETADATA1", f"title={TITLE}", "artist=Ethernet-APL explainer", ""]
    for i, ch in enumerate(chapters):
        end = chapters[i + 1]["time"] if i + 1 < len(chapters) else total
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(ch['time'] * 1000)}", f"END={int(end * 1000)}", f"title={ch['title']}", ""]
    meta.write_text("\n".join(lines))
    write_transcript(cues, chapters)

    # 7) mux (+ backdrop glow blended with "lighten", which forces a re-encode)
    suffix = "_voice-only" if args.no_music else ""
    final = OUT / f"{STEM}{suffix}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_only), "-i", str(norm_wav), "-i", str(srt), "-i", str(meta)]
    from apl.backdrop import make as make_backdrop
    w, h, fps = probe_video(video_only)
    cmd += ["-loop", "1", "-framerate", fps, "-i", str(make_backdrop(w, h)), "-i", str(voice_only)]
    if args.backdrop:
        cmd += ["-filter_complex", "[0:v]format=gbrp[a];[4:v]format=gbrp[b];[a][b]blend=all_mode=lighten:shortest=1,format=yuv420p[v]",
                "-map", "[v]"]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-map", "1:a"]
    if not args.no_music:
        cmd += ["-map", "5:a"]
    cmd += ["-map", "2:s", "-map_metadata", "3", "-map_chapters", "3"]
    track0 = "Narration only" if args.no_music else "Narration + music"
    if args.reencode or args.backdrop:
        cmd += ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf), "-tune", "animation", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart"]
    else:
        cmd += ["-c:v", "copy", "-movflags", "+faststart"]
    cmd += ["-c:a", "aac", "-b:a:0", "160k", "-b:a:1", "96k", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
            "-metadata:s:a:0", "language=eng", "-metadata:s:a:0", f"title={track0}",
            "-metadata:s:a:0", f"handler_name={track0}", "-metadata:s:s:0", "handler_name=English", "-disposition:s:0", "0",
            "-disposition:a:0", "default"]
    if not args.no_music:
        cmd += ["-metadata:s:a:1", "language=eng", "-metadata:s:a:1", "title=Narration only",
                "-metadata:s:a:1", "handler_name=Narration only", "-disposition:a:1", "0"]
    cmd += ["-shortest", str(final)]
    run(cmd)
    size = final.stat().st_size / 1e6
    print(f"wrote {final} ({size:.1f} MB), {srt.name}", flush=True)


def write_transcript(cues, chapters):
    doc = ROOT / "docs" / "transcript.md"
    out = [f"# Transcript — {TITLE}", "", "_Generated from the narration that is rendered into the video._", ""]
    ci = 0
    para = []
    prev_end = None
    for c in cues:
        if para and prev_end is not None and c["start"] - prev_end > 0.9:
            out += [" ".join(para), ""]
            para = []
        prev_end = c["end"]
        while ci < len(chapters) and chapters[ci]["time"] <= c["start"] + 0.01:
            if para:
                out += [" ".join(para), ""]
                para = []
            m, s = divmod(int(chapters[ci]["time"]), 60)
            out += [f"## {chapters[ci]['title']}  `{m:02d}:{s:02d}`", ""]
            ci += 1
        para.append(c["text"])
    if para:
        out += [" ".join(para), ""]
    doc.write_text("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "assemble", "all"])
    ap.add_argument("-q", "--quality", default="h", choices=list(QUALITY))
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--scenes", nargs="*")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--reencode", action="store_true", help="final x264 encode instead of stream copy")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--no-backdrop", dest="backdrop", action="store_false")
    args = ap.parse_args()
    if args.cmd in ("render", "all"):
        cmd_render(args)
    if args.cmd in ("assemble", "all"):
        cmd_assemble(args)


if __name__ == "__main__":
    main()
