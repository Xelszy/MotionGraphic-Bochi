"""Verify the final MP4: streams, frame count, A/V sync, beat/cut alignment, pixel match, flash scan.

  .venv\\Scripts\\python.exe tools\\verify.py [path.mp4]

Writes out/verify.json and out/verify_sheet.jpg (contact sheet decoded from the MP4 itself).
Flash scan = simplified WCAG 2.x general-flash check: relative-luminance transitions >= 0.1 with the
darker side < 0.8, concurrent over > 25 % of a 1/3 x 1/2-screen window (overlapping grid) or the full
frame, more than 3 flashes (>= 7 transitions) in any 1 s.  An indicator only, not a certified test.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

import cv2
import imageio_ffmpeg
import numpy as np
from scipy import signal

MP4 = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from core import FPS as AUTHOR_FPS, H, NFRAMES as AUTHOR_FRAMES, W  # noqa: E402

MP4 = MP4 or os.path.join(ROOT, "build", "CLARITY_iXelszy_vhs.mp4")
_cap = cv2.VideoCapture(MP4)
FPS = int(round(_cap.get(cv2.CAP_PROP_FPS)))
_cap.release()
if FPS not in (30, 60):
    raise ValueError(f"Expected a 30/60 fps render, got {FPS}: {MP4}")
RATE = FPS / AUTHOR_FPS
NFRAMES = round(AUTHOR_FRAMES * RATE)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SONG = os.path.join(ROOT, "audio", "song.mp3")
OUT = os.path.join(ROOT, "out")
SR, GW, GH = 48000, 160, 82
BEAT_S, PHASE_S = 2 / 3, 1 / 6
AREA, FLASH_TH, DARK_MAX = 0.25, 0.1, 0.8
MATCH = [round(fi * RATE) for fi in [0, 90, 300, 455, 700, 905, 1100, 1250, 1345]]
SHEET = [round(fi * RATE) for fi in range(15, AUTHOR_FRAMES, 40)] + [NFRAMES - 1]
_g = np.arange(256) / 255.0
LUT = np.where(_g <= 0.04045, _g / 12.92, ((_g + 0.055) / 1.055) ** 2.4).astype(np.float32)


def probe():
    r = subprocess.run([FF, "-hide_banner", "-i", MP4], capture_output=True, text=True, errors="replace")
    return [ln.strip() for ln in r.stderr.splitlines() if ln.strip().startswith(("Duration", "Stream"))]


def pcm(path, dur=None):
    cmd = [FF, "-v", "error", "-i", path] + (["-t", f"{dur:.3f}"] if dur else []) + \
          ["-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()


def frames():
    cmd = [FF, "-v", "error", "-i", MP4, "-map", "0:v:0", "-fps_mode", "passthrough",
           "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=bgr24", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * H * 3
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    finally:
        p.stdout.close()
        p.wait()


def rel_lum(bgr):
    lin = LUT[bgr]
    return lin[..., 2] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 0] * 0.0722


class Zig:
    """Per-pixel zig-zag of luminance; records each transition >= TH at the frame its extreme was reached."""

    def __init__(self, shape, T):
        self.ev = np.zeros((T,) + shape, np.int8)
        self.d = np.zeros(shape, np.int8)
        self.t = np.zeros(shape, np.int32)
        self.yx = np.indices(shape)
        self.lo = self.hi = self.piv = self.ext = None

    def _emit(self, m, s):
        m = m & (np.minimum(self.piv, self.ext) < DARK_MAX)
        self.ev[self.t[m], self.yx[0][m], self.yx[1][m]] = s

    def step(self, fi, L):
        if self.piv is None:
            self.lo, self.hi, self.piv, self.ext = L.copy(), L.copy(), L.copy(), L.copy()
            return
        d = self.d
        m0 = d == 0
        np.minimum(self.lo, L, out=self.lo)
        np.maximum(self.hi, L, out=self.hi)
        up = m0 & (L - self.lo >= FLASH_TH)
        dn = m0 & ~up & (self.hi - L >= FLASH_TH)
        self.piv[up], self.piv[dn] = self.lo[up], self.hi[dn]
        d[up], d[dn] = 1, -1
        new = up | dn
        self.ext[new], self.t[new] = L[new], fi
        for s in (1, -1):
            m = (d == s) & ~new
            g = m & ((L - self.ext) * s > 0)
            self.ext[g], self.t[g] = L[g], fi
            rv = m & ((self.ext - L) * s >= FLASH_TH)
            self._emit(rv, s)
            self.piv[rv], self.ext[rv], self.t[rv] = self.ext[rv], L[rv], fi
            d[rv] = -s
            new |= rv

    def flush(self):
        for s in (1, -1):
            self._emit(self.d == s, s)


def flash_scan(ev):
    T = ev.shape[0]
    cw, ch = GW // 3, GH // 2
    regions = {"full": (slice(0, GH), slice(0, GW))}
    for y in range(0, GH - ch + 1, ch // 2):
        for x in range(0, GW - cw + 1, cw // 2):
            regions[f"win_x{x * W // GW}_y{y * H // GH}"] = (slice(y, y + ch), slice(x, x + cw))
    res, bad = {}, np.zeros(T, bool)
    for name, (sy, sx) in regions.items():
        e = ev[:, sy, sx].reshape(T, -1)
        areas = []
        for s in (1, -1):
            m = e == s
            m[1:] |= m[:-1].copy()
            areas.append(m.mean(1))
        tr, last = [], 0
        for t in range(T):
            for s, a in ((1, areas[0][t]), (-1, areas[1][t])):
                if a > AREA and last != s:
                    tr.append(t)
                    last = s
        tr = np.array(tr, int)
        cnt = np.searchsorted(tr, np.arange(T) + FPS) - np.searchsorted(tr, np.arange(T))
        fail = cnt >= 7
        for t in np.nonzero(fail)[0]:
            bad[t:t + FPS] = True
        res[name] = {"transitions": int(len(tr)), "max_per_s": int(cnt.max(initial=0)),
                     "max_flashes_per_s": float(cnt.max(initial=0)) / 2, "fail_windows": int(fail.sum())}
    ranges, t = [], 0
    while t < T:
        if bad[t]:
            u = t
            while u < T and bad[u]:
                u += 1
            ranges.append([round(t / FPS, 2), round(u / FPS, 2),
                           round((t / RATE - 5) / 20, 2), round((u / RATE - 5) / 20, 2)])
            t = u
        t += 1
    worst = max(res.items(), key=lambda kv: kv[1]["max_per_s"])
    return {"worst_region": worst[0], "worst": worst[1], "fail_ranges_s_and_beats": ranges,
            "fail_seconds": round(float(bad.sum()) / FPS, 2), "regions": res}


def onset_env(a, hop=400, nfft=1024):
    win = np.hanning(nfft).astype(np.float32)
    pad = np.pad(a, (nfft // 2, nfft // 2))
    fr = np.lib.stride_tricks.sliding_window_view(pad, nfft)[::hop] * win
    lm = np.log1p(100 * np.abs(np.fft.rfft(fr, axis=1)))
    return np.r_[0, np.maximum(0, np.diff(lm, axis=0)).sum(1)], hop


def psnr(a, b):
    mse = float(np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2))
    return 99.0 if mse < 1e-9 else 10 * math.log10(255 ** 2 / mse)


def main():
    t0 = time.perf_counter()
    rep = {"file": MP4, "size_mb": round(os.path.getsize(MP4) / 2 ** 20, 2), "probe": probe()}

    keep = set(MATCH) | set(SHEET)
    kept, lum, cut = {}, [], []
    zig = Zig((GH, GW), NFRAMES + 120)
    prev, n = None, 0
    for fi, f in enumerate(frames()):
        if fi in keep:
            kept[fi] = f.copy()
        L = cv2.resize(rel_lum(f), (GW, GH), interpolation=cv2.INTER_AREA)
        zig.step(fi, L)
        lum.append(float(L.mean()))
        g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (GW, GH), interpolation=cv2.INTER_AREA).astype(np.int16)
        cut.append(0.0 if prev is None else float((np.abs(g - prev) > 40).mean()))
        prev, n = g, n + 1
    zig.flush()
    rep["frames_decoded"], rep["frames_expected"] = n, NFRAMES
    rep["video_s"] = round(n / FPS, 4)
    rep["last10_mean_lum"] = round(float(np.mean(lum[-10:])), 4)
    rep["decode_s"] = round(time.perf_counter() - t0, 1)

    cf = np.array(cut)
    peaks = [t for t in range(1, n) if cf[t] >= 0.3 and cf[t] == cf[max(0, t - 3):t + 4].max()]
    offs = [(round(t / RATE) % 10) - 5 for t in peaks]
    hist = {str(k): offs.count(k) for k in range(-5, 5)}
    rep["cuts"] = {"n": len(peaks), "offset_hist_vs_half_beat": hist,
                   "within_1_frame": round(sum(abs(o) <= 1 for o in offs) / max(1, len(offs)), 3),
                   "chance_within_1_frame": 0.3}

    a = pcm(MP4)
    s = pcm(SONG, len(a) / SR + 1.0)
    rep["audio_s"] = round(len(a) / SR, 4)
    rep["av_duration_diff_ms"] = round((len(a) / SR - n / FPS) * 1000, 1)
    lag = int(0.25 * SR)
    i0, i1 = int(2.0 * SR), int(12.0 * SR)
    x = a[i0:i1]
    c = signal.correlate(s[i0 - lag:i1 + lag], x, mode="valid", method="fft")
    k = int(np.argmax(c)) - lag
    ncc = float(c.max() / (np.linalg.norm(x) * np.linalg.norm(s[i0 + k:i1 + k]) + 1e-9))
    rep["av_lag_vs_song"] = {"lag_samples": k, "lag_ms": round(k / SR * 1000, 3), "ncc": round(ncc, 4)}
    env, hop = onset_env(a)
    per = int(round(BEAT_S * SR / hop))
    fold = env[:len(env) // per * per].reshape(-1, per).mean(0)
    ph = int(np.argmax(fold)) * hop / SR
    dev = (ph - PHASE_S + BEAT_S / 2) % BEAT_S - BEAT_S / 2
    rep["audio_beat_phase"] = {"measured_s": round(ph, 4), "grid_s": round(PHASE_S, 4),
                               "deviation_ms": round(dev * 1000, 1), "peak_over_mean": round(float(fold.max() / fold.mean()), 2)}
    tail = a[-int(0.05 * SR):]
    rep["audio_peak_dbfs"] = round(20 * math.log10(float(np.abs(a).max()) + 1e-12), 2)
    rep["audio_tail_rms_dbfs"] = round(20 * math.log10(float(np.sqrt(np.mean(tail ** 2))) + 1e-12), 1)

    rep["flash"] = flash_scan(zig.ev[:n])

    import engine
    engine.load(FPS)
    rows = []
    for fi in MATCH:
        if fi not in kept:
            continue
        row = {"frame": fi}
        for off in (-1, 0, 1):
            j = fi + off
            if 0 <= j < NFRAMES:
                row[f"psnr_vs_engine{off:+d}"] = round(psnr(kept[fi], engine.frame(j / RATE)[..., :3]), 2)
        rows.append(row)
    rep["pixel_match"] = rows

    tw, th, cols = 256, 132, 7
    nr = -(-len(SHEET) // cols)
    canvas = np.full((nr * (th + 18), cols * tw, 3), 24, np.uint8)
    for kk, fi in enumerate(SHEET):
        if fi not in kept:
            continue
        r, cc = divmod(kk, cols)
        y, xx = r * (th + 18), cc * tw
        canvas[y:y + th, xx:xx + tw] = cv2.resize(kept[fi], (tw, th), interpolation=cv2.INTER_AREA)
        cv2.putText(canvas, f"f{fi} b{(fi / RATE - 5) / 20:.2f} {fi / FPS:.2f}s", (xx + 4, y + th + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (140, 255, 170), 1, cv2.LINE_AA)
    os.makedirs(OUT, exist_ok=True)
    tag = os.path.splitext(os.path.basename(MP4))[0]
    cv2.imwrite(os.path.join(OUT, f"verify_{tag}_sheet.jpg"), canvas, [cv2.IMWRITE_JPEG_QUALITY, 88])
    rep["total_s"] = round(time.perf_counter() - t0, 1)
    with open(os.path.join(OUT, f"verify_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    short = {k: v for k, v in rep.items() if k != "flash"}
    short["flash"] = {k: v for k, v in rep["flash"].items() if k != "regions"}
    print(json.dumps(short, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
