"""Dark section: b44-67.5 (black, galaxy purple, magenta, dark red, chrome)."""
from __future__ import annotations

import math

import cv2
import numpy as np
import skia

import fx
import kin
from core import *  # noqa: F401,F403
from kit import *  # noqa: F401,F403

VIO = (40, 12, 72)


def chrome(cap, hue=(200, 200, 230)):
    return lin(0, -cap * 0.5, 0, cap * 0.5, [WHITE, (215, 215, 235), (60, 50, 90), hue, (140, 130, 175), WHITE],
               [0.0, 0.38, 0.5, 0.56, 0.82, 1.0])


def speed_lines(c, cx, cy, n, r0, r1, col, a, seed, tick, w=(1.0, 4.0)):
    for i in range(n):
        ang = hash01(seed, i, tick) * 6.283
        ww = math.radians(hr(w[0], w[1], seed, i, tick, 1) * 0.12)
        rr0 = r0 * hr(0.7, 1.3, seed, i, tick, 2)
        p = skia.Path()
        p.moveTo(cx + math.cos(ang) * rr0, cy + math.sin(ang) * rr0)
        p.lineTo(cx + math.cos(ang + ww) * r1, cy + math.sin(ang + ww) * r1)
        p.lineTo(cx + math.cos(ang - ww) * r1, cy + math.sin(ang - ww) * r1)
        p.close()
        c.drawPath(p, paint(col, a))


def bokeh(c, seed, n, t, cols, cx=CX, cy=CY, burst=None, spread=(80, 700), size=(10, 70), a=0.8, drift=20.0):
    for i in range(n):
        col = cols[int(hash01(seed, i) * len(cols))]
        ang = hash01(seed, i, 1) * 6.283
        d = hr(spread[0], spread[1], seed, i, 2)
        if burst is not None:
            d *= out_expo(clamp((t - burst) * hr(1.5, 3.5, seed, i, 3)))
        x = cx + math.cos(ang) * d * 1.5 + drift * math.sin(t * 0.8 + i)
        y = cy + math.sin(ang) * d + drift * math.cos(t * 0.7 + i)
        r = hr(size[0], size[1], seed, i, 4)
        c.drawCircle(x, y, r, paint(col, a * hr(0.4, 1.0, seed, i, 5), blur=hr(1, r * 0.35, seed, i, 6), blend=PLUS))


def _orbit_layer(c, cx, cy, rx, ry, t, q, seed=0, col=MAG):
    """Sparse midground orbits: deliberate parallax around the focal subject."""
    if q <= 0:
        return
    for i in range(3):
        ph = (seed * 17 + i * 47 + t * (18 if i & 1 else -24)) % 360
        span = 96 + 24 * math.sin(t * 1.7 + i + seed)
        p = skia.Path()
        p.arcTo(skia.Rect(cx - rx * (1 + i * 0.14), cy - ry * (1 - i * 0.08),
                          cx + rx * (1 + i * 0.14), cy + ry * (1 - i * 0.08)), ph, span, False)
        c.drawPath(p, paint(col if i != 1 else WHITE, q * (0.16 - i * 0.025), stroke=1.4 + i * 0.7, blur=2))


def _lens_streaks(c, t, q, seed=0, cols=(WHITE, MAG, CYAN)):
    """A few continuous foreground glints, not a full-frame animated overlay."""
    if q <= 0:
        return
    for i in range(5):
        u = (hash01(seed, i, 1) + t * (0.018 + 0.006 * (i % 3))) % 1.0
        xx = lerp(-180, W + 180, u)
        yy = hr(70, H - 70, seed, i, 2) + 18 * math.sin(t * 1.3 + i)
        ln = hr(90, 260, seed, i, 3)
        col = cols[i % len(cols)]
        c.drawLine(xx - ln, yy, xx + ln, yy + hr(-3, 3, seed, i, 4),
                   paint(col, q * hr(0.10, 0.24, seed, i, 5), stroke=hr(1.2, 3.2, seed, i, 6), blur=5, blend=PLUS))
        c.drawCircle(xx, yy, hr(3, 10, seed, i, 7),
                     paint(col, q * 0.22, blur=12, blend=PLUS))


def _depth_specks(c, t, q, seed=0, n=18, col=(180, 160, 220)):
    """Sparse background points that reinforce depth behind graphic layers."""
    if q <= 0:
        return
    for i in range(n):
        xx = (hash01(seed, i, 1) * W + t * hr(4, 18, seed, i, 2)) % W
        yy = hash01(seed, i, 3) * H
        r = hr(0.8, 2.6, seed, i, 4)
        c.drawCircle(xx, yy, r, paint(col, q * hr(0.16, 0.42, seed, i, 5), blur=r * 2))

def ring_text(c, s, cx, cy, R, size, font, col, a0, a=1.0, **kw):
    k = size / REF
    advs = [glyph(font, ch)[1] * k for ch in s]
    ang = math.radians(a0)
    for ch, adv in zip(s, advs):
        da = adv / R
        th = ang + da / 2
        if ch != " ":
            txt(c, ch, cx + math.cos(th) * R, cy + math.sin(th) * R, size, font, col, a, rot=math.degrees(th) + 90, **kw)
        ang += da


# ---------------------------------------------------------------- D0 light burst  b44..44.5
def s_burst(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, BLACK)
    q = seg(lb, 0.0, 0.5)
    e = out_expo(q)
    for i in range(70):
        ang = hash01(44, i) * 360
        wd = hr(0.4, 2.2, 44, i, 1)
        ln = hr(500, 1400, 44, i, 2) * e
        p = skia.Path()
        p.moveTo(CX, CY)
        p.arcTo(skia.Rect(CX - ln, CY - ln, CX + ln, CY + ln), ang, wd, False)
        p.close()
        c.drawPath(p, paint(WHITE, 0.75 * (1 - q) + 0.1, blend=PLUS))
    c.drawCircle(CX, CY, 60 + 260 * e, paint(WHITE, 0.9 * (1 - q) + 0.1, blur=60))
    c.drawCircle(CX, CY, 30 + 40 * e, paint(WHITE, 1.0))
    c.drawRect(skia.Rect(0, CY - 3, W, CY + 3), paint((200, 220, 255), 0.9 * (1 - q), blur=4))
    c.drawPath(P_sparkle(CX, CY, 120 + 200 * e, 45 * e), paint(WHITE, 0.9))


# ---------------------------------------------------------------- D1 CLARITY chrome hero  b44.5..45.5 (CREDIT)
def _chrome_blob(c, cx, cy, r, seed, t, cols):
    pth = P_blob(cx, cy, r, seed, t, 0.22)
    c.drawPath(pth, paint(shader=lin(cx - r, cy - r, cx + r, cy + r, cols)))
    c.save()
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    c.drawCircle(cx - r * 0.3, cy - r * 0.35, r * 0.45, paint(WHITE, 0.7, blur=r * 0.18))
    c.drawPath(xform(pth, 8, 10), paint(BLACK, 0.35, stroke=r * 0.12, blur=6))
    c.restore()


def s_clarity(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 800, [VIO, (22, 6, 40), BLACK])))
    stars(c, t, 5, 90, 0.7)
    for k, (bx, by, br, cols) in enumerate([(230, 170, 120, [(255, 150, 210), MAG, (90, 20, 90)]),
                                           (1060, 480, 150, [(160, 220, 255), (60, 110, 255), (20, 20, 80)]),
                                           (1120, 130, 70, [(255, 200, 240), HOT, (70, 10, 60)]),
                                           (170, 520, 80, [(200, 240, 255), (80, 150, 255), (10, 20, 60)])]):
        e = out_back(seg(lb, 0.05 * k, 0.3 + 0.05 * k), 1.7)
        if e > 0:
            _chrome_blob(c, bx + 14 * math.sin(t * 1.5 + k), by + 10 * math.cos(t * 1.2 + k), br * e, 20 + k, t, cols)
    size = 178
    cap = cap_of("unb900") * size
    e = seg(lb, 0.0, 0.3)
    tint = smooth(seg(lb, 0.45, 0.65))
    hue = mix((170, 200, 255), (255, 150, 220), tint)
    g = kin.stretch_in(e, 0.35)
    tick = x.fi // 2
    glitch = 1 - smooth(seg(lb, 0.0, 0.14))
    if lb >= 0.5:
        glitch = 0.55 * (1 - smooth(seg(lb, 0.5, 0.59)))
    bands = None
    if glitch > 0:
        bands = [(j / 6, (j + 1) / 6 + 0.001, hr(-12, 12, tick, j) * glitch) for j in range(6)]
    txt(c, "CLARITY", CX, CY - 10, size, "unb900", WHITE, shader=chrome(cap, hue), track=4, gfn=g,
        ext=(12, 1.2, 1.8, (70, 30, 110), (8, 2, 16)), stroke=1.6, scol=WHITE,
        glow=(16, mix((80, 140, 255), MAG, tint), 0.35), bands=bands,
        ghost=(4 * glitch, 0, CYAN, MAG, 0.25 * glitch, PLUS) if glitch > 0 else None)
    sweep_x = lerp(-720, 720, smooth(seg(lb, 0.28, 0.95)))
    txt(c, "CLARITY", CX, CY - 10, size, "unb900", WHITE, track=4, gfn=g,
        shader=lin(sweep_x - 90, -cap, sweep_x + 90, cap, [BLACK, WHITE, BLACK]),
        a=0.22 * smooth(seg(lb, 0.25, 0.4)), blend=PLUS)
    p = seg(lb, 0.25, 0.7)
    if p > 0:
        txt(c, "TRACK_01  //  90 BPM", CX, CY + 150, 22, "monob", (230, 220, 255), track=6,
            gfn=kin.scramble(p, seed=9, tick=tick, lead=5))
    return fx.rgb_split(x.arr, 4 * glitch) if glitch > 0 else None


# ---------------------------------------------------------------- D2 manga collage  b45.5..46
def s_manga(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (14, 12, 18))
    drift = smooth(seg(lb, -0.12, 0.62))
    img(c, "panic", 250 + lerp(-12, 12, drift), CY + 4 * math.sin(t * 2), 700,
        fx=("manga",), sx=1.7, rot=-4 + math.sin(t * 2))
    img(c, "full", 1060 + lerp(12, -12, drift), CY + 180 + 5 * math.cos(t * 1.8), 1100,
        fx=("manga",), sx=1.5, rot=5 - math.sin(t * 2))
    c.save()
    c.translate(CX + 6 * math.sin(t * 2.2), CY + 4 * math.cos(t * 1.8))
    c.rotate(-3 + 1.5 * math.sin(t * 2.5))
    c.drawRect(skia.Rect(-230, -190, 230, 190), paint(HOT))
    photo(c, "shot", -215, -175, 430, 350, 0.5, 0.45, 1.35 + 0.1 * lb, fx=("duo", (60, 0, 40), (255, 170, 215)))
    c.drawRect(skia.Rect(-215, -175, 215, 175), paint(WHITE, stroke=4))
    c.restore()
    return fx.rgb_split(x.arr, 1.5 + 3.5 * (1 - smooth(seg(lb, 0.0, 0.12))))


# ---------------------------------------------------------------- D3 card row on galaxy  b46..47
def s_cards(x):
    c, lb, t = x.c, x.lb, x.t
    bg_galaxy(c, t, 3)
    _depth_specks(c, t, 0.7, seed=46, n=22, col=(150, 130, 210))
    _orbit_layer(c, CX, CY, 380, 190, t, 0.46 * smooth(seg(lb, 0.0, 0.55)), seed=46, col=(110, 130, 220))
    flip = smooth(seg(lb, 0.38, 0.7))
    sy = abs(math.cos(flip * math.pi))
    col = BLUE if flip < 0.5 else HOT
    txt(c, "STARRY", CX, CY, 330, "unb900", col, a=0.55 * smooth(seg(sy, 0, 0.08)),
        sy=max(0.001, sy), track=-4)
    names = [("shot", 0.5, 0.4, 1.6, None), ("peace", 0.5, 0.2, 1.0, ("duo", (40, 10, 70), (255, 190, 230))),
             ("maid", 0.5, 0.18, 1.0, ("duo", (20, 10, 60), (190, 220, 255)))]
    alt = [("guitar", 0.4, 0.2, 1.0, ("duo", (40, 10, 70), (255, 170, 220))), ("shot", 0.3, 0.6, 2.0, None),
           ("full", 0.5, 0.1, 1.0, ("duo", (20, 10, 60), (200, 230, 255)))]
    for k in range(3):
        q = seg(lb, -0.2 + 0.08 * k, 0.15 + 0.08 * k)
        e = out_expo(q)
        fk = smooth(seg(lb, 0.43 + 0.05 * k, 0.73 + 0.05 * k))
        sx = max(0.001, abs(math.cos(fk * math.pi)))
        src = names[k] if fk < 0.5 else alt[k]
        cx = CX + (k - 1) * 300 - 30 * lb
        cy = CY + (1 - e) * 500 + 6 * math.sin(t * 2 + k)
        c.save()
        c.translate(cx, cy)
        c.scale(sx, 1)
        c.rotate((k - 1) * 3)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-126, -166, 126, 166), 14, 14), paint(WHITE))
        nm, u, v, z, f = src
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-118, -158, 118, 158), 10, 10), paint((30, 14, 50)))
        photo(c, nm, -118, -158, 236, 316, u, v, z, fx=f, r=10)
        c.restore()
    _lens_streaks(c, t, 0.18 * smooth(seg(lb, 0.18, 0.9)), seed=146, cols=(WHITE, BLUE, PINK))


# ---------------------------------------------------------------- D4 swirls + collapse streak  b47..47.5
def s_swirl(x):
    c, lb, t = x.c, x.lb, x.t
    arr, s, lc = layer()
    bg_galaxy(lc, t, 8)
    stars(lc, t, 9, 120, 1.0, zoom=lb * 2)
    for k in range(6):
        p = skia.Path()
        a0 = k * 60 + t * 90
        cx, cy = CX, CY
        p.moveTo(cx + math.cos(math.radians(a0)) * 90, cy + math.sin(math.radians(a0)) * 90)
        for j in range(1, 20):
            aa = math.radians(a0 + j * 22)
            rr = 90 + j * 22
            p.lineTo(cx + math.cos(aa) * rr * 1.5, cy + math.sin(aa) * rr)
        lc.drawPath(p, paint(PINK if k % 2 else (90, 150, 255), 0.75, stroke=26 - k * 2, blur=6, blend=PLUS))
    img(lc, "full", CX, CY + 60, 620, fx=("sil", WHITE), blur=16, a=0.6)
    img(lc, "full", CX, CY + 60, 620, fx=("tint", WHITE, 0.55))
    q = in_expo(seg(lb, 0.2, 0.5))
    c.clear(rgba(BLACK))
    c.save()
    c.translate(CX, CY)
    c.scale(1 + 0.3 * q, max(0.01, 1 - q))
    c.translate(-CX, -CY)
    blit(c, arr)
    c.restore()
    if q > 0:
        c.drawRect(skia.Rect(0, CY - 2 - 8 * q, W, CY + 2 + 8 * q), paint(WHITE, q, blur=10))
        c.drawRect(skia.Rect(0, CY - 1.5, W, CY + 1.5), paint(WHITE, q))


# ---------------------------------------------------------------- D5 pink blob -> outline page  b47.5..48
def s_blobpage(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, BLACK)
    g = in_expo(seg(lb, 0.0, 0.3))
    R = lerp(140, 1100, g)
    c.drawPath(P_blob(CX, CY, R, 12, t * 3, 0.16), paint(HOT))
    if g < 0.3:
        label(c, "signal 47%", CX, CY - 10, 14, "monob", WHITE, align="c")
        label(c, "kessoku_live.mov", CX, CY + 12, 11, "mono", WHITE, 0.8, align="c")
    w = seg(lb, 0.28, 0.4)
    if w > 0:
        c.drawPaint(paint(WHITE, w))
        p = seg(lb, 0.3, 0.5)
        txt(c, "HITORI", CX, CY, 520, "bebas", HOT, sx=0.62, fill=0.0, stroke=2.5, draw=p, track=20)


# ---------------------------------------------------------------- D6 doodles + laser  b48..49
def _doodles(c, p, tick, cols=(HOT, PINK)):
    j = tick
    items = [P_heart(310 + hr(-2, 2, j), 190, 50, -12), P_star(990, 170, 52, 22, 5, 8),
             wave_path(180, 470, 470, 18, 3.2, 0.5), P_heart(1040, 480, 36, 14),
             P_sparkle(470, 120, 40, 0), wave_path(820, 1120, 590, 12, 4.0, 1.0)]
    arr = skia.Path()
    arr.moveTo(860, 300)
    arr.cubicTo(900, 220, 980, 240, 1000, 300)
    arr.moveTo(985, 280)
    arr.lineTo(1002, 304)
    arr.lineTo(1020, 282)
    items.append(arr)
    for k, pth in enumerate(items):
        pk = seg(p, 0.08 * k, 0.4 + 0.08 * k)
        if pk <= 0:
            continue
        q = xform(pth, hr(-2, 2, j, k), hr(-2, 2, j, k, 1))
        c.drawPath(trim_path(q, pk), paint(cols[k % 2], stroke=5))


def s_doodle(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, WHITE)
    txt(c, "HITORI", CX, CY, 520, "bebas", (255, 214, 232), sx=0.62, fill=0.0, stroke=2.0, track=20)
    img(c, "peace", CX + 40, CY + 40 + 6 * math.sin(t * 3), 360, rot=-3, fx=("stk", 6, WHITE))
    _doodles(c, seg(lb, 0.0, 0.8), x.fi // 3)
    q = seg(lb, 0.5, 0.62)
    if q > 0:
        xe = lerp(-100, W + 200, out_expo(q))
        a = 1 - seg(lb, 0.75, 1.0)
        c.drawRect(skia.Rect(-100, 400 - 6, xe, 400 + 6), paint(HOT, a))
        c.drawRect(skia.Rect(-100, 400 - 16, xe, 400 + 16), paint(HOT, 0.5 * a, blur=12))
        c.drawCircle(xe, 400, 20, paint(WHITE, a, blur=6))
    label(c, "ぼっち", 150, 600, 22, "round", HOT, 0.9)
    label(c, "b48 / 90 BPM", W - 60, 600, 12, "monob", HOT, 0.8, align="r")


# ---------------------------------------------------------------- D7 speed-line card  b49..50
def s_speedcard(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, WHITE)
    sh = lerp(1.0, 0.82, inout_cubic(seg(lb, 0.55, 0.9)))
    c.save()
    camz(c, sh)
    rr = skia.RRect.MakeRectXY(skia.Rect(50, 40, W - 50, H - 40), 34, 34)
    c.save()
    c.clipRRect(rr, True)
    c.drawPaint(paint(shader=rad(CX, CY, 700, [(255, 200, 235), MAG, (130, 0, 90)])))
    speed_lines(c, CX, CY, 90, 120, 1000, WHITE, 0.8, 49, x.fi // 2, (2, 8))
    c.drawCircle(CX, CY, 150, paint(WHITE, 0.6, blur=50))
    img(c, "panic", CX, CY + 10, 250 * (1 + 0.1 * pulse(lb % 0.5, 0.08)), rot=6 * math.sin(t * 8))
    c.restore()
    c.drawRRect(rr, paint(WHITE, stroke=10))
    c.restore()
    txt(c, "90 BPM", CX, H - 18, 14, "monob", HOT, a=seg(lb, 0.6, 0.8))


# ---------------------------------------------------------------- D8 red lens + title card  b50..51
def s_redtitle(x):
    c, lb, t = x.c, x.lb, x.t
    if lb < 0.5:
        bg(c, BLACK)
        _depth_specks(c, t, 0.45, seed=50, n=16, col=(130, 35, 55))
        _orbit_layer(c, CX, CY, 430, 190, t, 0.28 * smooth(seg(lb, 0.0, 0.5)), seed=50, col=CRIM)
        p = seg(lb, 0.0, 0.3)
        c.drawPath(trim_path(P_arc(CX, CY, 250, -90, 359.9), out_cubic(p)), paint(WHITE, stroke=2))
        img(c, "guitar", CX + 20, CY + 30, 480, fx=("sil", CRIM), a=0.9)
        for k in range(3):
            c.drawPath(P_arc(CX, CY, 420 + k * 70, 150 + t * 20 * (k + 1), 70), paint(CRIM, 0.7 - 0.2 * k, stroke=10 - k * 3))
            c.drawPath(P_arc(CX, CY, 420 + k * 70, -30 - t * 25 * (k + 1), 60), paint(CRIM, 0.7 - 0.2 * k, stroke=10 - k * 3))
        _lens_streaks(c, t, 0.16 * smooth(seg(lb, 0.08, 0.48)), seed=150, cols=(WHITE, CRIM, HOT))
        return
    c.drawPaint(paint(shader=rad(CX, CY, 700, [(150, 16, 40), DRED, (30, 2, 8)])))
    _depth_specks(c, t, 0.4, seed=51, n=14, col=(160, 30, 50))
    _orbit_layer(c, CX, CY, 520, 240, t, 0.2 * smooth(seg(lb, 0.5, 0.85)), seed=51, col=(230, 70, 90))
    for side in (-1, 1):
        c.drawCircle(CX + side * 1050, CY, 760, paint(BLACK, 0.85, blur=30))
        c.drawCircle(CX + side * 1050, CY, 770, paint((255, 90, 110), 0.5, stroke=3))
    p = seg(lb, 0.5, 0.8)
    txt(c, "後藤ひとり", CX, CY - 20, 66, "round", WHITE, gfn=kin.scramble(p, seed=5, tick=x.fi // 2, lead=2, jp=True))
    txt(c, "HITORI GOTOH", CX, CY + 42, 22, "monob", (255, 200, 205), track=8,
        gfn=kin.scramble(seg(lb, 0.58, 0.9), seed=6, tick=x.fi // 2, lead=4))
    _lens_streaks(c, t, 0.14 * smooth(seg(lb, 0.55, 0.96)), seed=151, cols=(WHITE, (255, 120, 140), CRIM))


# ---------------------------------------------------------------- D9 split silhouettes + waveform  b51..52
def s_split(x):
    c, lb, t = x.c, x.lb, x.t
    sw = inout_cubic(seg(lb, 0.45, 0.6))
    xs = lerp(CX - 60, CX + 60, sw)
    bg(c, CRIM if sw < 0.5 else HOT)
    _depth_specks(c, t, 0.24, seed=51, n=12, col=(255, 170, 190))
    _lens_streaks(c, t, 0.12 * smooth(seg(lb, 0.0, 0.8)), seed=251, cols=(WHITE, HOT, CRIM))
    L = skia.Path()
    L.moveTo(-10, -10)
    L.lineTo(xs + 90, -10)
    L.lineTo(xs - 90, H + 10)
    L.lineTo(-10, H + 10)
    L.close()
    c.save()
    c.clipPath(L, skia.ClipOp.kIntersect, True)
    c.drawPaint(paint(CRIM if sw < 0.5 else HOT))
    img(c, "maid", 330 - 200 * sw, CY + 180, 1100, fx=("sil", HOT if sw < 0.5 else CRIM))
    c.restore()
    c.save()
    c.clipPath(L, skia.ClipOp.kDifference, True)
    c.drawPaint(paint(HOT if sw < 0.5 else CRIM))
    img(c, "peace", 960 + 200 * sw, CY + 220, 1150, fx=("sil", CRIM if sw < 0.5 else HOT), flip=True)
    c.restore()
    j = x.fi
    for i in range(40):
        yy = i * H / 40 + 8
        xx = xs + 90 - 180 * (yy / H)
        amp = 12 + 90 * hash01(i, j) * (0.4 + 0.6 * pulse(lb % 0.5, 0.15))
        c.drawRect(skia.Rect(xx - amp, yy - 3, xx + amp, yy + 3), paint(WHITE, 0.9))


# ---------------------------------------------------------------- D10 bokeh explosion  b52..53
def s_bokeh(x):
    c, lb, t = x.c, x.lb, x.t
    tl = 1 - seg(lb, 0.0, 0.3)
    c.drawPaint(paint(shader=rad(CX, CY, 800, [mix((110, 10, 30), TEAL, tl), mix((50, 4, 14), (4, 40, 44), tl), BLACK])))
    _depth_specks(c, t, 0.6, seed=52, n=24, col=(100, 180, 190))
    _orbit_layer(c, CX, CY, 440, 250, t, 0.25 * (1 - seg(lb, 0.1, 0.4)), seed=52, col=(100, 220, 210))
    bokeh(c, 52, 40, lb * 2, [PINK, MAG, (255, 60, 60), PURPLE, (90, 140, 255), YEL], burst=0.0, spread=(120, 620),
          size=(14, 64), a=0.75)
    img(c, "peace", CX, CY + 260, 900, fx=("sil", WHITE), blur=24, a=0.5)
    img(c, "peace", CX, CY + 260, 900)
    bokeh(c, 53, 16, lb * 2, [PINK, (255, 80, 80), MAG, YEL], burst=0.1, spread=(250, 700), size=(30, 90), a=0.6)
    _lens_streaks(c, t, 0.16 * smooth(seg(lb, 0.08, 0.9)), seed=152, cols=(WHITE, TEAL, PINK))
    if lb < 0.3:
        txt(c, "STARRY", CX, 120, 90, "unb900", WHITE, glow=(24, (120, 255, 240), 0.9), a=1 - seg(lb, 0.15, 0.3))


# ---------------------------------------------------------------- D11 close-ups + smear  b53..54.5
def s_closeups(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 800, [(80, 10, 20), (26, 4, 8)])))
    if lb < 0.75 or lb >= 1.0:
        first = lb < 0.75
        nm = "maid" if first else "guitar"
        z = 1 + 0.12 * (lb if first else lb - 1.0)
        img(c, nm, CX + (60 if first else -80), (1320 if first else 1500) * z * 0.62 - 160, (1400 if first else 1700) * z,
            ay=0.5)
        bokeh(c, 54 + int(lb), 22, t, [(255, 40, 60), (255, 90, 110), CRIM], spread=(100, 700), size=(24, 90), a=0.55,
              drift=40)
        _lens_streaks(c, t, 0.12 * smooth(seg(lb, 0.0, 0.72)), seed=154, cols=(WHITE, CRIM, (255, 100, 120)))
        return None
    img(c, "maid", CX + 60, 1320 * 1.09 * 0.62 - 160, 1400 * 1.09, ay=0.5)
    g = cv2.cvtColor(cv2.cvtColor(x.arr, cv2.COLOR_BGRA2GRAY), cv2.COLOR_GRAY2BGRA)
    return fx.smear(fx.slices(g, x.fi, 10, 120, 8, 50, tint=False), x.fi + 3, 8)


# ---------------------------------------------------------------- D12 big white word on red  b54.5..55.5
def s_bigword(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (120, 8, 24))
    _depth_specks(c, t, 0.25, seed=54, n=14, col=(180, 80, 100))
    _lens_streaks(c, t, 0.1 * smooth(seg(lb, 0.0, 0.7)), seed=254, cols=(WHITE, CRIM, HOT))
    img(c, "peace", 820 - 20 * lb, 700, 1500, ay=0.55, fx=("duo", (60, 0, 12), (255, 150, 160)))
    c.drawPaint(paint(shader=lin(0, 0, W, 0, [(90, 0, 14), (90, 0, 14), (0, 0, 0)], [0, 0.3, 1.0], a=0.55)))
    txt(c, "BOCCHI", 70, 190, 250, "anton", WHITE, align="l", gfn=kin.combine(kin.stretch_in(seg(lb, -0.1, 0.25), 0.3)),
        shadow=(0, 0, 20, BLACK, 0.4))
    if lb >= 0.5:
        txt(c, "THE ROCK", 76, 380, 120, "anton", WHITE, align="l", gfn=kin.rail(seg(lb, 0.5, 0.75), 600))


# ---------------------------------------------------------------- D13 lock screen  b55.5..56.5
def s_lock(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (60, 30, 50))
    img(c, "shot", CX, CY, 1300 * (1.05 + 0.03 * lb), blur=22, fx=("tint", (255, 150, 190), 0.35))
    c.drawPaint(paint((24, 12, 32), 0.48))
    dots(c, WHITE, 18, 1.2, a=0.18)
    label(c, "Enter Passcode", CX, 96, 18, "monob", WHITE, align="c")
    for i in range(4):
        cx = CX - 45 + i * 30
        filled = smooth(seg(lb, i * 0.2 + 0.04, i * 0.2 + 0.12))
        c.drawCircle(cx, 132, 7, paint(WHITE, stroke=1.6))
        if filled > 0:
            c.drawCircle(cx, 132, 7 * out_back(filled, 1.3), paint(WHITE, filled))
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", ""]
    sub = ["", "ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ", "", "+", ""]
    presses = [2, 8, 4, 0]
    for k, key in enumerate(keys):
        if not key:
            continue
        i, j = k % 3, k // 3
        cx, cy = CX + (i - 1) * 104, 220 + j * 100
        dt = lb - presses.index(k) * 0.2 if k in presses else -1.0
        pr = smooth(seg(dt, 0.0, 0.04)) * (1 - smooth(seg(dt, 0.04, 0.18)))
        if 0 < dt < 0.24:
            ripple = seg(dt, 0.02, 0.24)
            c.drawCircle(cx, cy, 40 + 12 * out_cubic(ripple),
                         paint(WHITE, 0.28 * pr * (1 - ripple), stroke=1.4))
        c.save()
        c.translate(cx, cy)
        c.scale(1 - 0.07 * pr, 1 - 0.07 * pr)
        c.drawCircle(0, 0, 40, paint(WHITE, 0.12 + 0.35 * pr))
        c.drawCircle(0, 0, 40, paint(WHITE, 0.6 + 0.25 * pr, stroke=1.4))
        txt(c, key, 0, -6, 30, "unb400", WHITE)
        label(c, sub[k], 0, 20, 9, "monob", WHITE, 0.8, align="c")
        c.restore()


# ---------------------------------------------------------------- D14 orb -> chrome warp text  b56.5..57.5
def s_chrome(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 800, [(46, 16, 70), (16, 6, 26), BLACK])))
    _depth_specks(c, t, 0.45, seed=56, n=20, col=(170, 130, 210))
    _orbit_layer(c, CX, CY, 460, 250, t, 0.22 * smooth(seg(lb, 0.0, 0.6)), seed=56, col=(220, 150, 220))
    stars(c, t, 14, 110, 0.9)
    pts = [(hr(80, W - 80, 57, i), hr(60, H - 60, 58, i)) for i in range(14)]
    for i in range(13):
        a, b = pts[i], pts[i + 1]
        c.drawLine(a[0], a[1], b[0], b[1], paint(WHITE, 0.25, stroke=1))
        c.drawCircle(a[0], a[1], 3, paint(WHITE, 0.7))
    o = seg(lb, 0.0, 0.25)
    if lb < 0.3:
        r = 40 + 220 * out_expo(o)
        c.drawCircle(CX, CY, r * 1.6, paint((255, 150, 230), 0.5, blur=r * 0.5))
        c.drawCircle(CX, CY, r, paint(shader=rad(CX - r * 0.3, CY - r * 0.3, r * 1.3, [WHITE, (255, 190, 240), (140, 60, 200)])))
    if lb >= 0.2:
        cols = [(255, 190, 220), (190, 225, 255), (200, 255, 225), (255, 240, 170), (220, 200, 255)]

        def cube(k, s, cy0):
            cx = (230 if k % 2 else 1050) + hr(-170, 170, 60, k)
            cy = cy0 + hr(-60, 60, 61, k) - 18 * (k % 3)
            iso_cube(c, cx, cy + 8 * math.sin(t * 2 + k), s, mix(cols[k % 5], WHITE, 0.4), cols[k % 5],
                     mix(cols[k % 5], (90, 70, 140), 0.3))

        for k in range(18):
            cube(k, 14, 440)
        size = 138
        cap = cap_of("unb900") * size
        for li, (word, dy) in enumerate((("KESSOKU", -78), ("BAND", 64))):
            e = seg(lb, 0.2 + 0.08 * li, 0.45 + 0.08 * li)
            w = kin.combine(kin.wave(t + li, 22, 0.9, 5, 10), kin.dive(e, 0.3),
                            lambda i, n, ch: {"sy": 1 + 0.3 * math.sin(t * 5 + i * 0.9 + li * 2)})
            txt(c, word, CX, CY + dy, size, "unb900", WHITE, shader=chrome(cap, (255, 170, 230)), gfn=w,
                ext=(12, 1.2, 2.2, (80, 30, 110), (10, 4, 20)), glow=(20, (255, 120, 220), 0.4))
        for k in range(18, 30):
            cube(k, 24, 560)
    _lens_streaks(c, t, 0.13 * smooth(seg(lb, 0.2, 0.9)), seed=156, cols=(WHITE, PINK, CYAN))
    return fx.fisheye(x.arr, 0.28)


# ---------------------------------------------------------------- D15 huge words  b57.5..59.5
def s_words(x):
    c, lb, t = x.c, x.lb, x.t
    n = static_noise(x.fi // 2, block=3)
    n = cv2.resize(n[:, ::6], (W, H), interpolation=cv2.INTER_LINEAR)
    x.arr[:] = (n.astype(np.float32) * 0.55).astype(np.uint8)
    x.arr[..., 3] = 255
    _depth_specks(c, t, 0.42, seed=57, n=16, col=(160, 150, 190))
    for i in range(18):
        yy = hr(0, H, 159, i, x.fi // 2)
        c.drawRect(skia.Rect(0, yy, W, yy + hr(1, 5, 160, i)), paint(WHITE, 0.25))
    words = [(0.0, "LONELY"), (1.0, "ROCK"), (1.5, "ぼっち")]
    cur = [w for w in words if lb >= w[0]]
    if not cur:
        return None
    t0, word = cur[-1]
    q = seg(lb, t0, t0 + 0.2)
    font = "anton" if word.isascii() else "dela"
    size = 470 if word.isascii() else 330
    sx = 0.72 if word.isascii() else 1.0
    tick = x.fi // 2
    bands = [(j / 5, (j + 1) / 5 + 0.001, hr(-90, 90, tick, j) * (1 - out_cubic(q))) for j in range(5)]
    txt(c, word, CX, CY, size, font, WHITE, sx=sx * lerp(1.8, 1.0, out_expo(q)), bands=bands,
        glow=(18, WHITE, 0.3))
    for i in range(10):
        yy = hr(80, H - 80, 161, i, tick)
        c.drawRect(skia.Rect(hr(-200, 600, 162, i, tick), yy, hr(700, 1500, 163, i, tick), yy + 3), paint(WHITE, 0.7))
    _lens_streaks(c, t, 0.1 * smooth(seg(lb, 0.0, 0.92)), seed=157, cols=(WHITE, MAG, CYAN))
    return None


# ---------------------------------------------------------------- D16 circular text tunnel  b59.5..61
RINGS = ["BOCCHI THE ROCK ★ KESSOKU BAND ★ ", "ぼっち ・ 結束バンド ・ 下北沢 ・ ", "STARRY ★ LONELY ROCK ★ 90 BPM ★ "]


def s_tunnel(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 700, [(40, 14, 60), (8, 4, 14)])))
    _depth_specks(c, t, 0.5, seed=59, n=20, col=(130, 100, 170))
    _orbit_layer(c, CX, CY, 390, 210, t, 0.24, seed=59, col=(190, 100, 200))
    for k in range(7):
        u = ((k + t * 1.1) % 7) / 7
        R = 40 * math.exp(u * 3.3)
        size = R * 0.2
        a = clamp(u * 3) * clamp((1 - u) * 4)
        s = RINGS[k % 3]
        font = "unb900" if s.isascii() else "round"
        reps = max(1, int(2 * math.pi * R / max(1.0, text_w(s, size, font))))
        ring_text(c, s * reps, CX, CY, R, size, font, WHITE if k % 2 else (255, 190, 235),
                  (k * 40 + t * (30 if k % 2 else -40)) % 360, a=a)
    tick = x.fi // 2
    word = "ぼっち" if int(lb * 2) % 2 == 0 else "BOCCHI"
    font = "round" if word == "ぼっち" else "unb900"
    p = (lb * 2) % 1.0
    txt(c, word, CX, CY, 76, font, WHITE, gfn=kin.shuffle_to(seg(p, 0.0, 0.6), seed=16, tick=tick),
        glow=(16, MAG, 0.6))
    _lens_streaks(c, t, 0.14 * smooth(seg(lb, 0.0, 0.94)), seed=159, cols=(WHITE, MAG, PINK))


# ---------------------------------------------------------------- D17 speed tunnel + panic zoom  b61..62
def s_zoomtunnel(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 800, [(250, 250, 255), (160, 160, 175), (40, 40, 48)])))
    _depth_specks(c, t, 0.28 * (1 - seg(lb, 0.82, 1.0)), seed=61, n=14, col=(90, 90, 110))
    speed_lines(c, CX, CY, 120, 150, 1100, (30, 30, 36), 0.85, 61, x.fi // 2, (2, 7))
    z = in_expo(seg(lb, 0.0, 1.0))
    h = lerp(140, 2400, z)
    img(c, "panic", CX, CY + h * 0.05, h * 1.15, fx=("sil", WHITE), blur=20, a=0.7)
    img(c, "panic", CX, CY + h * 0.05, h, rot=6 * math.sin(t * 10) * (1 - z))
    c.drawCircle(CX, CY, 200 * z, paint(WHITE, 0.6 * z, blur=60))
    _lens_streaks(c, t, 0.16 * smooth(seg(lb, 0.12, 0.86)), seed=161, cols=((40, 40, 48), WHITE, (100, 100, 115)))


# ---------------------------------------------------------------- D18 static + torn hole  b62..63
def _torn(cx, cy, w, h, seed):
    p = skia.Path()
    n = 36
    for i in range(n):
        a = 2 * math.pi * i / n
        rx = w / 2 * hr(0.86, 1.08, seed, i)
        ry = h / 2 * hr(0.86, 1.08, seed, i, 1)
        (p.moveTo if i == 0 else p.lineTo)(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
    p.close()
    return p


def s_static(x):
    c, lb, t = x.c, x.lb, x.t
    x.arr[:] = static_noise(x.fi, block=2)
    _lens_streaks(c, t, 0.13 * smooth(seg(lb, 0.08, 0.92)), seed=162, cols=(WHITE, (180, 180, 190), (90, 90, 105)))
    s = out_back(seg(lb, 0.0, 0.25), 1.6)
    hole = _torn(CX, CY, 560 * s, 330 * s, 7)
    c.drawPath(xform(hole, 0, 0, 0, 1.06, CX, CY), paint((240, 236, 226)))
    c.save()
    c.clipPath(hole, skia.ClipOp.kIntersect, True)
    photo(c, "shot", CX - 300, CY - 180, 600, 360, 0.5, 0.45, 1.2 + 0.1 * lb)
    c.restore()
    c.drawPath(hole, paint((120, 110, 100), 0.6, stroke=2))
    if (x.fi // 4) % 3 != 0 and s > 0.5:
        c.drawRect(skia.Rect(CX - 96, CY - 22, CX + 96, CY + 22), paint(BLACK, 0.85))
        c.drawRect(skia.Rect(CX - 96, CY - 22, CX + 96, CY + 22), paint(TERM, stroke=2))
        txt(c, "NO SIGNAL", CX, CY, 22, "monob", TERM, track=2)


# ---------------------------------------------------------------- D19 CH_07 paper letter  b63..65
def s_letter(x):
    c, lb, t = x.c, x.lb, x.t
    x.arr[:] = (static_noise(x.fi, block=3).astype(np.float32) * 0.12).astype(np.uint8)
    x.arr[..., 3] = 255
    c.drawPaint(paint((20, 20, 24), 0.6))
    _depth_specks(c, t, 0.2, seed=63, n=14, col=(150, 150, 170))
    _lens_streaks(c, t, 0.11 * smooth(seg(lb, 0.0, 0.9)), seed=163, cols=(WHITE, TERM, (120, 120, 135)))
    if (x.fi // 10) % 2 == 0:
        c.drawRect(skia.Rect(30, 26, 132, 60), paint(BLACK, 0.6))
        c.drawRect(skia.Rect(30, 26, 132, 60), paint(TERM, stroke=2))
        label(c, "CH_07", 42, 43, 20, "monob", TERM)
    label(c, "PLAY ▶", 40, 80, 14, "monob", TERM, 0.8)
    label(c, "STARRY LIVE ●", W - 40, 43, 14, "monob", WHITE, 0.85, align="r")
    label(c, "00:" + f"{int(b2t(x.b)):02d}:{x.fi % 30:02d}", W - 40, H - 36, 16, "monob", TERM, align="r")
    letters = ["B", "ぼ", "っ", "ち", "!"]
    k = max(0, min(len(letters) - 1, math.floor((lb + 0.08) * 2)))
    flip = smooth(seg(lb, k * 0.5 - 0.08, k * 0.5 + 0.08)) if k > 0 else 1.0
    sq = abs(math.cos(flip * math.pi))
    shown = k - 1 if flip < 0.5 else k
    c.save()
    c.translate(CX, CY + 10)
    c.rotate(-7 + 3 * math.sin(t * 1.5))
    c.drawRect(skia.Rect(-196, -236, 216, 256), paint(BLACK, 0.4, blur=14))
    c.drawRect(skia.Rect(-200, -240, 200, 240), paint(shader=lin(0, -240, 0, 240, [(250, 248, 240), (222, 218, 208)])))
    ch = letters[shown]
    font = "archivo" if ch.isascii() else "dela"
    txt(c, ch, 0, 0, 330 if ch.isascii() else 250, font, (14, 14, 16),
        sy=max(0.001, sq), sx=0.95, a=smooth(seg(sq, 0, 0.08)))
    c.restore()
    close = 0.35 * (0.5 + 0.5 * math.sin(lb * math.pi)) + 0.2 * pulse(lb % 1.0, 0.1)
    for side in (-1, 1):
        for i in range(3):
            w = CX * close * (1 - i * 0.28)
            if side < 0:
                c.drawRect(skia.Rect(0, 0, w, H), paint((8, 8, 10), 0.85 - i * 0.2))
            else:
                c.drawRect(skia.Rect(W - w, 0, W, H), paint((8, 8, 10), 0.85 - i * 0.2))
    return fx.scanlines(x.arr, 0.18)


# ---------------------------------------------------------------- D20 cracked glass  b65..65.5
def _cracks(c, ix, iy, q, col=(150, 150, 165), a=0.9, seed=65, n=16, rings=4):
    for i in range(n):
        ang = hash01(seed, i) * 6.283
        p = skia.Path()
        p.moveTo(ix, iy)
        r = 0
        for j in range(6):
            r += hr(60, 160, seed + 1, i, j)
            ang += hr(-0.25, 0.25, seed + 2, i, j)
            p.lineTo(ix + math.cos(ang) * r, iy + math.sin(ang) * r)
        c.drawPath(trim_path(p, q), paint(col, a, stroke=1.6))
    for k in range(rings):
        c.drawCircle(ix, iy, (40 + k * 55) * q, paint(col, a * 0.65, stroke=1.2))


def s_glass(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (246, 246, 250))
    _lens_streaks(c, t, 0.22 * smooth(seg(lb, 0.0, 0.8)), seed=165, cols=(WHITE, (210, 220, 255), (150, 150, 190)))
    c.drawCircle(CX + 60, CY - 20, 260, paint(WHITE, 0.9, blur=80))
    _cracks(c, CX + 60, CY - 20, out_expo(seg(lb, 0.0, 0.25)), (120, 120, 138))


# ---------------------------------------------------------------- D21 restricted dialog over cracked photo  b65.5..67
LOST = ["Unfortunately, you are unable to perform for 24 hours as we suspect",
        "you have breached our Social Battery Policy.",
        "",
        "If you need temporary access to a higher anxiety limit and can prove",
        "you are not hiding in a closet, contact STARRY to discuss."]


def s_lost(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (10, 8, 14))
    img(c, "shot", CX + 20 * lb, CY, 940, blur=4, fx=("duo", (8, 6, 14), (170, 140, 170)))
    c.drawPaint(paint(BLACK, 0.3))
    _depth_specks(c, t, 0.34, seed=66, n=20, col=(120, 100, 145))
    _orbit_layer(c, CX, CY, 520, 260, t, 0.16, seed=66, col=(150, 120, 180))
    _cracks(c, 1010, 170, 1.0, WHITE, 0.5, seed=70, n=24, rings=3)
    _cracks(c, 220, 560, 1.0, WHITE, 0.35, seed=80, n=14, rings=2)
    g = skia.Path()
    gx = lerp(-300, 1500, seg(lb, 0.1, 1.4))
    g.moveTo(gx, -20)
    g.lineTo(gx + 140, -20)
    g.lineTo(gx - 200, H + 20)
    g.lineTo(gx - 340, H + 20)
    g.close()
    c.drawPath(g, paint(WHITE, 0.07, blur=18))
    _lens_streaks(c, t, 0.14 * smooth(seg(lb, 0.18, 0.92)), seed=166, cols=(WHITE, (180, 160, 210), (120, 100, 150)))
    s = out_back(seg(lb, 0.0, 0.25), 1.5)
    c.save()
    c.translate(CX + 10 * math.sin(t * 0.9), CY + 6 * math.sin(t * 0.7))
    c.rotate(0.8 * math.sin(t * 0.6))
    c.scale(s, s)
    rect = skia.Rect(-400, -170, 400, 170)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-392, -154, 408, 186), 18, 18), paint(BLACK, 0.55, blur=22))
    c.drawRRect(skia.RRect.MakeRectXY(rect, 18, 18), paint((36, 32, 44), 0.88))
    c.drawRRect(skia.RRect.MakeRectXY(rect, 18, 18), paint(WHITE, 0.16, stroke=1.5))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-370, -140, -330, -100), 8, 8), paint((236, 64, 92)))
    c.drawPath(P_poly(-350, -117, 13, 3), paint(WHITE))
    txt(c, "!", -350, -113, 13, "archivo", (236, 64, 92))
    txt(c, "Stage access temporarily restricted", -370, -70, 26, "archivo", WHITE, align="l",
        gfn=kin.scramble(seg(lb, 0.05, 0.4), seed=21, tick=x.fi // 2, lead=6))
    for i, s_ in enumerate(LOST):
        k = int(seg(lb, 0.2 + 0.12 * i, 0.5 + 0.12 * i) * (len(s_) + 0.999))
        label(c, s_[:k], -370, -26 + i * 26, 15, "mono", (214, 208, 226))
    button(c, 290, 132, 120, 40, "OK", (120, 116, 140), (60, 58, 72), WHITE, size=15)
    c.restore()
    return fx.rgb_split(x.arr, 2.0)


def s_white(x):
    bg(x.c, WHITE)


def s_black(x):
    bg(x.c, BLACK)


SHOTS = [
    (44.0, 44.5, s_burst, {}),
    (44.5, 45.5, s_clarity, {"mb": lambda lb: 4 if lb < 0.3 else 1}),
    (45.5, 46.0, s_manga, {}),
    (46.0, 47.0, s_cards, {}),
    (47.0, 47.5, s_swirl, {}),
    (47.5, 48.0, s_blobpage, {}),
    (48.0, 49.0, s_doodle, {}),
    (49.0, 50.0, s_speedcard, {}),
    (50.0, 51.0, s_redtitle, {}),
    (51.0, 52.0, s_split, {}),
    (52.0, 53.0, s_bokeh, {}),
    (53.0, 54.5, s_closeups, {}),
    (54.5, 55.5, s_bigword, {"mb": lambda lb: 3 if lb < 0.3 or 0.5 <= lb < 0.75 else 1}),
    (55.5, 56.5, s_lock, {}),
    (56.5, 57.5, s_chrome, {}),
    (57.5, 59.5, s_words, {}),
    (59.5, 61.0, s_tunnel, {}),
    (61.0, 62.0, s_zoomtunnel, {"mb": lambda lb: 3 if lb > 0.6 else 1}),
    (62.0, 63.0, s_static, {}),
    (63.0, 65.0, s_letter, {}),
    (65.0, 65.5, s_glass, {}),
    (65.5, 67.0, s_lost, {}),
    (67.0, 67.5, s_white, {}),
    (67.5, 70.0, s_black, {}),
]

TRANS = [
    (45.5, "slice", 0.12, 0.12, {}),
    (46.0, "zoom", 0.12, 0.18, {"streak": [MAG, (120, 170, 255), WHITE]}),
    (49.0, "iris", 0.25, 0.1, {"rims": [MAG, WHITE]}),
    (50.0, "flash", 0.05, 0.12, {}),
    (51.0, "whip", 0.1, 0.14, {"d": -1}),
    (52.0, "burst", 0.12, 0.12, {"col": (200, 255, 250)}),
    (54.5, "slice", 0.12, 0.12, {"d": -1}),
    (55.5, "luma", 0.2, 0.15, {}),
    (56.5, "flash", 0.1, 0.12, {}),
    (57.5, "static", 0.1, 0.12, {}),
    (59.5, "zoom", 0.15, 0.2, {"streak": [WHITE, MAG]}),
    (61.0, "zoom", 0.12, 0.18, {}),
    (62.0, "flash", 0.1, 0.12, {}),
    (63.0, "tear", 0.3, 0.15, {}),
    (65.0, "flash", 0.06, 0.1, {}),
    (65.5, "shatter", 0.02, 0.45, {"ix": CX + 60, "iy": CY - 20}),
    (67.0, "peel", 0.0, 0.5, {}),
]

FXE = [
    (44.0, "flash", 0.3, 1.0),
    (44.5, "chroma", 0.14, 4.0),
    (44.5, "slice", 0.1, 14.0),
    (45.0, "invert", 0.06, 0.3),
    (45.0, "chroma", 0.1, 3.0),
    (47.0, "chroma", 0.2, 10.0),
    (48.0, "chroma", 0.15, 6.0),
    (50.5, "chroma", 0.2, 10.0),
    (51.5, "invert", 0.06, 1.0),
    (53.0, "chroma", 0.2, 10.0),
    (54.5, "chroma", 0.2, 12.0),
    (56.4, "flash", 0.12, 0.9, {"pre": 0.1}),
    (57.5, "slice", 0.15, 90.0),
    (58.5, "chroma", 0.2, 14.0),
    (59.0, "invert", 0.06, 1.0),
    (61.0, "rchroma", 0.4, 14.0),
    (63.0, "chroma", 0.2, 8.0),
    (64.0, "slice", 0.12, 50.0),
    (64.5, "chroma", 0.2, 8.0),
]

CAM = [(44.0, "shake", 18, 0.12), (44.5, "punch", 0.08, 0.12), (45.0, "shake", 3, 0.1), (46.0, "punch", 0.05),
       (49.0, "shake", 10, 0.1), (52.0, "shake", 14, 0.1), (54.5, "punch", 0.06), (57.5, "shake", 16, 0.1),
       (58.5, "shake", 14, 0.1), (59.0, "shake", 12, 0.1), (61.0, "punch", 0.05), (62.0, "shake", 16, 0.12),
       (63.0, "shake", 8, 0.1), (65.0, "shake", 14, 0.1)]
