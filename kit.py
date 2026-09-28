"""Shared shot helpers."""
from __future__ import annotations

import math

import numpy as np
import skia

import kin
from core import *  # noqa: F401,F403


def camz(c, z=1.0, cx=CX, cy=CY, rot=0.0, dx=0.0, dy=0.0):
    c.translate(cx + dx, cy + dy)
    if rot:
        c.rotate(rot)
    c.scale(z, z)
    c.translate(-cx, -cy)


def glyph_xs(s, size, font, track=0.0):
    k = size / REF
    xs, x = [], 0.0
    for ch in s:
        a = glyph(font, ch)[1] * k
        xs.append(x + a / 2)
        x += a + track
    return xs, x - track


def wave_text(c, s, x0, y, size, font, col, amp, freq, phase, track=0.0, gfn=None, **kw):
    """Text riding a sine wave y = amp*sin(freq*x/100 + phase), glyphs rotated to the slope."""
    xs, total = glyph_xs(s, size, font, track)

    def g(i, n, ch):
        u = xs[i]
        yy = amp * math.sin(freq * u / 100.0 + phase)
        sl = amp * freq / 100.0 * math.cos(freq * u / 100.0 + phase)
        d = {"dy": yy, "rot": math.degrees(math.atan(sl))}
        if gfn:
            e = gfn(i, n, ch)
            if e:
                if e.get("hide"):
                    return e
                for k2, v in e.items():
                    d[k2] = d.get(k2, 0.0) + v if k2 in ("dy", "dx", "rot") else v
        return d
    return txt(c, s, x0, y, size, font, col, align="l", track=track, gfn=g, **kw)


def sticker(c, path, fill, outline=WHITE, ow=12.0, shadow=(6, 8, 10, (60, 50, 90), 0.18), stroke=None, scol=None,
            shader=None, a=1.0):
    if shadow:
        c.save()
        c.translate(shadow[0], shadow[1])
        c.drawPath(path, paint(shadow[3], shadow[4] * a, stroke=ow * 2, blur=shadow[2]))
        c.drawPath(path, paint(shadow[3], shadow[4] * a, blur=shadow[2]))
        c.restore()
    if outline is not None and ow > 0:
        c.drawPath(path, paint(outline, a, stroke=ow * 2))
    if fill is not None or shader is not None:
        c.drawPath(path, paint(fill or WHITE, a, shader=shader))
    if stroke:
        c.drawPath(path, paint(scol or fill, a, stroke=stroke))


def marquee(c, s, y, size, font, col, off, gap=60.0, track=0.0, **kw):
    w = text_w(s, size, font, track) + gap
    x = (off % w) - w
    while x < W + w:
        txt(c, s, x, y, size, font, col, align="l", track=track, **kw)
        x += w


def dash_ring(c, cx, cy, r, col, lw, on, off, phase=0.0, a=1.0):
    p = paint(col, a, stroke=lw, cap=skia.Paint.kButt_Cap)
    p.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    c.drawCircle(cx, cy, r, p)


def fan(c, cx, cy, r, n, a0, spread, col, a=1.0, w=0.5):
    for i in range(n):
        ang = math.radians(a0 + (i - (n - 1) / 2) * spread)
        tip = (cx + math.cos(ang) * r, cy + math.sin(ang) * r)
        pa = ang + w * spread * math.pi / 180
        pb = ang - w * spread * math.pi / 180
        p = skia.Path()
        p.moveTo(cx + math.cos(pa) * r * 0.35, cy + math.sin(pa) * r * 0.35)
        p.lineTo(*tip)
        p.lineTo(cx + math.cos(pb) * r * 0.35, cy + math.sin(pb) * r * 0.35)
        p.close()
        c.drawPath(p, paint(col, a))


def smoke_bg(c, t, base=(232, 232, 238), puff=WHITE, seed=5, n=9, a=0.8):
    bg(c, base)
    for i in range(n):
        x = hash01(seed, i) * W + 40 * math.sin(t * 0.7 + i)
        y = hash01(seed, i, 1) * H + 30 * math.cos(t * 0.5 + i * 2)
        r = hr(120, 320, seed, i, 2)
        c.drawCircle(x, y, r, paint(puff, a * hr(0.4, 0.9, seed, i, 3), blur=r * 0.45))


def card(c, x, y, w, h, bar, content, rot=0.0, s=1.0, a=1.0, sx=1.0, title="", r=8.0, lw=3.0, ink=INK):
    """Mini window card with coloured title bar. content(c, rect) draws inside."""
    if a <= 0.001 or s <= 0.001:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s * sx, s)
    c.translate(-w / 2, -h / 2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(5, 7, w + 5, h + 7), r, r), paint((40, 30, 70), 0.16 * a, blur=6))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(0, 0, w, h), r, r), paint(WHITE, a))
    bh = max(14.0, h * 0.11)
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(0, 0, w, h), r, r), True)
    c.drawRect(skia.Rect(0, 0, w, bh), paint(bar, a))
    if content:
        c.save()
        c.clipRect(skia.Rect(4, bh + 4, w - 4, h - 4))
        content(c, (4, bh + 4, w - 8, h - bh - 8))
        c.restore()
    c.restore()
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(0, 0, w, h), r, r), paint(ink, a * 0.85, stroke=lw))
    for i in range(3):
        c.drawCircle(w - 12 - i * 13, bh / 2, bh * 0.2, paint(WHITE, a))
    if title:
        label(c, title, 8, bh / 2, bh * 0.55, "monob", WHITE, a)
    c.restore()


def photo_fn(name, u=0.5, v=0.5, z=1.0, bgc=None, fx=None):
    def f(c, rc):
        x, y, w, h = rc
        if bgc is not None:
            c.drawRect(skia.Rect(x, y, x + w, y + h), paint(bgc))
        photo(c, name, x, y, w, h, u, v, z, fx=fx)
    return f


def lines_fn(col=GREY, n=5, seed=0):
    def f(c, rc):
        x, y, w, h = rc
        for i in range(n):
            ww = w * hr(0.35, 0.92, seed, i)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 8, y + 10 + i * 16, x + 8 + ww, y + 18 + i * 16), 4, 4), paint(col))
    return f


def flat_shadow(c, path, dx, dy, col, a=1.0):
    c.save()
    c.translate(dx, dy)
    c.drawPath(path, paint(col, a))
    c.restore()


def bang(c, cx, cy, h, col=WHITE, a=1.0, rot=0.0, outline=None, ow=6.0):
    """Exclamation mark shape."""
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    body = skia.Path()
    body.moveTo(-h * 0.16, -h * 0.5)
    body.lineTo(h * 0.16, -h * 0.5)
    body.lineTo(h * 0.07, h * 0.18)
    body.lineTo(-h * 0.07, h * 0.18)
    body.close()
    body.addCircle(0, h * 0.4, h * 0.1)
    if outline:
        c.drawPath(body, paint(outline, a, stroke=ow))
    c.drawPath(body, paint(col, a))
    c.restore()


def ribbon(c, pts_fn, p, col, lw, a=1.0, start=0.0):
    """Draw-on thick stroke along a polyline path given as skia.Path via pts_fn()."""
    path = pts_fn()
    tp = trim_path(path, p, start)
    c.drawPath(tp, paint(col, a, stroke=lw))


def iso_cube(c, x, y, s, top, left, right, lw=0.0, ink=None, a=1.0):
    """Isometric cube with top face centred at (x, y)."""
    h = s * 0.5
    t = skia.Path()
    t.moveTo(x, y - h)
    t.lineTo(x + s, y)
    t.lineTo(x, y + h)
    t.lineTo(x - s, y)
    t.close()
    l = skia.Path()
    l.moveTo(x - s, y)
    l.lineTo(x, y + h)
    l.lineTo(x, y + h + s)
    l.lineTo(x - s, y + s)
    l.close()
    r = skia.Path()
    r.moveTo(x + s, y)
    r.lineTo(x, y + h)
    r.lineTo(x, y + h + s)
    r.lineTo(x + s, y + s)
    r.close()
    for pth, col in ((l, left), (r, right), (t, top)):
        c.drawPath(pth, paint(col, a))
        if lw:
            c.drawPath(pth, paint(ink or WHITE, a, stroke=lw))
    return t


def iso_matrix(x, y, s):
    """Matrix mapping unit square (-1..1) onto the iso top face centred at (x, y) with half-diagonal s."""
    m = skia.Matrix()
    m.setAll(s / 2, -s / 2, x, s / 4, s / 4, y, 0, 0, 1)
    return m
