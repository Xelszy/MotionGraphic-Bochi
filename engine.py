"""Timeline engine: shots + transitions + cut-edge fx + camera + grade -> final frame."""
from __future__ import annotations

import bisect
import math

import cv2
import numpy as np

import fx
import trans
from core import (W, H, CX, CY, FPS, SPB, FPB, END_B, NFRAMES, f2b, clamp, seg, pulse, hash01, hr, surface, lerp, smooth, vnoise)

SHUTTER = 0.5 / FPB  # half-frame shutter in beats


class Ctx:
    __slots__ = ("c", "arr", "b", "lb", "dur", "fi", "t", "p")

    def __init__(self, c, arr, b, lb, dur, fi):
        self.c, self.arr, self.b, self.lb, self.dur, self.fi = c, arr, b, lb, dur, fi
        self.t = lb * SPB
        self.p = lb / dur if dur > 0 else 0.0


SHOTS, TRANS, FXE, CAM = [], [], [], []
_starts = []


def load(output_fps=FPS):
    """Collect timeline from shot modules (safe to call repeatedly)."""
    global SHOTS, TRANS, FXE, CAM, _starts, SHUTTER
    SHUTTER = 0.5 * FPS / (FPB * output_fps)
    import shots_a
    import shots_b
    import shots_c
    S, T, F, C = [], [], [], []
    for m in (shots_a, shots_b, shots_c):
        S += m.SHOTS
        T += m.TRANS
        F += m.FXE
        C += getattr(m, "CAM", [])
    S.sort(key=lambda s: s[0])
    SHOTS, TRANS, FXE, CAM = S, sorted(T, key=lambda t: t[0]), F, C
    _starts = [s[0] for s in SHOTS]


def shot_index(b):
    i = bisect.bisect_right(_starts, b) - 1
    return max(0, min(len(SHOTS) - 1, i))


def _render_once(i, b, fi):
    b0, b1, fn, kw = SHOTS[i]
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = 255
    s = surface(arr)
    x = Ctx(s.getCanvas(), arr, b, b - b0, b1 - b0, fi)
    kw = {k: v for k, v in kw.items() if k != "mb"}
    res = fn(x, **kw)
    out = res if res is not None else arr
    del s
    return out


def render_shot(i, b, fi):
    n = SHOTS[i][3].get("mb", 1)
    if callable(n):
        n = n(b - SHOTS[i][0])
    if n <= 1:
        return _render_once(i, b, fi)
    acc = np.zeros((H, W, 4), np.float32)
    for k in range(n):
        acc += _render_once(i, b + ((k + 0.5) / n - 0.5) * SHUTTER, fi)
    return np.clip(acc * (1.0 / n) + 0.5, 0, 255).astype(np.uint8)


def compose(b, fi):
    for bc, kind, pre, post, kw in TRANS:
        if bc - pre <= b < bc + post:
            ia, ib = shot_index(bc - 1e-6), shot_index(bc)
            A = render_shot(ia, b, fi)
            B = render_shot(ib, b, fi)
            return trans.apply(kind, A, B, (b - (bc - pre)) / (pre + post), **kw)
    return render_shot(shot_index(b), b, fi)


def _env(b, b0, pre, dur):
    if b < b0 - pre or b > b0 + dur:
        return 0.0
    if b < b0:
        return seg(b, b0 - pre, b0)
    return 1.0 - seg(b, b0, b0 + dur) if dur > 0 else 1.0


def apply_fx(img, b, fi):
    for ev in FXE:
        b0, kind, dur, amp = ev[:4]
        kw = ev[4] if len(ev) > 4 else {}
        e = _env(b, b0, kw.get("pre", 0.0), dur)
        if e <= 0.001:
            continue
        a = amp * e
        seed = int(kw.get("seed", 1)) * 131 + fi
        if kind == "chroma":
            img = fx.rgb_split(img, a, kw.get("dy", 0.0))
        elif kind == "rchroma":
            img = fx.radial_chroma(img, a)
        elif kind == "shake":
            age = b - b0
            img = fx.affine(img, a * vnoise(age * 14, seed=31), a * vnoise(age * 14, seed=47),
                            a * 0.02 * vnoise(age * 10, seed=59))
        elif kind == "slice":
            img = fx.slices(img, seed, n=kw.get("n", 8), amp=a, hmax=kw.get("hmax", 60))
        elif kind == "block":
            img = fx.blocks(img, seed, n=int(kw.get("n", 12) * e) + 1, amp=a)
        elif kind == "invert":
            img = fx.invert(img, a)
        elif kind == "flash":
            img = fx.flash(img, a, kw.get("col", (255, 255, 255)))
        elif kind == "zoom":
            img = fx.zoom_blur(img, a, kw.get("cx", CX), kw.get("cy", CY))
        elif kind == "mosaic":
            img = fx.mosaic(img, 1 + a)
        elif kind == "smear":
            img = fx.smear(img, seed, n=kw.get("n", 6))
        elif kind == "punch":
            img = fx.affine(img, s=1 + a, cx=kw.get("cx", CX), cy=kw.get("cy", CY))
        elif kind == "hblur":
            img = fx.hblur(img, a)
        elif kind == "fish":
            img = fx.fisheye(img, a)
    return img


def _impact(age, decay):
    """Short smooth attack, then a damped release; no one-frame camera teleport."""
    if age <= 0:
        return 0.0
    attack = 0.025
    peak = attack * math.log1p(decay / attack)
    norm = (1 - math.exp(-peak / attack)) * math.exp(-peak / decay)
    return (1 - math.exp(-age / attack)) * math.exp(-age / decay) / norm


def camera(b):
    dx = dy = rot = 0.0
    s = 1.0
    for ev in CAM:
        b0, kind, amp = ev[:3]
        dec = ev[3] if len(ev) > 3 else 0.12
        age = b - b0
        if age < 0 or age > dec * 8:
            continue
        e = _impact(age, dec)
        if kind == "punch":
            s += amp * e
        elif kind == "shake":
            phase = age * 34
            dx += amp * e * math.sin(phase)
            dy += amp * e * 0.65 * math.sin(phase * 1.31)
            rot += amp * e * 0.025 * math.sin(phase * 0.83)
    if 44.0 <= b < 64.0:
        s += 0.012 * _impact(b % 1.0, 0.1)
    elif 4.0 <= b < 34.0:
        s += 0.006 * _impact(b % 1.0, 0.1)
    # Keep the frame covered during shake instead of reflecting its edges.
    r = abs(math.radians(rot))
    cover = max((W + 2 * abs(dx) + H * r) / W, (H + 2 * abs(dy) + W * r) / H)
    return dx, dy, rot, max(s, cover)


def grade(img, b, fi):
    dark = smooth(seg(b, 43.8, 44.5))
    return fx.finish_shader(img, b * SPB, dark, fi)


def frame(fi):
    b = f2b(fi)
    if b >= END_B:
        return fx.black()
    tick = int(math.floor(fi))
    img = compose(b, tick)
    img = apply_fx(img, b, tick)
    dx, dy, rot, s = camera(b)
    img = fx.affine(img, dx, dy, rot, s)
    img = grade(img, b, tick)
    return fx.vhs_crt(img, fi / FPS, tick)
