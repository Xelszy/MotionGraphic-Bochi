"""Render driver.
  python render.py --beats 4,4.5,5            stills -> build/stills/
  python render.py --sheet 0:20:0.5 --name a  contact sheets -> out/sheet_a*.jpg
  python render.py --compare 4:20:1 --name a  ours|reference pairs -> out/compare_a*.jpg
  python render.py --full --fps 60            native 60fps VHS/CRT -> build/CLARITY_iXelszy_vhs.mp4
"""
from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import os
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "out")
_REF = None


def _init(fps=30):
    cv2.setNumThreads(1)
    import engine
    engine.load(fps)


def _frame(fi):
    import engine
    return engine.frame(fi)


def _job(args):
    fi, tag = args
    t0 = time.perf_counter()
    img = _frame(fi)
    return fi, tag, img[..., :3].copy(), time.perf_counter() - t0


def _frame_bytes(fi):
    return _frame(fi).tobytes()


def beat_frames(spec):
    from core import b2f
    out = []
    for part in spec.split(","):
        a, b, s = (float(v) for v in part.split(":"))
        x = a
        while x < b - 1e-9:
            out.append(int(round(b2f(x))))
            x += s
    return out


def ref_time(bt):
    if bt < 4:
        return 0.87 * max(0.0, bt) / 4
    if bt < 44:
        return (bt - 3) * 0.75
    return 30.8 + (bt - 44) / 2.098


def ref_frame(t):
    global _REF
    if _REF is None:
        cap = cv2.VideoCapture(os.path.join(ROOT, "reference", "ref.mp4"))
        _REF = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            _REF.append(f)
    return _REF[max(0, min(len(_REF) - 1, int(round(t * 30))))]


def run(frames, workers):
    jobs = [(fi, k) for k, fi in enumerate(frames)]
    res = [None] * len(jobs)
    times = []
    with mp.Pool(min(workers, len(jobs)), initializer=_init) as pool:
        for fi, k, img, dt in pool.imap_unordered(_job, jobs):
            res[k] = img
            times.append(dt)
    print(f"{len(jobs)} frames  mean {np.mean(times) * 1000:.0f} ms  max {np.max(times) * 1000:.0f} ms", flush=True)
    return res


def sheet(frames, workers, name, compare=False, cols=None):
    from core import f2b
    imgs = run(frames, workers)
    tw, th = 384, 198
    cols = cols or (3 if compare else 5)
    cw = tw * (2 if compare else 1) + (6 if compare else 0)
    rows = math.ceil(len(frames) / cols)
    canvas = np.full((rows * (th + 22), cols * cw, 3), 24, np.uint8)
    for k, (fi, im) in enumerate(zip(frames, imgs)):
        r, c = divmod(k, cols)
        y, x = r * (th + 22), c * cw
        canvas[y:y + th, x:x + tw] = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
        bt = f2b(fi)
        lab = f"b{bt:.2f} f{fi}"
        if compare:
            t = ref_time(bt)
            canvas[y:y + th, x + tw:x + 2 * tw] = cv2.resize(ref_frame(t), (tw, th), interpolation=cv2.INTER_AREA)
            lab += f"  | ref {t:.2f}s"
        cv2.putText(canvas, lab, (x + 6, y + th + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 255, 170), 1, cv2.LINE_AA)
    os.makedirs(OUT, exist_ok=True)
    base = f"{'compare' if compare else 'sheet'}_{name}"
    rh, per = th + 22, 4
    parts = math.ceil(rows / per)
    for i in range(parts):
        p = os.path.join(OUT, f"{base}{'' if parts == 1 else '_' + str(i)}.jpg")
        cv2.imwrite(p, canvas[i * per * rh:(i + 1) * per * rh], [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("->", p)


def stills(beats, workers):
    from core import b2f
    d = os.path.join(BUILD, "stills")
    os.makedirs(d, exist_ok=True)
    frames = [int(round(b2f(v))) for v in beats]
    for fi, im, bt in zip(frames, run(frames, workers), beats):
        cv2.imwrite(os.path.join(d, f"b{bt:06.2f}.png"), im)
    print("->", d)


def audio():
    import imageio_ffmpeg
    from core import NFRAMES, FPS
    os.makedirs(BUILD, exist_ok=True)
    wav = os.path.join(BUILD, "audio.wav")
    dur = NFRAMES / FPS
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-i", os.path.join(ROOT, "audio", "song.mp3"), "-t", f"{dur:.4f}",
           "-af", f"afade=t=out:st={dur - 0.47:.3f}:d=0.45", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", wav]
    subprocess.run(cmd, check=True)
    return wav


def full(workers, crf, name, fps=60):
    import imageio_ffmpeg
    from core import W, H, FPS, NFRAMES
    count = round(NFRAMES * fps / FPS)
    wav = audio()
    out = os.path.join(BUILD, name)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-i", wav, "-map", "0:v:0", "-map", "1:a:0",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"
                  "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-tune", "animation",
           "-profile:v", "high", "-g", str(fps * 2), "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-color_range", "tv",
           "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sem = threading.Semaphore(workers * 2)

    def gen():
        for fi in range(count):
            sem.acquire()
            yield fi * FPS / fps

    t0 = time.perf_counter()
    with mp.Pool(workers, initializer=_init, initargs=(fps,)) as pool:
        for k, buf in enumerate(pool.imap(_frame_bytes, gen(), chunksize=1)):
            proc.stdin.write(buf)
            sem.release()
            if (k + 1) % 100 == 0 or k + 1 == count:
                el = time.perf_counter() - t0
                print(f"{k + 1:4d}/{count}  {el:6.1f}s  eta {el / (k + 1) * (count - k - 1):5.1f}s", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    print(f"ffmpeg exit {rc} -> {out}")
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats")
    ap.add_argument("--sheet")
    ap.add_argument("--compare")
    ap.add_argument("--name", default="x")
    ap.add_argument("--cols", type=int)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--out", default="CLARITY_iXelszy_vhs.mp4")
    ap.add_argument("--fps", type=int, choices=(30, 60), default=60,
                    help="Native animation samples per second; beat timing stays unchanged")
    a = ap.parse_args()
    if a.beats:
        stills([float(v) for v in a.beats.split(",")], a.workers)
    if a.sheet:
        sheet(beat_frames(a.sheet), a.workers, a.name, cols=a.cols)
    if a.compare:
        sheet(beat_frames(a.compare), a.workers, a.name, compare=True, cols=a.cols)
    if a.full:
        sys.exit(full(a.workers, a.crf, a.out, a.fps))
