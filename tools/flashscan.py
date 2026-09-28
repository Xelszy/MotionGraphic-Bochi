"""Photosensitivity indicator scan for the rendered MP4 (not a certified Harding/PEAT test).

  .venv\\Scripts\\python.exe tools\\flashscan.py [path.mp4] [--top N]

Methods (all: a flash = pair of opposing transitions; fail = more than 3 flashes, i.e. >= 7
transitions, inside any 1 s window):
  gen32   WCAG-style general flash: 32 px blocks, relative-luminance transitions >= 0.1 with the darker
          side < 0.8, dominant-direction concurrent area > 25 % of a 10-degree window (1/3 x 1/3 screen).
  red32   same, WCAG red flash: saturated red (R/(R+G+B) >= 0.8, linear) metric (R-G-B)*320, delta >= 20.
  mean    region-mean luminance (Ofcom-like): mean of each 10-degree window / full frame swings >= 0.1.
  gen8    strict 8 px variant of gen32 (reacts to TV static / fast motion; informational).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS, AREA = 30, 0.25
_g = np.arange(256) / 255.0
LUT = np.where(_g <= 0.04045, _g / 12.92, ((_g + 0.055) / 1.055) ** 2.4).astype(np.float32)


def f2b(fi):
    return (fi * 30 / FPS - 5) / 20


def decode(mp4, w, h):
    cmd = [FF, "-v", "error", "-i", mp4, "-map", "0:v:0", "-fps_mode", "passthrough",
           "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=bgr24", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = w * h * 3
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        p.stdout.close()
        p.wait()


def grids(mp4, gw=160, gh=82):
    tag = os.path.splitext(os.path.basename(mp4))[0]
    cache = os.path.join(ROOT, "out", f"flash_cache_{tag}.npz")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(mp4):
        z = np.load(cache)
        return z["lum"], z["red"]
    r = subprocess.run([FF, "-hide_banner", "-i", mp4], capture_output=True, text=True, errors="replace").stderr
    import re
    w, h = (int(v) for v in re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", r).groups())
    lum, red = [], []
    for f in decode(mp4, w, h):
        b, g, rr = LUT[f[..., 0]], LUT[f[..., 1]], LUT[f[..., 2]]
        L = rr * 0.2126 + g * 0.7152 + b * 0.0722
        s = rr + g + b
        R = np.where((rr >= 0.8 * s) & (s > 1e-6), np.maximum(0.0, (rr - g - b) * 320.0), 0.0).astype(np.float32)
        lum.append(cv2.resize(L, (gw, gh), interpolation=cv2.INTER_AREA))
        red.append(cv2.resize(R, (gw, gh), interpolation=cv2.INTER_AREA))
    lum, red = np.stack(lum), np.stack(red)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez(cache, lum=lum, red=red)
    return lum, red


def zig_events(X, th, dark_max):
    """Per-cell zig-zag.  Returns int8 (T, ...) with +1/-1 at the frame each qualifying transition peaked."""
    T = X.shape[0]
    ev = np.zeros(X.shape, np.int8)
    shp = X.shape[1:]
    idx = np.indices(shp)
    d = np.zeros(shp, np.int8)
    t = np.zeros(shp, np.int32)
    lo, hi, piv, ext = X[0].copy(), X[0].copy(), X[0].copy(), X[0].copy()

    def emit(m, s):
        m = m & (np.minimum(piv, ext) < dark_max)
        ev[(t[m],) + tuple(i[m] for i in idx)] = s

    for fi in range(1, T):
        L = X[fi]
        m0 = d == 0
        np.minimum(lo, L, out=lo)
        np.maximum(hi, L, out=hi)
        up = m0 & (L - lo >= th)
        dn = m0 & ~up & (hi - L >= th)
        piv[up], piv[dn] = lo[up], hi[dn]
        d[up], d[dn] = 1, -1
        new = up | dn
        ext[new], t[new] = L[new], fi
        for s in (1, -1):
            m = (d == s) & ~new
            g = m & ((L - ext) * s > 0)
            ext[g], t[g] = L[g], fi
            rv = m & ((ext - L) * s >= th)
            emit(rv, s)
            piv[rv], ext[rv], t[rv] = ext[rv], L[rv], fi
            d[rv] = -s
            new |= rv
    for s in (1, -1):
        emit(d == s, s)
    return ev


def windows(gh, gw):
    cw, ch = max(1, gw // 3), max(1, gh // 3)
    out = {"full": (slice(0, gh), slice(0, gw))}
    for y in range(0, gh - ch + 1, max(1, ch // 2)):
        for x in range(0, gw - cw + 1, max(1, cw // 2)):
            out[f"x{x / gw:.2f}_y{y / gh:.2f}"] = (slice(y, y + ch), slice(x, x + cw))
    return out


def count(trs, T):
    """trs: sorted transition frames -> per-start-frame count in [t, t+FPS)."""
    trs = np.asarray(trs, int)
    a = np.arange(T)
    return np.searchsorted(trs, a + FPS) - np.searchsorted(trs, a)


def area_method(X, th, dark_max):
    T, gh, gw = X.shape
    ev = zig_events(X, th, dark_max)
    res = {}
    for name, (sy, sx) in windows(gh, gw).items():
        e = ev[:, sy, sx].reshape(T, -1)
        ar = []
        for s in (1, -1):
            m = e == s
            m[1:] |= m[:-1].copy()
            ar.append(m.mean(1))
        up, dn = ar
        trs, last = [], 0
        for t in range(T):
            for s, a, o in ((1, up[t], dn[t]), (-1, dn[t], up[t])):
                if a > AREA and a >= o and last != s:
                    trs.append((t, s, round(float(a), 2)))
                    last = s
        res[name] = trs
    return res


def zig_1d(x, th, dark_max):
    trs, d, lo, hi, piv, ext, te = [], 0, x[0], x[0], x[0], x[0], 0
    for t in range(1, len(x)):
        v = x[t]
        if d == 0:
            lo, hi = min(lo, v), max(hi, v)
            if v - lo >= th:
                d, piv, ext, te = 1, lo, v, t
            elif hi - v >= th:
                d, piv, ext, te = -1, hi, v, t
            continue
        if (v - ext) * d > 0:
            ext, te = v, t
        elif (ext - v) * d >= th:
            if min(piv, ext) < dark_max:
                trs.append((te, d, round(float(abs(ext - piv)), 3)))
            piv, ext, te, d = ext, v, t, -d
    if d and min(piv, ext) < dark_max:
        trs.append((te, d, round(float(abs(ext - piv)), 3)))
    return trs


def mean_method(X, th, dark_max):
    T, gh, gw = X.shape
    return {name: zig_1d(X[:, sy, sx].reshape(T, -1).mean(1), th, dark_max)
            for name, (sy, sx) in windows(gh, gw).items()}


def summarize(res, T):
    bad = np.zeros(T, bool)
    worst, wname, wt = 0, None, 0
    for name, trs in res.items():
        c = count([t for t, _, _ in trs], T)
        for t0 in np.nonzero(c >= 7)[0]:
            bad[t0:t0 + FPS] = True
        if c.max(initial=0) > worst:
            worst, wname, wt = int(c.max()), name, int(np.argmax(c))
    ranges, t = [], 0
    while t < T:
        if bad[t]:
            u = t
            while u < T and bad[u]:
                u += 1
            ranges.append({"s": [round(t / FPS, 2), round(u / FPS, 2)], "beats": [round(f2b(t), 2), round(f2b(u), 2)]})
            t = u
        t += 1
    detail = [(t, round(f2b(t), 2), s, a) for t, s, a in res.get(wname, []) if wt <= t < wt + FPS] if wname else []
    for rg in ranges:
        a, b = int(round(rg["s"][0] * FPS)), int(round(rg["s"][1] * FPS))
        name, trs = max(res.items(), key=lambda kv: sum(a <= t < b for t, _, _ in kv[1]))
        rg["region"] = name
        rg["tr"] = [(t, round(f2b(t), 2), s, amt) for t, s, amt in trs if a <= t < b][:24]
    return {"worst_transitions_per_s": worst, "worst_flashes_per_s": worst / 2, "worst_region": wname,
            "worst_at": {"frame": wt, "s": round(wt / FPS, 2), "beat": round(f2b(wt), 2)},
            "worst_window_transitions(frame,beat,sign,amount)": detail,
            "fail_seconds": round(float(bad.sum()) / FPS, 2), "fail_ranges": ranges, "pass": not bad.any()}


def scan(mp4):
    global FPS
    cap = cv2.VideoCapture(mp4)
    FPS = int(round(cap.get(cv2.CAP_PROP_FPS)))
    cap.release()
    if FPS <= 0:
        raise ValueError(f"Cannot read video frame rate: {mp4}")
    lum, red = grids(mp4)
    T = lum.shape[0]
    l32 = np.stack([cv2.resize(f, (40, 20), interpolation=cv2.INTER_AREA) for f in lum])
    r32 = np.stack([cv2.resize(f, (40, 20), interpolation=cv2.INTER_AREA) for f in red])
    res = {"gen32": area_method(l32, 0.1, 0.8), "red32": area_method(r32, 20.0, 1e9),
           "mean": mean_method(l32, 0.1, 0.8), "gen8": area_method(lum, 0.1, 0.8)}
    out = {"frames": T, "fps": FPS}
    for k, r in res.items():
        out[k] = summarize(r, T)
        out[k + "_full"] = summarize({"full": r["full"]}, T)
    return out


if __name__ == "__main__":
    mp4 = next((a for a in sys.argv[1:] if a.endswith(".mp4")), os.path.join(ROOT, "build", "CLARITY_iXelszy_vhs.mp4"))
    mp4 = os.path.abspath(mp4)
    rep = scan(mp4)
    tag = os.path.splitext(os.path.basename(mp4))[0]
    with open(os.path.join(ROOT, "out", f"flashscan_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(tag, rep["frames"], "frames")
    for k in ("gen32", "gen32_full", "red32", "mean", "mean_full", "gen8"):
        r = rep[k]
        print(f"  {k:10s} pass={r['pass']!s:5s} worst={r['worst_flashes_per_s']:.1f}/s @{r['worst_at']['s']}s "
              f"b{r['worst_at']['beat']} ({r['worst_region']})  fail_s={r['fail_seconds']:5.2f}  "
              f"ranges_s={[x['s'] for x in r['fail_ranges']]}")
    if "--detail" in sys.argv:
        for k in ("mean", "gen32"):
            for rg in rep[k]["fail_ranges"]:
                print(f"  [{k}] {rg['s']}s b{rg['beats']} {rg['region']}: " +
                      " ".join(f"{t}/b{bt}{'+' if s > 0 else '-'}{amt}" for t, bt, s, amt in rg["tr"]))
