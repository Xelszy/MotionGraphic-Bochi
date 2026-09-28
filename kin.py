"""Kinetic text recipes -> per-glyph fns for core.txt(gfn=...).  Ported/adapted from JIZURA enter recipes."""
from __future__ import annotations

import math

from core import (clamp, lerp, seg, hash01, hr, hsgn, out_back, out_cubic, out_expo, in_expo, in_cubic, out_bounce,
                  out_elastic, inout_cubic, smooth, scramble_ch)


def _d(n, i, spread):
    return (i / (n - 1) if n > 1 else 0.0) * spread


def combine(*fns):
    fns = [f for f in fns if f]

    def g(i, n, ch):
        out = {}
        for f in fns:
            d = f(i, n, ch)
            if not d:
                continue
            for k, v in d.items():
                if k in ("dx", "dy", "rot", "skx"):
                    out[k] = out.get(k, 0.0) + v
                elif k in ("s", "sx", "sy", "a"):
                    out[k] = out.get(k, 1.0) * v
                elif k == "hide":
                    out[k] = out.get(k, False) or v
                else:
                    out[k] = v
        return out
    return g


def pop(p, spread=0.45, rot=28.0, seed=0, over=2.6):
    def g(i, n, ch):
        q = (p - _d(n, i, spread)) / (1 - spread)
        if q <= 0:
            return {"hide": True}
        return {"s": max(0.0, out_back(q, over)), "rot": (1 - out_cubic(q)) * hr(-1, 1, seed, i) * rot}
    return g


def slam(p, stretch=4.2):
    e = out_expo(p)
    return lambda i, n, ch: {"sx": lerp(stretch, 1, e), "sy": lerp(0.6, 1, e), "a": clamp(p * 4)}


def drop(p, size, spread=0.5, seed=0):
    def g(i, n, ch):
        q = (p - _d(n, i, spread)) / (1 - spread)
        if q <= 0:
            return {"hide": True}
        b = out_bounce(q)
        return {"dy": -(1 - b) * 2.4 * size, "sy": 1 + (1 - clamp(q * 1.5)) * 0.5, "sx": 1 - (1 - clamp(q * 1.5)) * 0.2}
    return g


def assemble(p, size, seed=0, motion=1.0):
    def g(i, n, ch):
        q = out_expo(clamp((p - _d(n, i, 0.25)) / 0.75))
        ang = hash01(seed, i) * 6.283
        spread = size * 3.2 * (0.6 + 0.7 * motion) * (1 - q)
        return {"dx": math.cos(ang) * spread, "dy": math.sin(ang) * spread, "rot": hr(-1, 1, seed, i, 2) * 190 * (1 - q),
                "s": lerp(hr(0.4, 2.1, seed, i, 3), 1, q), "a": clamp(q * 3)}
    return g


def scramble(p, seed=0, tick=0, lead=3, jp=False, spread=1.0):
    def g(i, n, ch):
        k = p * (n + lead) * spread
        if i < k - lead:
            return None
        if i < k:
            return {"ch": scramble_ch(ch, seed, i, tick, jp)}
        return {"hide": True}
    return g


def shuffle_to(p, seed=0, tick=0):
    """Random glyphs everywhere, settle left-to-right."""
    def g(i, n, ch):
        q = p * 1.3 - _d(n, i, 0.3)
        if q >= 1:
            return None
        return {"ch": scramble_ch(ch, seed, i, tick), "a": 0.6 + 0.4 * clamp(q)}
    return g


def typ(p):
    def g(i, n, ch):
        return {"hide": True} if i >= int(p * (n + 0.999)) else None
    return g


def wave(t, amp=10.0, freq=0.6, speed=6.0, rot=0.0):
    def g(i, n, ch):
        ph = i * freq + t * speed
        return {"dy": amp * math.sin(ph), "rot": rot * math.cos(ph)}
    return g


def jitter(tick, amp=2.0, seed=0, rot=2.0):
    def g(i, n, ch):
        return {"dx": hr(-amp, amp, seed, i, tick), "dy": hr(-amp, amp, seed, i, tick, 1), "rot": hr(-rot, rot, seed, i, tick, 2)}
    return g


def flip(p, spread=0.5, seed=0, tick=0):
    """Split-flap: glyph squashes vertically, shows random glyphs, lands."""
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        if q <= 0:
            return {"hide": True}
        if q < 1:
            return {"sy": abs(math.cos(q * math.pi * 3)) * 0.9 + 0.1, "ch": scramble_ch(ch, seed, i, tick)}
        return None
    return g


def zipper(p, size, spread=0.4):
    def g(i, n, ch):
        q = out_expo(clamp((p - _d(n, i, spread)) / (1 - spread)))
        sgn = 1 if i % 2 == 0 else -1
        return {"dy": sgn * (1 - q) * size * 1.6, "a": clamp(q * 2)}
    return g


def rail(p, width=900.0, spread=0.35, over=1.8):
    """snapRail: glyphs slide in along the baseline with overshoot."""
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        return {"dx": (1 - out_back(q, over)) * width, "a": clamp(q * 3), "skx": -20 * (1 - out_cubic(q))}
    return g


def spring(p, size, spread=0.4, seed=0):
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        if q <= 0:
            return {"hide": True}
        e = out_elastic(q)
        return {"dy": (1 - e) * size * 1.2, "s": 0.4 + 0.6 * e, "rot": (1 - e) * hr(-40, 40, seed, i)}
    return g


def dive(p, spread=0.3):
    """knDiveIn: glyph flies in from huge scale in front of camera."""
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        if q <= 0:
            return {"hide": True}
        e = out_expo(q)
        return {"s": lerp(6.0, 1.0, e), "a": clamp(q * 2.5)}
    return g


def stretch_in(p, spread=0.3):
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        e = out_expo(q)
        return {"sx": lerp(0.05, 1, e), "sy": lerp(2.4, 1, e), "a": clamp(q * 3)}
    return g


def exit_fall(p, size, seed=0, spread=0.3):
    def g(i, n, ch):
        q = clamp((p - _d(n, i, spread)) / (1 - spread))
        e = in_cubic(q)
        return {"dy": e * size * 6, "rot": e * hr(-90, 90, seed, i), "a": 1 - clamp(q * 1.2 - 0.2)}
    return g


def exit_scatter(p, size, seed=0):
    def g(i, n, ch):
        e = in_expo(p)
        ang = hash01(seed, i, 5) * 6.283
        return {"dx": math.cos(ang) * e * size * 8, "dy": math.sin(ang) * e * size * 8, "rot": e * hr(-200, 200, seed, i, 6),
                "s": 1 + e, "a": 1 - e}
    return g


def colors(cols, offset=0):
    return lambda i, n, ch: {"col": cols[(i + offset) % len(cols)]}


def beat_bounce(lb, size, every=1.0, amp=0.25):
    """Glyph hop on each beat, travelling left to right."""
    def g(i, n, ch):
        ph = (lb % every) / every
        q = clamp(ph * 3 - i / max(1, n) * 1.2)
        h = math.sin(q * math.pi) if 0 < q < 1 else 0.0
        return {"dy": -h * size * amp}
    return g


def glint(p, width=3.0):
    """Highlight sweep: returns per-glyph brightness via 'a' pulse (use with bright duplicate)."""
    def g(i, n, ch):
        x = i / max(1, n - 1)
        d = abs(x - (p * 1.4 - 0.2)) * n / width
        return {"a": clamp(1 - d)}
    return g
