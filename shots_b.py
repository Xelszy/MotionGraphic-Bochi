"""Light section B: b20-44 (lavender, pastel 3D, indigo UI, fake desktop, sticky credit)."""
from __future__ import annotations

import math

import cv2
import numpy as np
import skia

import fx
import kin
from core import *  # noqa: F401,F403
from kit import *  # noqa: F401,F403

LAVD = (118, 92, 200)
LAVL = (228, 214, 255)


# ---------------------------------------------------------------- L11 error cards  b20..21
def _err_card(c, x, y, w, h, title, body, s=1.0, rot=0.0, col=PINK):
    if s <= 0.001:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.translate(-w / 2, -h / 2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(8, 10, w + 8, h + 10), 12, 12), paint((70, 30, 110), 0.3, blur=6))
    rr = skia.RRect.MakeRectXY(skia.Rect(0, 0, w, h), 12, 12)
    c.drawRRect(rr, paint(col))
    c.save()
    c.clipRRect(rr, True)
    c.drawRect(skia.Rect(0, 0, w, 32), paint(HOT))
    c.restore()
    c.drawRRect(rr, paint(WHITE, stroke=3))
    label(c, title, 14, 16, 13, "monob", WHITE)
    pw = paint(WHITE, stroke=2.5)
    c.drawLine(w - 26, 9, w - 12, 23, pw)
    c.drawLine(w - 12, 9, w - 26, 23, pw)
    warn(c, 44, 32 + (h - 32) / 2 + 4, 22, YEL, mark=INK)
    txt(c, body, 82, 32 + (h - 32) / 2, min(40, (w - 100) / max(1, len(body)) * 1.6), "round", WHITE, align="l")
    c.restore()


def _tiles(c, cols, rows, gap, fxs, seed, t, names=("shot",), drift=0.0):
    tw = (W - gap * (cols + 1)) / cols
    th = (H - gap * (rows + 1)) / rows
    for j in range(rows):
        for i in range(cols):
            k = j * cols + i
            nm = names[k % len(names)]
            photo(c, nm, gap + i * (tw + gap), gap + j * (th + gap), tw, th, hr(0.2, 0.8, seed, k),
                  hr(0.15, 0.6, seed, k, 1) + drift * math.sin(t + k) * 0.02, hr(1.0, 2.2, seed, k, 2), fx=fxs, r=4)


def s_errors(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, LAVL)
    c.save()
    camz(c, 1.06 + 0.03 * lb, dx=-10 * lb)
    _tiles(c, 4, 3, 10, ("duo", LAVD, LAVL), 7, t, ("shot", "peace", "guitar", "maid"))
    c.restore()
    c.drawPaint(paint(LAV, 0.25))
    zoom = in_expo(seg(lb, 0.8, 1.0))
    for k in range(4):
        q = seg(lb, 0.22 * k, 0.22 * k + 0.25)
        if q <= 0:
            continue
        s = out_back(q, 2.2)
        cx, cy = 420 + 60 * k, 210 + 62 * k
        if k == 3:
            s *= 1 + 4.0 * zoom
            cx, cy = lerp(cx, CX, zoom), lerp(cy, CY, zoom)
        _err_card(c, cx, cy, 440, 150, ["ERR_SOCIAL", "ERR_STAGE", "ERR_TALK", "ERR_404"][k],
                  ["STAGE FRIGHT", "TOO MANY PEOPLE", "CAN'T SPEAK", "BRAIN.EXE ?"][k], s, [-4, 3, -2, 2][k])
    pk = out_back(seg(lb, 0.1, 0.45), 1.6)
    img(c, "panic", W - 150, H + 40 - 250 * pk, 300, fx=("stk", 7, WHITE), rot=-10 + 5 * math.sin(t * 5))


# ---------------------------------------------------------------- L12 document page  b21..22
def s_page(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (255, 236, 244))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(26, 22, W - 26, H - 22), 16, 16), paint(PINK, 0.5, stroke=2))
    s = out_back(seg(lb, 0.0, 0.2), 2)
    c.save()
    c.translate(96, 96)
    c.scale(s, s)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-34, -34, 34, 34), 14, 14), paint(PINK))
    txt(c, "ぼ", 0, 2, 44, "round", WHITE)
    c.restore()
    label(c, "kessoku_notice.txt", 146, 96, 16, "monob", PINK)
    lines = ["Hitori Gotoh has left the chat.", "Please wait while we look for her inside the closet...",
             "estimated time: 30 years.  do not knock."]
    p = seg(lb, 0.05, 0.85)
    total = sum(len(s_) for s_ in lines)
    shown = int(p * total)
    y = 190
    for s_ in lines:
        k = max(0, min(len(s_), shown))
        shown -= len(s_)
        if k > 0:
            label(c, s_[:k], 96, y, 22, "mono", PINK)
            if 0 < k < len(s_) or (k == len(s_) and shown <= 0 and (x.fi // 5) % 2 == 0):
                wv = text_w(s_[:k], 22, "mono")
                c.drawRect(skia.Rect(96 + wv + 2, y - 11, 96 + wv + 13, y + 11), paint(PINK))
        y += 40
    q = seg(lb, 0.55, 0.75)
    if q > 0:
        wv = text_w("inside the closet", 22, "mono")
        x0 = 96 + text_w("Please wait while we look for her ", 22, "mono")
        c.drawRect(skia.Rect(x0 - 2, 216, x0 - 2 + wv * out_cubic(q), 244), paint(HOT, 0.28))
    for k in range(3):
        c.drawCircle(96 + 26 * k, 360, 7, paint(PINK, 0.3 + 0.7 * (int(t * 8) % 3 == k)))
    pk = out_back(seg(lb, 0.15, 0.5), 1.6)
    img(c, "panic", W - 190, H + 30 - 240 * pk, 280, rot=8 + 5 * math.sin(t * 4))


# ---------------------------------------------------------------- L13 peace close-up  b22..23
def _label_card(c, x, y, s, text, bgc, tc, rot, size=44, font="round"):
    if s <= 0.001:
        return
    w = text_w(text, size, font) + 48
    h = size * 1.45
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRect(skia.Rect(-w / 2 + 7, -h / 2 + 8, w / 2 + 7, h / 2 + 8), paint(INK, 0.25))
    c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), paint(bgc))
    txt(c, text, 0, 0, size, font, tc)
    c.restore()


def s_peace(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 900, [(255, 190, 215), PINK, HOT])))
    confetti(c, 51, 34, t, [YEL, SKY, WHITE, LAV, (86, 146, 238)], spread=700, size=(14, 34), shapes="t", spin=0.6)
    e = out_expo(seg(lb, -0.2, 0.5))
    img(c, "peace", lerp(760, 700, e) - 12 * lb, 820, 1500 * lerp(1.1, 1.0, e), ay=0.62, rot=-4 + 2 * math.sin(t * 2))
    for k, (xx, yy, txt_, bgc, tc, rot) in enumerate([(300, 520, "KESSOKU BAND", WHITE, (86, 146, 238), -8),
                                                    (1040, 150, "結束バンド", YEL, HOT, 6),
                                                    (1060, 430, "STARRY", (86, 146, 238), WHITE, -4)]):
        q = seg(lb, 0.1 + 0.18 * k, 0.4 + 0.18 * k)
        s = lerp(1.7, 1.0, out_back(q, 1.6)) if q > 0 else 0.0
        _label_card(c, xx, yy, s, txt_, bgc, tc, rot + (1 - out_cubic(q)) * 25)


# ---------------------------------------------------------------- L14 diagonal panels + 3D letters  b23..24
PANELS = [((86, 146, 238), "ぼっち", WHITE), ((70, 200, 120), "ROCK", WHITE), ((240, 70, 60), "GOTOH", WHITE),
          (PINK, "STARRY", WHITE)]


def s_panels(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (252, 244, 250))
    if lb < 0.55:
        c.save()
        c.translate(CX, CY)
        c.rotate(-28)
        for k, (col, word, tc) in enumerate(PANELS):
            q = seg(lb, -0.12 + 0.07 * k, 0.2 + 0.07 * k)
            off = lerp(-1900, 0, out_expo(q)) + 260 * lb
            y0 = -420 + k * 210
            c.drawRect(skia.Rect(-1400 + off, y0, 1400 + off, y0 + 200), paint(col))
            marquee_x = off - 600 + (k % 2 * 2 - 1) * t * 400
            for j in range(4):
                txt(c, word, marquee_x + j * 620, y0 + 100, 150, "unb900" if word.isascii() else "dela", tc, a=0.95)
        c.restore()
        img(c, "panic", 1030, 470 - 30 * out_back(seg(lb, 0.2, 0.45)), 260, fx=("stk", 6, WHITE), rot=12)
        return
    q = seg(lb, 0.5, 0.8)
    word = "BOCCHI"
    xs, total = glyph_xs(word, 190, "unb900")
    x0 = CX - total / 2
    for i, ch in enumerate(word):
        qi = seg(lb, 0.5 + 0.04 * i, 0.78 + 0.04 * i)
        if qi <= 0:
            continue
        e = out_back(qi, 1.8)
        col = [PINK, (140, 190, 250), (255, 214, 90), (150, 230, 190), LAV, (255, 170, 200)][i]
        dark = mix(col, (90, 60, 120), 0.35)
        cx = x0 + xs[i]
        cy = CY - (1 - e) * 500 + 10 * math.sin(t * 3 + i)
        c.save()
        c.translate(cx, cy)
        c.rotate((1 - e) * hr(-90, 90, 3, i) + 4 * math.sin(t * 2 + i))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-88 + 12, -100 + 14, 88 + 12, 100 + 14), 20, 20), paint(dark))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-88, -100, 88, 100), 20, 20), paint(WHITE))
        txt(c, ch, 0, 0, 150, "unb900", col, ext=(8, 1.5, 1.8, col, dark))
        c.restore()


# ---------------------------------------------------------------- L15 iso cubes  b24..25
CUBE_COLS = [(255, 176, 206), (160, 206, 255), (160, 238, 204), (255, 230, 140), (205, 185, 255)]
CUBES = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (0, 2, 0),
         (1, 2, 0), (2, 2, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (0, 0, 2)]
LETTERS = {(3, 0, 0): "ぼ", (3, 1, 0): "っ", (2, 2, 0): "ち", (1, 0, 1): "B", (0, 1, 1): "O", (0, 0, 2): "C",
           (2, 1, 0): "K", (1, 2, 0): "!"}


def _cube_scene(c, lb, t, ox=640, oy=215, s=94.0, drop=True):
    for j in range(-6, 8):
        for i in range(-6, 8):
            X = ox + (i - j) * s
            Y = oy + (i + j) * s / 2 + s
            pth = skia.Path()
            pth.moveTo(X, Y - s / 2)
            pth.lineTo(X + s, Y)
            pth.lineTo(X, Y + s / 2)
            pth.lineTo(X - s, Y)
            pth.close()
            c.drawPath(pth, paint(WHITE if (i + j) % 2 == 0 else (250, 232, 242)))
    order = sorted(range(len(CUBES)), key=lambda k: (CUBES[k][0] + CUBES[k][1], CUBES[k][2]))
    for k in order:
        gx, gy, gz = CUBES[k]
        q = seg(lb, 0.035 * k, 0.035 * k + 0.4) if drop else 1.0
        if q <= 0:
            continue
        X = ox + (gx - gy) * s
        Y = oy + (gx + gy) * s / 2 - gz * s - (1 - out_bounce(q)) * 700
        col = CUBE_COLS[(gx * 2 + gy * 3 + gz) % 5]
        iso_cube(c, X, Y, s, mix(col, WHITE, 0.35), col, mix(col, (120, 100, 160), 0.2), lw=2.5, ink=WHITE)
        ch = LETTERS.get((gx, gy, gz))
        if ch:
            c.save()
            c.concat(iso_matrix(X, Y, s))
            txt(c, ch, 0, 0, 1.25, "round", mix(col, (90, 60, 140), 0.55))
            c.restore()


def s_cubes(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (255, 246, 250))
    camz(c, 1.0 + 0.1 * lb, cy=CY + 40)
    _cube_scene(c, lb + 0.25, t)


def s_cubefig(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (255, 246, 250))
    handoff = smooth(seg(lb, 0.86, 1.22))
    c.save()
    z = 1.25 + 0.05 * lb + 0.15 * handoff + 0.5 * in_expo(seg(lb, 1.6, 2.0))
    camz(c, z, cx=CX + lerp(-120, 160, handoff), cy=CY + 40)
    _cube_scene(c, 1.0, t, drop=False)
    c.restore()
    c.drawPaint(paint(WHITE, 0.15))
    leave = handoff
    if leave < 1:
        e = out_expo(seg(lb, 0.0, 0.35))
        img(c, "guitar", lerp(1300, 900, e) + 800 * leave, H + 10 + 35 * leave, 720, ay=1.0,
            rot=-3 + 1.5 * math.sin(t * 2) + 7 * leave)
        c.save()
        c.translate(-720 * leave, 30 * leave)
        _label_card(c, 330, 470, out_back(seg(lb, 0.2, 0.45), 1.8), "HITORI GOTOH", PINK, WHITE, -7)
        _label_card(c, 400, 560, out_back(seg(lb, 0.35, 0.6), 1.8), "ギターヒーロー", (86, 146, 238), WHITE, 4, 30)
        c.restore()
    arrive = out_cubic(seg(lb, 0.94, 1.3))
    if arrive > 0:
        img(c, "full", lerp(-600, 360, arrive), H + 60 + 35 * (1 - arrive), 840, ay=1.0,
            rot=2 * math.sin(t * 2) - 5 * (1 - arrive))
    _label_card(c, 930, 200, out_back(seg(lb, 1.15, 1.4), 1.8), "LONELY ROCK", YEL, HOT, 6)
    img(c, "panic", 1080, 520, 220 * out_back(seg(lb, 1.3, 1.55), 2), fx=("stk", 6, WHITE), rot=-12)


# ---------------------------------------------------------------- L17 magenta tiles  b27..27.5  /  L18 grey wall b27.5..28
def s_tiles(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (250, 220, 240))
    cols, rows, gap = 5, 3, 8
    tw = (W - gap * (cols + 1)) / cols
    th = (H - gap * (rows + 1)) / rows
    for j in range(rows):
        for i in range(cols):
            k = j * cols + i
            q = seg(lb, -0.14 + 0.02 * (i + j), 0.02 * (i + j) + 0.06)
            sx = max(0.02, abs(math.cos((1 - out_cubic(q)) * math.pi / 2)))
            if q <= 0:
                continue
            xx, yy = gap + i * (tw + gap), gap + j * (th + gap)
            c.save()
            c.translate(xx + tw / 2, yy + th / 2)
            c.scale(sx, 1)
            photo(c, "peace", -tw / 2, -th / 2, tw, th, 0.5 + 0.05 * math.sin(k), 0.2, 1.6,
                  fx=("duo", (120, 0, 90), (255, 160, 225)), r=6)
            c.restore()


def s_wall(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (205, 205, 212))
    z = lerp(1.6, 1.0, out_expo(seg(lb, 0, 0.35)))
    c.save()
    camz(c, z)
    cols, rows, gap = 12, 7, 5
    tw = (W - gap * (cols + 1)) / cols
    th = (H - gap * (rows + 1)) / rows
    names = ("shot", "peace", "guitar", "maid", "full")
    for j in range(rows):
        for i in range(cols):
            k = j * cols + i
            photo(c, names[k % 5], gap + i * (tw + gap), gap + j * (th + gap), tw, th, hr(0.2, 0.8, 8, k),
                  hr(0.1, 0.5, 8, k, 1), hr(1.2, 2.5, 8, k, 2), fx=("gray",), r=3)
    c.restore()
    c.drawPaint(paint(WHITE, smooth(seg(lb, 0.25, 0.5))))


# ---------------------------------------------------------------- L19 indigo windows  b28..30
def _cursor(c, x, y, s=1.0, col=INK):
    p = skia.Path()
    for i, (a, b) in enumerate([(0, 0), (0, 26), (7, 20), (12, 31), (17, 29), (12, 18), (21, 18)]):
        (p.moveTo if i == 0 else p.lineTo)(x + a * s, y + b * s)
    p.close()
    c.drawPath(p, paint(WHITE))
    c.drawPath(p, paint(col, stroke=2.2))
def _wire(c, x0, y0, x1, y1, t, col=INDIGO, width=5.0, phase=0.0, alpha=0.75):
    """A legible animated connector; the dash head travels smoothly between nodes."""
    p = skia.Path()
    dx = x1 - x0
    p.moveTo(x0, y0)
    p.cubicTo(x0 + dx * 0.28, y0 + 26 * math.sin(t * 0.7 + phase),
              x1 - dx * 0.28, y1 - 26 * math.sin(t * 0.7 + phase),
              x1, y1)
    c.drawPath(p, paint(col, alpha * 0.32, stroke=width, cap=skia.Paint.kRound_Cap))
    q = (0.5 + 0.5 * math.sin(t * 2.0 + phase)) * 0.82 + 0.08
    c.drawPath(trim_path(p, q), paint(col, alpha, stroke=max(1.5, width * 0.34), cap=skia.Paint.kRound_Cap))
    c.drawCircle(lerp(x0, x1, q), lerp(y0, y1, q), width * 0.85, paint(WHITE, alpha * 0.8))


def _depth_marks(c, t, col=LAVL, count=12, spread=1.0):
    """Far-field motes that establish depth without competing with foreground text."""
    for k in range(count):
        a = hash01(81, k) * math.tau + t * (0.03 + 0.01 * (k % 3))
        rr = 150 + hash01(82, k) * 620
        xx = CX + math.cos(a) * rr * spread
        yy = CY + math.sin(a) * rr * 0.52 * spread
        r = 2.0 + hash01(83, k) * 4.0
        c.drawCircle(xx, yy, r, paint(col, 0.16 + 0.08 * math.sin(t + k)))


def _glass_reflection(c, x, y, w, h, t, depth=1.0):
    """Slow diagonal reflections for desktop/laptop panes."""
    c.save()
    c.clipRect(skia.Rect(x, y, x + w, y + h))
    sweep = (t * 34 * depth) % (w + h) - h
    p = skia.Path()
    p.moveTo(x + sweep, y)
    p.lineTo(x + sweep + 70 * depth, y)
    p.lineTo(x + sweep + h + 70 * depth, y + h)
    p.lineTo(x + sweep + h, y + h)
    p.close()
    c.drawPath(p, paint(WHITE, 0.07, blur=2))
    for i in range(3):
        xx = x + (0.2 + i * 0.3) * w + 8 * math.sin(t * 0.45 + i)
        c.drawLine(xx, y + 10, xx + 20 * depth, y + h - 10, paint(WHITE, 0.05, stroke=3))
    c.restore()


def _handoff_ribbon(c, x0, y0, x1, y1, t, col=YEL):
    """A single continuous cue linking the TV image to the credit note."""
    p = skia.Path()
    p.moveTo(x0, y0)
    p.cubicTo(lerp(x0, x1, 0.25), y0 - 35, lerp(x0, x1, 0.75), y1 + 35, x1, y1)
    c.drawPath(p, paint(col, 0.28, stroke=14, cap=skia.Paint.kRound_Cap))
    q = 0.5 + 0.5 * math.sin(t * 1.8)
    c.drawPath(trim_path(p, q), paint(WHITE, 0.8, stroke=3, cap=skia.Paint.kRound_Cap))
    c.drawCircle(lerp(x0, x1, q), lerp(y0, y1, q), 6, paint(col))




def s_windows(x):
    c, lb, t = x.c, x.lb, x.t
    bg_grid(c, WHITE, LILAC, 36, lw=1.2)
    _depth_marks(c, t, LAVL, 15, 1.05)
    # The connectors sit behind the windows, making the desktop read as one system.
    _wire(c, 370, 205, 860, 430, t, INDIGO, 7, 0.4, 0.65)
    _wire(c, 1020, 185, 860, 430, t, (86, 146, 238), 5, 1.2, 0.65)
    _wire(c, 475, 435, 860, 430, t, INDIGO, 4, 2.1, 0.55)
    _wire(c, 370, 205, 1020, 185, t, LAVD, 3, 2.8, 0.38)
    for k in range(5):
        q = 0.5 + 0.5 * math.sin(t * 1.3 + k * 1.7)
        c.drawCircle(150 + k * 250 + 18 * math.sin(t * 0.8 + k), 640 - 22 * q,
                     3 + 2 * q, paint((86, 146, 238), 0.35))
    z = 1.0 + 0.35 * out_expo(seg(lb, 1.0, 1.35)) + 0.02 * lb
    c.save()
    camz(c, z, cx=CX + 40 * seg(lb, 1.0, 1.35), cy=CY)
    for k, (sx_, sy_, r_) in enumerate([(120, 120, 40), (1170, 540, 34), (1150, 120, 22), (90, 560, 26)]):
        q = out_back(seg(lb, 0.05 * k, 0.3 + 0.05 * k), 2)
        c.drawPath(P_star(sx_, sy_, r_ * q, r_ * 0.45 * q, 5, t * 40 * (1 if k % 2 else -1)), paint((86, 146, 238)))
    c.drawPath(P_gear(1060, 300, 46, 8, 0.2, t * 30), paint(INDIGO, stroke=5))
    c.drawPath(P_arc(250, 330, 150, t * 60, 110), paint(INDIGO, stroke=10, cap=skia.Paint.kRound_Cap))
    c.drawPath(P_arc(250, 330, 120, 180 + t * 80, 70), paint((86, 146, 238), stroke=6))
    sw = skia.Path()
    sw.moveTo(-40, 610)
    sw.cubicTo(200, 480, 380, 700, 620, 590)
    c.drawPath(trim_path(sw, out_cubic(seg(lb, 0.2, 0.7))), paint(INDIGO, stroke=26))
    wins = [(210, 120, 330, 230, "maid.png"), (860, 90, 330, 200, "notes.txt"), (330, 330, 300, 210, "panic.gif"),
            (760, 330, 380, 230, "dialog")]
    for k, (wx, wy, ww, wh, title) in enumerate(wins):
        q = seg(lb, -0.06 + 0.15 * k, 0.2 + 0.15 * k)
        if q <= 0:
            continue
        s = out_back(q, 1.8)
        c.save()
        c.translate(wx + ww / 2, wy + wh / 2)
        tilt = (k - 1.5) * 1.6 + 2.2 * math.sin(t * (0.35 + k * 0.04) + k)
        c.rotate(tilt)
        c.scale(s, s)
        c.translate(-(wx + ww / 2), -(wy + wh / 2))
        rx, ry, rw, rh = window(c, wx, wy, ww, wh, title, INDIGO, WHITE, 10, 3, 26, shadow=8)
        if title == "maid.png":
            c.save()
            c.clipRect(skia.Rect(rx + 3, ry, rx + rw - 3, ry + rh - 3))
            c.drawRect(skia.Rect(rx, ry, rx + rw, ry + rh), paint(LILAC))
            img(c, "maid", rx + rw / 2, ry + rh + 150, 520, ay=1.0 - 0.0, rot=-4)
            c.restore()
        elif title == "notes.txt":
            for i in range(5):
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(rx + 16, ry + 18 + i * 28, rx + 16 + hr(120, 280, 3, i),
                                                            ry + 30 + i * 28), 5, 5), paint(LAV))
        elif title == "panic.gif":
            c.save()
            c.clipRect(skia.Rect(rx + 3, ry, rx + rw - 3, ry + rh - 3))
            img(c, "panic", rx + rw / 2, ry + rh / 2 + 8 * math.sin(t * 9), 190, rot=6 * math.sin(t * 7))
            c.restore()
        else:
            txt(c, "Go on stage?", rx + rw / 2, ry + 56, 34, "round", INDIGO)
            hov = seg(lb, 1.1, 1.3)
            press = pulse(lb - 1.55, 0.08) if lb >= 1.55 else 0
            button(c, rx + 50, ry + 110, 120, 50, "YES", INDIGO, mix(WHITE, LILAC, hov), size=18)
            button(c, rx + rw - 170 + 3 * press, ry + 110 + 3 * press, 120, 50, "NO", INDIGO,
                   mix(WHITE, INDIGO, 1.0 if lb >= 1.55 else 0), WHITE if lb >= 1.55 else INDIGO, size=18)
            cx_ = lerp(rx + rw + 60, rx + 110, out_cubic(seg(lb, 0.8, 1.15)))
            cy_ = lerp(ry + rh + 40, ry + 140, out_cubic(seg(lb, 0.8, 1.15)))
            cx_ = lerp(cx_, rx + rw - 110, inout_cubic(seg(lb, 1.3, 1.5)))
            _cursor(c, cx_, cy_)
        c.restore()
    trail = [(1010, 520), (950, 500), (900, 455), (860, 430)]
    for i in range(len(trail) - 1):
        ax, ay = trail[i]
        bx, by = trail[i + 1]
        q = smooth(seg(lb, 1.15 + i * 0.08, 1.35 + i * 0.08))
        if q > 0:
            _wire(c, ax, ay, bx, by, t, (86, 146, 238), 2.5, i + 0.4, 0.42 * q)
    c.restore()
    c.drawRect(skia.Rect(14, 14, W - 14, H - 14), paint(INDIGO, stroke=3))
    label(c, "clarity.exe", 26, 30, 12, "monob", INDIGO)
    label(c, "b" + str(int(x.b)), W - 26, 30, 12, "monob", INDIGO, align="r")


# ---------------------------------------------------------------- L20 marquee close-up  b30..32
def s_marquee(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=lin(0, 0, 0, H, [LILAC, WHITE])))
    marquee(c, "GUITAR HERO", 150, 230, "unb900", INDIGO, -t * 420, gap=90)
    marquee(c, "ギターヒーロー", 470, 190, "dela", (140, 190, 250), t * 360 - 300, gap=80)
    e = out_expo(seg(lb, -0.1, 0.4))
    img(c, "guitar", lerp(1100, 820, e) - 20 * lb, H + 90, 860 + 30 * lb, ay=1.0, rot=-2)
    for k, (wx, wy, msg) in enumerate([(90, 80, "audience detected"), (120, 420, "social battery 3%"),
                                       (560, 60, "hands shaking")]):
        q = seg(lb, 0.5 + 0.45 * k, 0.75 + 0.45 * k)
        if q <= 0:
            continue
        s = out_back(q, 2)
        c.save()
        c.translate(wx + 140, wy + 70)
        c.scale(s, s)
        c.translate(-(wx + 140), -(wy + 70))
        rx, ry, rw, rh = window(c, wx, wy, 280, 140, "WARNING", INDIGO, WHITE, 10, 3, 24, shadow=6)
        warn(c, rx + 48, ry + rh / 2 + 4, 26, RED)
        label(c, msg, rx + 86, ry + rh / 2, 16, "monob", INDIGO)
        c.restore()


# ---------------------------------------------------------------- L21 3D window stack  b32..34
def s_stack(x):
    c, lb, t = x.c, x.lb, x.t
    bg_grid(c, CREAM, (240, 226, 190), 40, lw=1.2)
    _depth_marks(c, t, (210, 190, 130), 10, 0.9)
    for k in range(5):
        _wire(c, 520 + k * 90, 250 + k * 48, 930 - k * 70, 420 - k * 34,
              t, (190, 150, 80), 3.5, k * 0.7, 0.42)
    for k in range(16):
        yy = (hash01(12, k) * H + t * hr(80, 200, 13, k)) % (H + 100) - 50
        xx = hash01(14, k) * W
        r = hr(10, 26, 15, k)
        c.save()
        c.translate(xx, yy)
        c.rotate(t * hr(-120, 120, 16, k))
        c.drawRect(skia.Rect(-r, -r, r, r), paint(YEL))
        c.restore()
    n = 6
    for k in range(n):
        q = seg(lb, 0.1 * k, 0.1 * k + 0.4)
        if q <= 0:
            continue
        e = out_expo(q)
        tx = lerp(1500, 330 + 90 * k, e)
        ty = lerp(-300, 110 + 55 * k, e)
        c.save()
        m = skia.Matrix()
        m.setAll(1.0, -0.18, tx, 0.22, 0.95, ty, 0.00012, 0.0, 1.0)
        c.concat(m)
        rx, ry, rw, rh = window(c, 0, 0, 420, 270, f"window_{k + 1:02d}", INDIGO, WHITE, 10, 3, 26, shadow=10)
        if k == n - 1 and lb > 1.0:
            c.save()
            c.clipRect(skia.Rect(rx + 3, ry, rx + rw - 3, ry + rh - 3))
            c.drawRect(skia.Rect(rx, ry, rx + rw, ry + rh), paint(LILAC))
            img(c, "full", rx + rw / 2, ry + 70 + 440 * (1 - out_expo(seg(lb, 1.0, 1.3))), 620, ay=0.1)
            c.restore()
        _glass_reflection(c, rx, ry, rw, rh, t, 0.55 + 0.08 * k)
        c.restore()
    for k in range(6):
        q = out_back(seg(lb, 1.1 + 0.08 * k, 1.35 + 0.08 * k), 2.2)
        if q > 0:
            warn(c, hr(120, W - 120, 17, k), hr(80, H - 80, 18, k), 34 * q, RED, rot=hr(-20, 20, 19, k))


def s_overload(x):
    c, lb, t = x.c, x.lb, x.t
    bg_grid(c, WHITE, (236, 236, 244), 40, lw=1.2)
    _depth_marks(c, t, (180, 180, 205), 9, 0.82)
    for k in range(4):
        rr = 170 + k * 92 + 18 * math.sin(t * 0.65 + k)
        c.drawCircle(CX, CY, rr, paint((170, 120, 220), 0.16, stroke=2.5))
    _wire(c, 120, 120, 420, 310, t, (150, 110, 210), 4, 0.3, 0.35)
    _wire(c, 1160, 110, 880, 300, t, (150, 110, 210), 4, 1.4, 0.35)
    bg_grid(c, WHITE, (236, 236, 244), 40, lw=1.2)
    for k in range(18):
        q = out_back(seg(lb, 0.04 * k, 0.04 * k + 0.25), 2)
        if q <= 0:
            continue
        xx, yy = hr(60, W - 60, 21, k), hr(50, H - 50, 22, k) + 6 * math.sin(t * 2 + k)
        r = hr(12, 30, 23, k) * q
        if k % 3 == 0:
            c.drawPath(P_poly(xx, yy, r, 3, t * 40 + k * 20), paint(RED, stroke=4))
        else:
            c.drawPath(P_poly(xx, yy, r, 3, t * 30 + k * 20), paint(RED))
        c.drawCircle(xx + 40, yy + 30, 4, paint(RED, 0.7))
    if lb < 1.0:
        q = seg(lb, 0.4, 0.6)
        if q > 0:
            s = out_back(q, 2)
            c.save()
            c.translate(CX, CY)
            c.scale(s, s)
            rx, ry, rw, rh = window(c, -220, -110, 440, 220, "system", INDIGO, WHITE, 10, 3, 26)
            for i in range(3):
                p = seg(lb, 0.5 + 0.12 * i, 0.62 + 0.12 * i)
                if p > 0:
                    txt(c, "OVERLOAD!", rx + 30, ry + 42 + i * 52, 40, "monob", RED, align="l", gfn=kin.typ(p))
            c.restore()
        return
    q = seg(lb, 1.0, 1.15)
    s = out_back(q, 1.8)
    c.save()
    c.translate(CX, CY)
    c.scale(s, s)
    rx, ry, rw, rh = window(c, -560, -250, 1120, 500, "type.exe", INDIGO, WHITE, 14, 4, 34, shadow=12)
    word = "BOCCHI"
    size = 250
    xs, total = glyph_xs(word, size, "round")
    x0 = -total / 2
    p = seg(lb, 1.1, 1.7)
    k = int(p * (len(word) + 0.999))
    txt(c, word, x0, 40, size, "round", INDIGO, align="l", gfn=kin.combine(kin.typ(p), kin.jitter(x.fi // 3, 1.5)))
    if k >= 2:
        pop = out_back(seg(lb, 1.1 + 2 / 7 * 0.6, 1.35 + 2 / 7 * 0.6), 2)
        op = text_path("O", x0 + xs[1], 40, size, "round")
        c.save()
        c.clipPath(op, skia.ClipOp.kIntersect, True)
        c.drawPaint(paint(LILAC))
        img(c, "panic", x0 + xs[1], 50, 220 * pop, rot=10 * math.sin(t * 6))
        c.restore()
        c.drawPath(op, paint(INDIGO, stroke=6))
    cxp = x0 + (xs[k - 1] + glyph("round", word[k - 1])[1] * size / REF / 2 if k > 0 else 0) + 10
    if (x.fi // 5) % 2 == 0:
        c.drawRect(skia.Rect(cxp, -60, cxp + 12, 130), paint(INDIGO))
    c.restore()


# ---------------------------------------------------------------- L23 fake desktop sequence  b36..40
def _wallpaper(c, t):
    c.drawPaint(paint(shader=lin(0, 0, 0, H, [(255, 176, 120), (240, 110, 150), (96, 60, 160)], [0, 0.55, 1])))
    c.drawCircle(W * 0.7, H * 0.52, 110, paint((255, 230, 170), 0.9))
    c.drawCircle(W * 0.7, H * 0.52, 190, paint((255, 200, 150), 0.4, blur=40))
    p = skia.Path()
    p.moveTo(0, H)
    for i in range(13):
        p.lineTo(i * W / 12, H * 0.66 + 40 * math.sin(i * 1.3) + 18 * math.sin(i * 3.1))
    p.lineTo(W, H)
    p.close()
    c.drawPath(p, paint((70, 40, 110)))
    # Long, slow wallpaper bands establish a distant plane behind the UI.
    for k in range(4):
        yy = H * (0.18 + 0.12 * k) + 10 * math.sin(t * 0.18 + k)
        c.drawLine(-80, yy, W + 80, yy + 34 * math.sin(t * 0.13 + k),
                   paint((255, 220, 240), 0.08, stroke=2))


def _browser(c, x, y, w, h, t, url="kessoku.band/live"):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 6, y + 10, x + w + 6, y + h + 10), 10, 10), paint(INK, 0.3, blur=10))
    rr = skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), 10, 10)
    c.drawRRect(rr, paint(WHITE))
    c.save()
    c.clipRRect(rr, True)
    c.drawRect(skia.Rect(x, y, x + w, y + 38), paint((232, 232, 238)))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        c.drawCircle(x + 16 + i * 18, y + 19, 6, paint(col))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 80, y + 9, x + w - 20, y + 29), 10, 10), paint(WHITE))
    label(c, url, x + 94, y + 19, 12, "mono", GREY)
    photo(c, "shot", x + 16, y + 52, w * 0.45, h - 70, 0.5, 0.4, 1.2, r=6)
    for i in range(6):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + w * 0.5, y + 60 + i * 24, x + w * 0.5 + hr(80, w * 0.42, 5, i),
                                                    y + 72 + i * 24), 5, 5), paint((220, 220, 230)))
    c.restore()


def _explorer(c, x, y, w, h):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 6, y + 10, x + w + 6, y + h + 10), 10, 10), paint(INK, 0.3, blur=10))
    rr = skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), 10, 10)
    c.drawRRect(rr, paint((250, 250, 252)))
    c.save()
    c.clipRRect(rr, True)
    c.drawRect(skia.Rect(x, y, x + w, y + 32), paint((60, 60, 72)))
    label(c, "C:/bocchi/songs", x + 12, y + 16, 12, "mono", WHITE)
    for i in range(8):
        cx_, cy_ = x + 30 + (i % 4) * (w - 40) / 4, y + 60 + (i // 4) * 80
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx_, cy_, cx_ + 44, cy_ + 36), 5, 5),
                    paint([YEL, SKY, PINK, GREEN][i % 4]))
        label(c, f"demo_{i:02d}", cx_, cy_ + 50, 10, "mono", INK)
    c.restore()


def _taskbar(c, t):
    c.drawRect(skia.Rect(0, H - 44, W, H), paint((20, 18, 30), 0.82))
    for i in range(7):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(420 + i * 62, H - 36, 448 + i * 62, H - 8), 7, 7),
                    paint([PINK, SKY, YEL, GREEN, LAV, ORANGE, WHITE][i]))
    label(c, "19:24", W - 30, H - 22, 14, "monob", WHITE, align="r")
def _desktop(c, t, lb, mode):
    _wallpaper(c, t)
    _wire(c, 260, 180, 470 - 30 * lb, 230, t, (255, 230, 180), 5, 0.2, 0.42)
    _wire(c, 470 - 30 * lb, 230, 1050, 325, t, (255, 210, 150), 4, 1.0, 0.34)
    if mode == 2:
        _wire(c, 1050, 325, 1030, 150, t, YEL, 3, 1.8, 0.5)
    if mode >= 1:
        _explorer(c, 70 + 10 * math.sin(t), 70, 420, 250)
    _browser(c, 420 - 30 * lb, 150, 640, 380, t)
    _glass_reflection(c, 420 - 30 * lb, 150, 640, 380, t, 0.8)
    if mode == 2:
        q = out_back(seg(lb, 0.0, 0.2), 1.8)
        c.save()
        c.translate(1030, 150)
        c.scale(q, q)
        c.drawRect(skia.Rect(-120, -80, 130, 90), paint(INK, 0.25, blur=8))
        c.drawRect(skia.Rect(-125, -85, 125, 85), paint((255, 236, 120)))
        c.drawRect(skia.Rect(-125, -85, 125, -62), paint((240, 214, 80)))
        s = type_on("practice guitar", seg(lb, 0.05, 0.4), tick=x_tick(t))
        label(c, s, -108, -20, 20, "monob", INK)
        label(c, "6 hours/day", -108, 20, 16, "mono", INK)
        c.restore()
    _taskbar(c, t)


def x_tick(t):
    return int(t * 6)


def _laptop(x):
    """Keep both laptop shots on one desktop clock and camera move."""
    lb = x.b - 36.0
    t = lb * SPB
    tilt = lerp(1.0, 0.4, smooth(seg(lb, 0.15, 1.1)))
    push = 0.02 * lb + 0.22 * smooth(seg(lb, 0.3, 2.0))
    arr, s, cc = layer()
    cc.clear(rgba(BLACK))
    _desktop(cc, t, lb, 1)
    room = np.zeros((H, W, 4), np.uint8)
    room[..., 3] = 255
    rc = surface(room).getCanvas()
    rc.drawPaint(paint(shader=rad(W * 0.5, H * 0.3, 900, [(92, 70, 80), (30, 24, 30), (10, 8, 12)])))
    z = 1.0 + push
    j = 4 * math.sin(t * 1.7)
    q = [(170 - 60 * tilt, 60 + j), (1130 + 20 * tilt, 40 - j), (1150 + 40 * tilt, 560 + j), (130 - 80 * tilt, 600 - j)]
    q = [(CX + (a - CX) * z, CY + (b - CY) * z) for a, b in q]
    bez = skia.Path()
    bez.moveTo(q[0][0] - 18, q[0][1] - 18)
    bez.lineTo(q[1][0] + 18, q[1][1] - 18)
    bez.lineTo(q[2][0] + 18, q[2][1] + 22)
    bez.lineTo(q[3][0] - 18, q[3][1] + 22)
    bez.close()
    rc.drawPath(bez, paint((22, 22, 26)))
    base = skia.Path()
    base.moveTo(q[3][0] - 30, q[3][1] + 22)
    base.lineTo(q[2][0] + 30, q[2][1] + 22)
    base.lineTo(q[2][0] + 160, H + 40)
    base.lineTo(q[3][0] - 180, H + 40)
    base.close()
    rc.drawPath(base, paint((48, 44, 52)))
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (W, 0), (W, H), (0, H)]), np.float32(q))
    warped = cv2.warpPerspective(arr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    over(room, warped)
    glow = cv2.GaussianBlur(cv2.resize(warped, (W // 8, H // 8)), (0, 0), 6)
    glow = cv2.resize(glow, (W, H))
    # Near plane: a slow desk reflection tracks the laptop's perspective.
    for k in range(7):
        xx = lerp(q[3][0], q[2][0], (k + 1) / 8.0) + 16 * math.sin(t * 0.35 + k)
        rc.drawLine(xx, q[3][1] + 18, xx + 26, H + 20,
                    paint((170, 150, 180), 0.11, stroke=3))
    room[..., :3] = np.clip(room[..., :3].astype(np.int16) + (glow[..., :3] * 0.35).astype(np.int16), 0, 255).astype(np.uint8)
    blurred = cv2.GaussianBlur(room, (0, 0), 7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    m = np.clip((np.sqrt(((xx - CX) / (W * 0.62)) ** 2 + ((yy - CY) / (H * 0.62)) ** 2) - 0.55) * 2.5, 0, 1)
    return fx.mask_mix(room, blurred, m)


def s_desk_a(x):
    return _laptop(x)


def s_desk_b(x):
    return _laptop(x)


def s_desk_c(x):
    c, lb, t = x.c, x.lb, x.t
    camz(c, 1.05 + 0.04 * lb)
    _desktop(c, t, lb, 2)


def s_player(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (16, 16, 22))
    c.drawRect(skia.Rect(0, 0, 230, H), paint((10, 10, 14)))
    for i, s_ in enumerate(["Home", "Search", "Library", "kessoku", "starry", "demo tapes"]):
        label(c, s_, 30, 60 + i * 38, 15, "monob", (200, 200, 210) if i != 3 else (30, 215, 96))
    photo(c, "shot", 280, 70, 250, 250, 0.5, 0.45, 1.3, r=10)
    label(c, "PLAYLIST", 560, 90, 13, "monob", GREY)
    txt(c, "track_01", 560, 150, 64, "archivo", WHITE, align="l", gfn=kin.rail(seg(lb, 0, 0.4), 300))
    label(c, "kessoku band · 1 song · 0:45", 560, 214, 14, "mono", GREY)
    c.drawCircle(590, 280, 30, paint((30, 215, 96)))
    tri = P_poly(594, 280, 14, 3, 90)
    c.drawPath(tri, paint(BLACK))
    for i in range(24):
        h = 12 + 38 * abs(math.sin(t * 7 + i * 0.7)) * (0.4 + 0.6 * hash01(i, int(t * 8)))
        c.drawRect(skia.Rect(660 + i * 12, 300 - h, 668 + i * 12, 300), paint((30, 215, 96), 0.85))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(280, 360, 1200, 366), 3, 3), paint((70, 70, 80)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(280, 360, 280 + 920 * (0.3 + 0.3 * lb), 366), 3, 3), paint(WHITE))
    names = ("peace", "guitar", "maid", "full", "panic")
    for i in range(5):
        photo(c, names[i], 280 + i * 186, 400, 170, 170, 0.5, 0.25, 1.0,
              fx=("duo", (30, 20, 60), [PINK, SKY, YEL, GREEN, LAV][i]), r=8)
    label(c, "now playing", W - 30, 30, 12, "mono", GREY, align="r")


def s_splash(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX * 1.3, CY, 900, [(255, 90, 160), (120, 40, 200), (20, 10, 60)])))
    for i in range(40):
        a = hash01(4, i) * 6.283 + t * 0.2
        r0 = hr(200, 400, 5, i)
        c.drawLine(CX * 1.3 + math.cos(a) * r0, CY + math.sin(a) * r0, CX * 1.3 + math.cos(a) * 1400,
                   CY + math.sin(a) * 1400, paint((255, 220, 255), 0.25, stroke=hr(2, 8, 6, i)))
    img(c, "guitar", 930, H + 40, 760 * (1 + 0.05 * lb), ay=1.0, fx=("tri", (40, 10, 70), (255, 60, 170), (120, 250, 255)))
    txt(c, "LONELY", 360, 250, 150, "unb900", YEL, ext=(10, 2, 3, (255, 120, 40), (140, 30, 80)), rot=-6,
        gfn=kin.dive(seg(lb, -0.2, 0.12)))
    txt(c, "ROCK", 330, 400, 170, "unb900", WHITE, ext=(10, 2, 3, (120, 250, 255), (40, 20, 120)), rot=-6,
        gfn=kin.dive(seg(lb, -0.12, 0.2)))
    if (x.fi // 4) % 2 == 0:
        label(c, "PRESS START", 330, 540, 22, "monob", WHITE, align="c", track=4)


def s_login(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (12, 12, 16))
    c.drawCircle(CX, 150, 44, paint(GREY, stroke=10))
    c.drawCircle(CX, 150, 14, paint(GREY))
    sh = 8 * pulse(lb % 0.25, 0.05)
    c.drawRect(skia.Rect(0, CY - 50 + sh, W, CY + 50 + sh), paint((200, 20, 30)))
    txt(c, "LOGIN ERROR", CX + hr(-6, 6, x.fi), CY - 12 + sh, 30, "monob", WHITE, track=3)
    label(c, "error: you are not allowed to go outside today.", CX, CY + 24 + sh, 13, "mono", (255, 200, 200), align="c")
    return fx.rgb_split(x.arr, 6 + 10 * pulse(lb % 0.25, 0.06), 0)


# ---------------------------------------------------------------- L24 dark TV room  b40..42
def s_tv(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=rad(CX, CY, 800, [(34, 30, 44), (12, 10, 16), (4, 4, 6)])))
    # Far room plane: quiet shelves and a cable-like glow frame the screen.
    for k in range(4):
        yy = 74 + k * 118 + 8 * math.sin(t * 0.22 + k)
        c.drawLine(110, yy, 1170, yy, paint((120, 100, 145), 0.16, stroke=3))
        c.drawCircle(170 + k * 230, yy - 10, 5 + 2 * math.sin(t * 0.3 + k), paint((210, 170, 130), 0.2))
    _depth_marks(c, t, (150, 120, 170), 8, 0.75)
    z = 1.0 + 0.18 * lb
    camz(c, z, cy=CY - 10)
    sx0, sy0, sw, sh_ = 330, 120, 620, 360
    names = ("shot", "peace", "maid", "shot", "guitar", "full")
    slide = max(0, math.floor(lb * 2))
    k = slide % len(names)
    previous = (slide - 1) % len(names) if slide else k
    reveal = smooth(seg(lb, slide * 0.5, slide * 0.5 + 0.2)) if slide else 1.0
    colors = [(240, 160, 190), (160, 200, 250), (250, 220, 150), (200, 180, 255), (170, 240, 210), (250, 180, 160)]
    col = mix(colors[previous], colors[k], reveal)
    c.drawRect(skia.Rect(sx0 - 80, sy0 - 60, sx0 + sw + 80, sy0 + sh_ + 80), paint(col, 0.22, blur=60))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx0 - 22, sy0 - 22, sx0 + sw + 22, sy0 + sh_ + 22), 14, 14), paint((18, 18, 22)))
    c.drawRect(skia.Rect(sx0, sy0, sx0 + sw, sy0 + sh_), paint((30, 30, 36)))
    if reveal < 1:
        photo(c, names[previous], sx0, sy0, sw, sh_, hr(0.3, 0.7, previous), hr(0.2, 0.5, previous, 1), 1.4)
    c.save()
    c.clipRect(skia.Rect(sx0, sy0, sx0 + sw * reveal, sy0 + sh_))
    c.drawRect(skia.Rect(sx0, sy0, sx0 + sw, sy0 + sh_), paint((30, 30, 36)))
    drift = smooth(seg(lb, slide * 0.5, (slide + 1) * 0.5))
    photo(c, names[k], sx0, sy0, sw, sh_, hr(0.3, 0.7, k), hr(0.2, 0.5, k, 1), 1.3 + 0.1 * drift)
    c.restore()
    for yy in range(sy0, sy0 + sh_, 4):
        c.drawLine(sx0, yy, sx0 + sw, yy, paint(BLACK, 0.18, stroke=1))
    c.drawRect(skia.Rect(sx0, sy0, sx0 + sw, sy0 + sh_), paint(WHITE, 0.06))
    c.drawRect(skia.Rect(CX - 60, sy0 + sh_ + 22, CX + 60, sy0 + sh_ + 60), paint((20, 20, 24)))
    c.drawRect(skia.Rect(CX - 160, sy0 + sh_ + 58, CX + 160, sy0 + sh_ + 70), paint((24, 24, 28)))
    c.drawRect(skia.Rect(-400, sy0 + sh_ + 70, W + 400, H + 400), paint((14, 12, 16)))
    _glass_reflection(c, sx0, sy0, sw, sh_, t, 0.65)
    handoff = smooth(seg(lb, 1.35, 1.95))
    if handoff > 0:
        _handoff_ribbon(c, sx0 + sw - 24, sy0 + sh_ - 28, W - 88, H - 38, t, (240, 190, 110))
    label(c, "▶ SLIDESHOW", sx0 + 12, sy0 + 20, 12, "monob", WHITE, 0.7)


# ---------------------------------------------------------------- L25 sticky-note credit  b42..44 (CREDIT)
def s_sticky(x):
    c, lb, t = x.c, x.lb, x.t
    c.drawPaint(paint(shader=lin(0, 0, 0, H, [(130, 190, 250), (185, 222, 255)])))
    _depth_marks(c, t, (255, 255, 255), 7, 0.7)
    # The handoff enters from the TV's direction before the note settles.
    handoff = smooth(seg(lb, -0.02, 0.36))
    if handoff > 0:
        _handoff_ribbon(c, 150, 530, 330, 320, t, (255, 205, 100))
    camz(c, 1.0 + 0.05 * lb)
    c.drawRect(skia.Rect(0, 0, W, 24), paint(WHITE, 0.35))
    label(c, "clarity.exe", 14, 12, 11, "monob", INK, 0.7)
    label(c, "Sat 19:24", W - 14, 12, 11, "monob", INK, 0.7, align="r")
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(40, 56, 150, 166), 12, 12), paint(WHITE, 0.9))
    c.drawRect(skia.Rect(40, 56, 150, 84), paint(RED))
    label(c, "JUL", 95, 70, 12, "monob", WHITE, align="c")
    txt(c, "21", 95, 126, 44, "archivo", INK)
    for i, col in enumerate([YEL, PINK, GREEN]):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(62, 200 + i * 90, 128, 262 + i * 90), 10, 10), paint(col))
        label(c, ["notes", "demo.wav", "setlist"][i], 95, 276 + i * 90, 11, "mono", INK, align="c")
    wx, wy, ww, wh = 330, 150, 760, 330
    enter = out_back(seg(lb, -0.04, 0.42), 1.15)
    settle = smooth(seg(lb, -0.04, 0.48))
    c.save()
    c.translate(wx + ww / 2 - 160 * (1 - enter), wy + wh / 2 + 100 * (1 - enter))
    c.rotate(-7 * (1 - settle))
    scale = lerp(0.82, 1.0, enter)
    c.scale(scale, scale)
    c.translate(-(wx + ww / 2), -(wy + wh / 2))
    c.drawRect(skia.Rect(wx + 10, wy + 14, wx + ww + 10, wy + wh + 14), paint(INK, 0.25, blur=10))
    c.drawRect(skia.Rect(wx, wy, wx + ww, wy + wh), paint((255, 236, 120)))
    c.drawRect(skia.Rect(wx, wy, wx + ww, wy + 34), paint((240, 214, 80)))
    label(c, "Sticky Notes", wx + 14, wy + 17, 13, "monob", INK, 0.8)
    for i in range(3):
        c.drawCircle(wx + ww - 18 - i * 22, wy + 17, 6, paint(INK, 0.5, stroke=1.8))
    size = 70
    ty = wy + 150
    tx = wx + 50
    first = "who made this?"
    final = "made by iXelszy"
    if lb < 0.95:
        s = first[:int(seg(lb, 0.0, 0.55) * (len(first) + 0.999))]
        sel = seg(lb, 0.62, 0.8)
        if sel > 0:
            wv = text_w(s, size, "round")
            c.drawRect(skia.Rect(tx - 4, ty - 50, tx - 4 + (wv + 8) * out_cubic(sel), ty + 50), paint((86, 146, 238), 0.45))
    else:
        s = final[:int(seg(lb, 1.0, 1.55) * (len(final) + 0.999))]
    txt(c, s, tx, ty, size, "round", INK, align="l")
    wv = text_w(s, size, "round")
    if lb < 1.55 or (x.fi // 6) % 2 == 0:
        c.drawRect(skia.Rect(tx + wv + 6, ty - 44, tx + wv + 12, ty + 44), paint(INK))
    q = seg(lb, 1.65, 1.8)
    if q > 0:
        txt(c, ":)", tx + 10, ty + 110, 70 * out_back(q, 2.4), "round", HOT, align="l", rot=-8)
        for k in range(5):
            qq = out_back(seg(lb, 1.7 + 0.03 * k, 1.85 + 0.03 * k), 2.5)
            c.drawPath(P_sparkle(tx + 150 + k * 110, ty + 100 + 20 * math.sin(k * 2), 16 * qq, t * 60), paint(WHITE))
    c.restore()


SHOTS = [
    (20.0, 21.0, s_errors, {}),
    (21.0, 22.0, s_page, {}),
    (22.0, 23.0, s_peace, {}),
    (23.0, 24.0, s_panels, {"mb": lambda lb: 3 if lb < 0.5 else 1}),
    (24.0, 25.0, s_cubes, {}),
    (25.0, 27.0, s_cubefig, {}),
    (27.0, 27.5, s_tiles, {}),
    (27.5, 28.0, s_wall, {}),
    (28.0, 30.0, s_windows, {}),
    (30.0, 32.0, s_marquee, {}),
    (32.0, 34.0, s_stack, {"mb": lambda lb: 3 if lb < 0.9 else 1}),
    (34.0, 36.0, s_overload, {}),
    (36.0, 36.5, s_desk_a, {}),
    (36.5, 38.0, s_desk_b, {}),
    (38.0, 38.5, s_desk_c, {}),
    (38.5, 39.0, s_player, {}),
    (39.0, 39.5, s_splash, {}),
    (39.5, 40.0, s_login, {}),
    (40.0, 42.0, s_tv, {}),
    (42.0, 44.0, s_sticky, {}),
]

TRANS = [
    (21.0, "zoom", 0.1, 0.18, {}),
    (22.0, "whip", 0.1, 0.16, {"d": -1}),
    (24.0, "slice", 0.2, 0.15, {}),
    (25.0, "flash", 0.05, 0.12, {}),
    (27.0, "pixelate", 0.12, 0.12, {}),
    (30.0, "blinds", 0.25, 0.1, {}),
    (32.0, "checker", 0.3, 0.1, {}),
    (34.0, "whip", 0.1, 0.16, {"d": 1}),
    (36.0, "zoom", 0.15, 0.2, {}),
    (38.0, "push", 0.1, 0.1, {"d": 1, "axis": "y"}),
    (40.0, "glitch", 0.25, 0.25, {}),
    (42.0, "flash", 0.08, 0.16, {}),
]

FXE = [
    (22.0, "chroma", 0.2, 6.0),
    (23.0, "chroma", 0.25, 8.0),
    (28.0, "chroma", 0.2, 6.0),
    (29.0, "chroma", 0.15, 4.0),
    (33.0, "chroma", 0.2, 6.0),
    (35.0, "chroma", 0.2, 6.0),
    (38.5, "slice", 0.12, 50.0),
    (39.0, "chroma", 0.2, 10.0),
    (39.5, "invert", 0.1, 1.0),
    (39.5, "slice", 0.2, 80.0),
]

CAM = [(20.0, "punch", 0.04), (21.0, "punch", 0.03), (22.0, "punch", 0.04), (23.0, "shake", 10, 0.1),
       (24.0, "punch", 0.03), (25.0, "punch", 0.04), (26.0, "punch", 0.04), (28.0, "punch", 0.04),
       (29.0, "punch", 0.05), (30.0, "punch", 0.04), (32.0, "punch", 0.04), (34.0, "punch", 0.03),
       (35.0, "punch", 0.05), (36.0, "punch", 0.03), (38.0, "punch", 0.03), (39.5, "shake", 16, 0.12),
       (40.0, "punch", 0.03), (42.0, "punch", 0.03)]
