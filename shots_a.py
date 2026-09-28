"""Light section A: b0-20 (white / pastel)."""
from __future__ import annotations

import math

import skia

import kin
from core import *  # noqa: F401,F403
from kit import *  # noqa: F401,F403



def _light_depth(c, t, fade=1.0, seed=0, flow=0.0, front=False):
    """Small pastel depth cues kept near the edges of the type/image work."""
    if fade <= 0.001:
        return
    cols = (SKY, LAV, PINK, BLUE)
    if not front:
        # Distant haze drifts slowly, while the midground dashes travel faster.
        for k in range(8):
            d = 0.16 + 0.055 * (k % 6)
            xx = (hash01(70 + seed, k) * (W + 180) + t * (10 + 28 * d) + flow * 180 * d) % (W + 180) - 90
            yy = hash01(71 + seed, k) * H + 12 * math.sin(t * (0.7 + d) + k)
            rr = 18 + 34 * d
            c.drawCircle(xx, yy, rr, paint(cols[k % len(cols)], fade * (0.045 + 0.025 * d), blur=8 + 10 * d))
        for k in range(7):
            d = 0.38 + 0.07 * (k % 5)
            xx = (hash01(72 + seed, k) * (W + 220) + t * (32 + 70 * d) + flow * 360 * d) % (W + 220) - 110
            yy = 86 + hash01(73 + seed, k) * (H - 172) + 20 * math.sin(t * 1.4 + k * 1.7)
            pth = skia.Path()
            pth.moveTo(xx, yy)
            pth.lineTo(xx + 58 + 84 * d, yy - 8 - 24 * d)
            c.drawPath(pth, paint(cols[(k + 1) % len(cols)], fade * (0.12 + 0.035 * d), stroke=2.0 + 3.0 * d))
    else:
        # Near streaks are sparse and leave the frame in the same direction as
        # the next shot's travel, making the cut feel intentional.
        for k in range(5):
            d = 0.72 + 0.07 * k
            phase = hash01(74 + seed, k) * (W + 360)
            xx = (phase + t * (130 + 85 * d) + flow * 420) % (W + 520) - 260
            yy = 78 + hash01(75 + seed, k) * (H - 156) + 34 * math.sin(t * 2.2 + k)
            pth = skia.Path()
            pth.moveTo(xx, yy)
            pth.lineTo(xx + 120 + 115 * d, yy - 18 - 40 * d)
            c.drawPath(pth, paint(cols[(k + 2) % len(cols)], fade * (0.17 - 0.012 * k), stroke=2.5 + 2.5 * d))

# ---------------------------------------------------------------- L0 intro  b-0.25..4
def s_intro(x):
    c, lb = x.c, x.b
    bg(c, WHITE)
    depth = smooth(seg(lb, 0.0, 0.6)) * (1 - smooth(seg(lb, 3.25, 3.72)))
    _light_depth(c, x.t, depth, seed=1, flow=smooth(seg(lb, 2.4, 3.72)))
    _light_depth(c, x.t, depth * 0.72, seed=2, flow=smooth(seg(lb, 2.4, 3.72)), front=True)
    if lb < 0 or lb >= 3.72:
        return
    tick = x.fi // 3
    z = 1 + 0.3 * in_cubic(seg(lb, 0.0, 3.72))
    camz(c, z, rot=-1.5 * in_cubic(seg(lb, 2.5, 3.72)))
    rec = 1.0 if (x.fi // 8) % 2 == 0 else 0.2
    c.drawCircle(66, 58, 6, paint(RED, rec))
    label(c, "REC", 80, 58, 14, "monob", BLUE)
    label(c, f"00:00:{int(b2t(x.b)):02d}:{x.fi % 30:02d}", W - 66, 58, 14, "mono", BLUE, align="r")
    label(c, "90 BPM", W - 66, H - 58, 13, "mono", BLUE, 0.8, align="r")
    for bx, by, sx, sy in ((40, 36, 1, 1), (W - 40, 36, -1, 1), (40, H - 36, 1, -1), (W - 40, H - 36, -1, -1)):
        pth = skia.Path()
        pth.moveTo(bx, by + sy * 22)
        pth.lineTo(bx, by)
        pth.lineTo(bx + sx * 22, by)
        c.drawPath(pth, paint(BLUE, 0.7, stroke=2))
    y = CY - 8
    if lb < 1.0:
        s = "clarity.exe"
        p = seg(lb, 0.05, 0.8)
        k = int(p * (len(s) + 0.999))
        txt(c, s, CX, y, 30, "monob", BLUE, gfn=kin.typ(p))
        full = text_w(s, 30, "monob")
        cxp = CX - full / 2 + text_w(s[:k], 30, "monob") + 4
        if (x.fi // 5) % 2 == 0 or p < 1:
            c.drawRect(skia.Rect(cxp, y - 13, cxp + 13, y + 13), paint(BLUE))
    elif lb < 2.5:
        pct = int(64 * out_cubic(seg(lb, 1.1, 2.3)))
        txt(c, f"LOADING {pct:02d}%", CX, y, 30, "monob", BLUE, gfn=kin.flip(seg(lb, 1.0, 1.4), seed=3, tick=tick))
        progress(c, CX - 180, y + 34, 360, 8, pct / 100, BLUE, WHITE)
    else:
        q = seg(lb, 2.5, 3.3)
        n = 1 + int(q * 6)
        col = seg(lb, 3.35, 3.72)
        cl = in_back(col, 2.0)

        def g(i, nn, ch):
            j = i // 3
            return {"col": BLUE if j % 2 == 0 else PINK, "s": out_back(clamp((q * 6 - j + 1) * 2.5), 3.0)}
        txt(c, "ぼっち" * n, CX, y, 32, "round", BLUE, track=lerp(2, 10, q), sx=max(0.001, 1 - cl), gfn=g)
    reveal = smooth(seg(lb, 0.45, 0.85))
    leave = smooth(seg(lb, 3.3, 3.6))
    visible = reveal * (1 - leave)
    if visible > 0:
        drift = inout_sine(seg(lb, 0.45, 3.6))
        c.save()
        c.translate(-12 * (1 - reveal) + 12 * leave, 6 * (1 - reveal) - 6 * leave)
        c.clipRect(skia.Rect(64, H - 180, 236, H - 180 + 140 * visible))
        photo(c, "shot", 66, H - 178, 168, 112, u=lerp(0.42, 0.57, drift),
              v=lerp(0.38, 0.5, drift), z=lerp(1.15, 1.4, drift), r=8)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(66, H - 178, 234, H - 66), 8, 8), paint(BLUE, stroke=2))
        label(c, "cam_01.mp4", 66, H - 50, 12, "mono", BLUE)
        c.restore()


# ---------------------------------------------------------------- L1 ZOZOCORE slam  b4..5 (CREDIT)
def s_zozo(x):
    c, lb = x.c, x.lb
    bg(c, WHITE)
    depth = out_expo(seg(lb, 0.0, 0.28)) * (1 - smooth(seg(lb, 0.72, 1.0)))
    _light_depth(c, x.t, depth, seed=3, flow=out_cubic(seg(lb, 0.32, 1.0)))
    e = out_expo(seg(lb, 0.0, 0.3))
    acc = pulse(lb - 0.5, 0.1) if lb >= 0.5 else 0.0
    s = lerp(2.4, 1.0, e) * (1 + 0.035 * acc) * (1 + 0.03 * lb)
    c.save()
    camz(c, s, rot=lerp(-8, -3, e))
    gh = (lerp(26, 3, e) + 10 * acc, 0.0, SKY, PINK, 0.55, MULT)

    def hop(i, n, ch):
        d = lb - 0.5 - 0.035 * i
        return {"dy": -38 * pulse(d, 0.09)} if d >= 0 else None
    txt(c, "ZOZO", CX - 40, CY - 138, 350, "unb900", ROSE, track=-6, ghost=gh, gfn=hop)
    txt(c, "CORE", CX + 60, CY + 150, 350, "unb900", ROSE, track=-6, ghost=gh, gfn=hop)
    c.restore()
    pk = out_back(seg(lb, 0.1, 0.42), 1.8)
    img(c, "panic", W + 60 - 330 * pk, 170 + 8 * math.sin(x.t * 7), 360, rot=-16 + 4 * math.sin(x.t * 5))
    _light_depth(c, x.t, depth * 0.8, seed=4, flow=out_cubic(seg(lb, 0.32, 1.0)), front=True)


# ---------------------------------------------------------------- L2 cluster  b5..7
CLUSTER = [("ぼっち", 250, 150, 70, -8), ("HITORI GOTOH", 1010, 128, 46, 5), ("結束バンド", 220, 515, 56, 6),
           ("STARRY", 1045, 522, 66, -7), ("下北沢", 640, 92, 40, 0), ("KESSOKU BAND", 640, 582, 34, 0),
           ("LONELY ROCK", 60, 330, 28, -90), ("90 BPM", 1220, 330, 28, 90), ("ギターヒーロー", 985, 236, 28, 0),
           ("★", 420, 236, 44, 10), ("★", 880, 442, 30, -12), ("STAGE FRIGHT", 330, 432, 24, -4)]


def s_cluster(x):
    c, lb = x.c, x.lb
    bg(c, WHITE)
    depth = smooth(seg(lb, 0.0, 0.32)) * (1 - smooth(seg(lb, 1.62, 2.0)))
    _light_depth(c, x.t, depth, seed=5, flow=smooth(seg(lb, 1.25, 2.0)))
    camz(c, 1.0 + 0.07 * lb)
    e = out_expo(seg(lb, 0, 0.35))
    txt(c, "ZOZOCORE", CX, CY - 6, lerp(190, 128, e), "unb900", PINK, track=-2, ghost=(4, 0, SKY, HOT, 0.45, MULT))
    ps = seg(lb, 0.2, 0.9)
    txt(c, "now playing > track_01", CX, CY + 86, 22, "monob", BLUE, fill=seg(ps, 0.6, 1.0), stroke=1.2, draw=ps)
    gh = (2.5, 0.0, SKY, PINK, 0.5, MULT)
    for k, (s, px, py, size, rot) in enumerate(CLUSTER):
        p = seg(lb, 0.04 * k, 0.04 * k + 0.45)
        if p <= 0:
            continue
        txt(c, s, px, py + 4 * math.sin(x.t * 2.2 + k), size, "round", BLUE, rot=rot + 2 * math.sin(x.t * 2 + k),
            gfn=kin.pop(p, 0.5, 30, seed=k), ghost=gh)
    _light_depth(c, x.t, depth * 0.62, seed=6, flow=smooth(seg(lb, 1.25, 2.0)), front=True)


# ---------------------------------------------------------------- L3 dash -> sine ribbon  b7..8
def s_ribbon(x):
    c, lb = x.c, x.lb
    bg(c, WHITE)
    grow = out_expo(seg(lb, 0.0, 0.3))
    amp = 78 * inout_cubic(seg(lb, 0.4, 0.95))
    X0 = CX - 760
    ph = -x.t * 5
    L = 1520 * grow
    x0 = CX - L / 2
    lw = lerp(8, 58, out_cubic(seg(lb, 0.12, 0.42)))
    if L > 2:
        pth = skia.Path()
        for i in range(161):
            xx = lerp(x0, x0 + L, i / 160)
            yy = CY + amp * math.sin(0.55 * (xx - X0) / 100 + ph)
            (pth.moveTo if i == 0 else pth.lineTo)(xx, yy)
        c.drawPath(pth, paint(BLUE, 1, stroke=lw + 8))
        c.drawPath(pth, paint(PINK, 1, stroke=lw))
    p = seg(lb, 0.14, 0.6)
    if p > 0:
        s = "BOCCHI THE ROCK // " * 5
        tx0 = CX - 760 - (x.t * 120) % text_w("BOCCHI THE ROCK // ", 30, "monob")
        wave_text(c, s, tx0, CY, 30, "monob", WHITE, amp, 0.55, ph + 0.55 * (tx0 - X0) / 100,
                  gfn=kin.scramble(p, seed=4, tick=x.fi // 2, lead=6))
    for k in range(6):
        q = out_back(seg(lb, 0.3 + 0.06 * k, 0.5 + 0.06 * k), 2.5)
        if q > 0:
            xx = 180 + k * 185
            yy = CY + (150 if k % 2 else -150) + amp * 0.3 * math.sin(x.t * 3 + k)
            c.drawPath(P_sparkle(xx, yy, 16 * q, x.t * 60), paint(PINK if k % 2 else BLUE))


# ---------------------------------------------------------------- L4 road signs  b8..10
def _sign(c, x, y, s, rot):
    c.save()
    c.translate(x, y)
    c.rotate(45 + rot)
    c.scale(s, s)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-112, -112, 128, 128), 38, 38), paint((60, 50, 30), 0.16, blur=8))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-120, -120, 120, 120), 38, 38), paint(YEL))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-101, -101, 101, 101), 26, 26), paint(INK, stroke=7))
    c.rotate(-45)
    img(c, "panic", 0, 8, 150, fx=("sil", INK))
    c.restore()


def s_signs(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, WHITE)
    for i in range(14):
        col = [PINK, SKY, GREEN, YEL, LAV, ORANGE][i % 6]
        xx = hash01(31, i) * W + 20 * math.sin(t + i)
        yy = hash01(32, i) * H + 16 * math.cos(t * 0.8 + i)
        r = hr(18, 46, 33, i)
        c.drawCircle(xx, yy, r, paint(col, 0.55, blur=hr(3, 14, 34, i)))
    confetti(c, 21, 40, t, [PINK, SKY, GREEN, YEL, LAV, ORANGE], spread=720, size=(7, 20), shapes="d", a=0.95)
    confetti(c, 22, 30, t, [PINK, SKY, YEL], cx=380, cy=CY, shapes="dt", size=(6, 14), burst=(0.0, 900), grav=90)
    base = 340
    xs = []
    bump = 1 + 0.05 * (0.5 + 0.5 * math.cos(lb * math.tau * 2)) ** 8
    for k in range(3):
        t0 = 0.5 * k - 0.1
        q = seg(lb, t0, t0 + 0.3)
        if q <= 0:
            continue
        e = out_quint(q)
        if k == 0:
            xk = lerp(-420, base, e)
        else:
            xk = lerp(base + 300 * (k - 1), base + 300 * k, e)
        shift = -60 * inout_cubic(seg(lb, 1.5, 1.9))
        age = max(0.0, lb - t0)
        settle = 4 * math.sin(age * 10) * math.exp(-age * 4)
        rot = (1 - e) * (-50 if k == 0 else 20) + settle + 5 * math.sin(t * 4 + k)
        s = 1.25 * (lerp(1.3, 1.0, e) if k == 0 else smooth(seg(q, 0.0, 0.18))) * bump
        xs.append((k, xk + shift, rot, s))
    for k, xk, rot, s in reversed(xs):
        _sign(c, xk, CY + 10 + 3 * math.sin(t * 2 + k), s, rot)


# ---------------------------------------------------------------- L5 card collage  b10..12
CARDS = [
    (250, 190, 300, 200, -6, RED, ("shot", 0.5, 0.35, 1.4, None), "cam_02"),
    (640, 150, 250, 165, 4, BLUE, None, "notes.txt"),
    (985, 205, 320, 215, -3, GREEN, ("peace", 0.5, 0.18, 1.0, BABY), "img_03"),
    (170, 470, 250, 200, 5, ORANGE, ("guitar", 0.45, 0.25, 1.0, PEACH), "img_04"),
    (500, 440, 300, 220, -4, PURPLE, ("shot", 0.3, 0.6, 2.0, None), "cam_05"),
    (860, 470, 280, 195, 6, PINK, ("maid", 0.5, 0.15, 1.0, LILAC), "img_06"),
    (1140, 450, 240, 180, -7, BLUE, ("shot", 0.75, 0.4, 1.8, None), "cam_07"),
    (1110, 105, 200, 140, 8, YEL, None, "todo.txt"),
    (380, 88, 220, 130, -8, GREEN, None, "log.txt"),
]


def s_collage(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, WHITE)
    depth = smooth(seg(lb, 0.0, 0.3)) * (1 - smooth(seg(lb, 1.68, 2.0)))
    _light_depth(c, t, depth, seed=7, flow=smooth(seg(lb, 1.0, 2.0)))
    z = 1 + 0.9 * out_expo(seg(lb, 1.0, 1.45)) + 0.04 * lb
    camz(c, z, rot=-2 * out_expo(seg(lb, 1.0, 1.45)))
    dots(c, LAV, 30, 2.2, a=0.9)
    for k, (fx_, fy, w, h, rot, bar, ph, title) in enumerate(CARDS):
        t0 = 0.05 * k
        q = seg(lb, t0, t0 + 0.45)
        if q <= 0:
            continue
        e = out_quint(q)
        ang = hash01(5, k) * 6.283
        dist = 950 * (1 - e)
        age = max(0.0, lb - t0)
        settle = 2.8 * math.sin(age * 10) * math.exp(-age * 3)
        tilt = rot + (1 - e) * hr(-60, 60, 5, k, 1) + settle + 0.8 * e * math.sin(t * 1.6 + k)
        content = photo_fn(*ph) if ph else lines_fn(GREY, 7, k)
        card(c, fx_ + math.cos(ang) * dist, fy + math.sin(ang) * dist + 4 * math.sin(t * 2 + k), w, h, bar, content,
             tilt, lerp(0.3, 1.0, e), 1.0, max(0.05, abs(math.cos((1 - e) * 1.3))), title)
    q = seg(lb, 1.05, 1.35)
    if q > 0:
        s = out_back(q, 2.2)
        c.save()
        c.translate(CX, CY)
        c.scale(s, s)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-128, -26, 128, 26), 12, 12), paint(INK, 0.2, blur=6))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-130, -28, 130, 24), 12, 12), paint(WHITE))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-130, -28, 130, 24), 12, 12), paint(INK, stroke=2.5))
        tp = seg(lb, 1.12, 1.6)
        txt(c, "guitar_hero()", 0, -2, 24, "monob", INK, gfn=kin.typ(tp))
        c.restore()
    _light_depth(c, t, depth * 0.72, seed=8, flow=smooth(seg(lb, 1.0, 2.0)), front=True)


# ---------------------------------------------------------------- L6 stickers  b12..14
def s_stickers(x):
    c, lb, t = x.c, x.lb, x.t
    bg_checker(c, WHITE, (243, 240, 252), 72, ox=-t * 24)

    def pp(t0):
        return out_back(seg(lb, t0, t0 + 0.3), 2.4)
    bump = 1 + 0.05 * (0.5 + 0.5 * math.cos(lb * math.tau * 2)) ** 8
    s = pp(0.0)
    if s > 0:
        c.save()
        c.translate(205, 300)
        c.rotate(t * 20)
        c.scale(s * bump, s * bump)
        sticker(c, P_flower(0, 0, 150, 6, 0.32), None, WHITE, 11, stroke=16, scol=PINK)
        c.restore()
    s = pp(0.25)
    if s > 0:
        c.save()
        c.translate(560 + 3 * s * math.sin(t * 1.6), 300 + 4 * s * math.sin(t * 2))
        c.rotate(-8 + 6 * math.sin(t * 2))
        c.scale(s * bump, s * bump)
        sticker(c, P_flower(0, 0, 150, 5, 0.26), SKY, WHITE, 10, stroke=6, scol=BLUE)
        txt(c, "ぼ", 0, 4, 150, "round", WHITE, stroke=5, scol=BLUE)
        c.restore()
    s = pp(0.5)
    if s > 0:
        c.save()
        c.translate(870 + 3 * s * math.sin(t * 1.7 + 1), 400 + 4 * s * math.sin(t * 2.1 + 1))
        c.rotate(6 * math.sin(t * 2.4))
        c.scale(s * bump, s * bump)
        sticker(c, P_blob(0, 0, 135, 7, t, 0.14), PINK, WHITE, 10)
        txt(c, "ROCK", 0, 0, 74, "round", WHITE, ext=(5, 0, 2.4, (200, 60, 110), (170, 40, 90)), rot=-6)
        c.restore()
    for k in range(3):
        p = seg(lb, 0.75 + 0.1 * k, 1.15 + 0.1 * k)
        if p > 0:
            txt(c, "STARRY", 1130, 190 + k * 54, 46, "round", BLUE, gfn=kin.pop(p, 0.4, 20, seed=40 + k))
    s = pp(1.0)
    if s > 0:
        img(c, "maid", 1110, 660 + 20 * (1 - s), 330 * s, fx=("stk", 9, WHITE), ay=1.0, rot=-6 + 3 * math.sin(t * 3))
    s = pp(0.6)
    if s > 0:
        c.save()
        c.translate(150, 555)
        c.rotate(t * 40)
        c.scale(s, s)
        c.drawPath(P_star(0, 0, 60, 18, 8), paint(PINK, stroke=9))
        c.restore()
    for k, (sx_, sy_, r_, col) in enumerate([(420, 520, 22, BLUE), (720, 120, 18, PINK), (1000, 560, 16, BLUE),
                                             (330, 110, 14, PINK), (760, 560, 26, SKY)]):
        s = pp(0.35 + 0.12 * k)
        if s > 0:
            c.drawPath(P_sparkle(sx_, sy_, r_ * s * 1.5, t * 50 + k * 30), paint(col))


# ---------------------------------------------------------------- L7 ribbons + rings  b14..16
def _ribbons(c, lb, t):
    bg(c, WHITE)
    depth = smooth(seg(lb, -0.08, 0.25)) * (1 - smooth(seg(lb, 0.32, 0.62)))
    _light_depth(c, t, depth, seed=9, flow=smooth(seg(lb, 0.18, 0.62)))
    for k in range(3):
        p = out_cubic(seg(lb, -0.14 + 0.05 * k, 0.32 + 0.05 * k))
        grow = in_cubic(seg(lb, 0.35, 0.55))
        pth = skia.Path()
        y0 = 150 + k * 180
        for i in range(81):
            xx = lerp(-80, W + 80, i / 80)
            yy = y0 + 70 * math.sin(i / 80 * 5.5 + k * 1.7 + t * 2)
            (pth.moveTo if i == 0 else pth.lineTo)(xx, yy)
        c.drawPath(trim_path(pth, p), paint(PINK, stroke=lerp(34, 260, grow)))
    for k in range(7):
        q = out_back(seg(lb, 0.1 + 0.04 * k, 0.3 + 0.04 * k), 2.4)
        if q > 0:
            xx, yy = hr(120, W - 120, 61, k), hr(90, H - 90, 62, k)
            pb = paint(BLUE, stroke=7 * q, cap=skia.Paint.kRound_Cap)
            c.drawLine(xx - 22 * q, yy - 9, xx + 22 * q, yy - 9, pb)
            c.drawLine(xx - 22 * q, yy + 9, xx + 22 * q, yy + 9, pb)
    _light_depth(c, t, depth * 0.6, seed=10, flow=smooth(seg(lb, 0.18, 0.62)), front=True)


def _rings(c, lb, t):
    smoke_bg(c, t, (228, 228, 236))
    depth = smooth(seg(lb, 0.4, 0.72)) * (1 - smooth(seg(lb, 1.72, 2.0)))
    _light_depth(c, t, depth, seed=11, flow=smooth(seg(lb, 1.0, 2.0)))
    z = lerp(1.28, 1.0, out_cubic(seg(lb, 0.45, 2.0)))
    c.save()
    camz(c, z, rot=lerp(-6, 0, out_cubic(seg(lb, 0.45, 2.0))))
    for side in (-1, 1):
        fan(c, CX + side * 395, CY + 20, 330, 5, (180 if side < 0 else 0) + 8 * math.sin(t * 2), 13, BLUE, a=0.9, w=0.3)
    b = 1 + 0.05 * pulse(lb % 1.0, 0.1)
    for side, cx in ((-1, 255), (1, 1025)):
        c.drawCircle(cx, CY + 20, 115 * b, paint(WHITE))
        c.drawCircle(cx, CY + 20, 128 * b, paint(PINK, stroke=10))
        img(c, "panic", cx, CY + 20, 200, rot=side * 10 + 5 * math.sin(t * 4), flip=side > 0)
    c.drawCircle(CX, CY, 205 * b, paint(WHITE))
    c.drawCircle(CX, CY, 226 * b, paint(PINK, stroke=16))
    dash_ring(c, CX, CY, 256 * b, PINK, 8, 30, 20, t * 80)
    img(c, "panic", CX, CY + 6 - 16 * abs(math.sin(lb * math.pi)), 330, rot=4 * math.sin(t * 3))
    q = out_back(seg(lb, 0.8, 1.1), 2.2)
    if q > 0:
        txt(c, "ぼっち", CX, CY + 262, 40, "round", PINK, gfn=kin.pop(seg(lb, 0.8, 1.2), 0.4, 20))
    c.restore()
    _light_depth(c, t, depth * 0.68, seed=12, flow=smooth(seg(lb, 1.0, 2.0)), front=True)


def s_rings(x):
    c, lb, t = x.c, x.lb, x.t
    if lb < 0.55:
        _ribbons(c, lb, t)
        return
    _rings(c, lb, t)
    r = out_cubic(seg(lb, 0.55, 0.85)) * 900
    if r < 890:
        c.save()
        cp = skia.Path()
        cp.addCircle(CX, CY, r)
        c.clipPath(cp, skia.ClipOp.kDifference, True)
        _ribbons(c, lb, t)
        c.restore()


# ---------------------------------------------------------------- L8 donuts + pie wipe  b16..17
def s_donut(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (236, 236, 243))
    s = out_back(seg(lb, -0.3, 0.12), 2.2)
    m = inout_cubic(seg(lb, 0.2, 0.38))
    col = mix(PINK, (86, 146, 238), m)
    c.drawPath(P_ring(CX, CY, lerp(150, 122, m) * s, lerp(60, 44, m) * s), paint(col))
    for k in range(10):
        a = math.radians(k * 36 + t * 90)
        r = 190 * out_back(m, 2)
        if m > 0:
            c.drawCircle(CX + math.cos(a) * r, CY + math.sin(a) * r, 8 * m, paint((86, 146, 238)))
    pw = inout_cubic(seg(lb, 0.45, 0.72))
    if pw <= 0:
        return
    c.save()
    c.clipPath(P_pie(CX, CY, 1500, -90, 360 * pw), skia.ClipOp.kIntersect, True)
    bg(c, (246, 244, 251))
    e = out_expo(seg(lb, 0.5, 0.85))
    xd = lerp(W + 320, 930, e)
    c.drawPath(P_ring(xd, CY + 40, 262, 96), paint(PINK))
    c.drawPath(P_arc(xd, CY + 40, 300, 120 + t * 50, 70), paint(BLUE, stroke=16, cap=skia.Paint.kButt_Cap))
    c.drawPath(P_arc(330, 250, 150, 200 + t * 40, 120), paint(BLUE, stroke=34, cap=skia.Paint.kButt_Cap))
    c.drawPath(P_arc(330, 250, 95, 20 + t * 60, 140), paint(SKY, stroke=22, cap=skia.Paint.kButt_Cap))
    c.drawPath(P_pie(560, 470, 170 * e, -30 + t * 30, 48), paint(SKY))
    c.drawPath(P_poly(420, 520, 40 * e, 3, t * 90), paint(PINK))
    for k in range(6):
        c.drawCircle(hr(100, 700, 81, k), hr(80, 600, 82, k), 7, paint((86, 146, 238)))
    c.restore()
    if pw < 1:
        a = math.radians(-90 + 360 * pw)
        c.drawLine(CX, CY, CX + math.cos(a) * 1500, CY + math.sin(a) * 1500, paint(PINK, stroke=6))


# ---------------------------------------------------------------- L9 gradient flower blob  b17..19
def s_blob(x):
    c, lb, t = x.c, x.lb, x.t
    bg(c, (246, 246, 251))

    def pp(t0):
        return out_back(seg(lb, t0, t0 + 0.3), 2.2)
    grow = in_expo(seg(lb, 1.45, 2.0))
    s = pp(0.0)
    if s > 0:
        c.drawPath(P_arc(230, 170, 92 * s, 40 + t * 50, 270), paint(BLUE, stroke=30, cap=skia.Paint.kButt_Cap))
        c.drawPath(P_arc(230, 170, 46 * s, 200 - t * 70, 250), paint(SKY, stroke=16, cap=skia.Paint.kButt_Cap))
    s = pp(0.12)
    if s > 0:
        c.drawPath(xform(P_crescent(300, 480, 110, 0.45, -30), rot=t * 15, s=s, cx=300, cy=480), paint(PINK))
    for k, (sx_, sy_, r_) in enumerate([(1085, 150, 38), (1150, 480, 30), (520, 110, 24), (980, 575, 32), (120, 330, 22)]):
        s = pp(0.3 + 0.07 * k)
        if s > 0:
            snowflake(c, sx_, sy_, r_ * s, SKY if k % 2 else BLUE, rot=t * 30 + k * 20)
    s = pp(0.2)
    if s > 0:
        R = lerp(175, 1300, grow) * s
        sh = lin(760 - R, 330 - R, 760 + R, 330 + R, [PINK, (190, 150, 255), SKY])
        c.drawPath(xform(P_flower(760, 330, R, 8, 0.18), rot=t * 25, cx=760, cy=330), paint(shader=sh))
        q = pp(0.35)
        c.drawPath(P_sparkle(760, 330, 82 * q * (1 + grow * 4), t * 40), paint(WHITE))
    for k in range(8):
        q = pp(0.4 + 0.05 * k)
        if q > 0:
            c.drawCircle(hr(80, W - 80, 91, k), hr(60, H - 60, 92, k), 7 * q, paint([PINK, SKY, LAV][k % 3]))


# ---------------------------------------------------------------- L10 sky marquee  b19..20
def s_sky(x):
    c, lb, t = x.c, x.lb, x.t
    bg_sky(c, t)
    marquee(c, "BOCCHI", 118, 300, "unb900", PINK, -lb * 760 - 120, gap=70,
            ext=(6, 0, 5, (205, 70, 125), (190, 60, 110)))
    if lb < 0.5:
        jy = -abs(math.sin(lb * math.pi * 4)) * 50
        img(c, "panic", 850, 470 + jy, 190, rot=math.sin(t * 9) * 8, fx=("stk", 6, WHITE))
        for k in range(3):
            q = out_back(seg(lb, 0.08 * k, 0.08 * k + 0.2), 2.5)
            if q > 0:
                bang(c, 690 + 70 * k, 400 - 26 * k, 70 * q, YEL, rot=-12 + 12 * k, outline=WHITE, ow=8)
    else:
        e = out_back(seg(lb, 0.42, 0.62), 1.8)
        img(c, "panic", 800, 400, 600 * e, fx=("sil", (86, 146, 238)), rot=-6 + 3 * math.sin(t * 6))
        bang(c, 360, 380, 340 * out_back(seg(lb, 0.45, 0.68), 2), WHITE, outline=(86, 146, 238), ow=12)


SHOTS = [
    (-0.25, 4.0, s_intro, {}),
    (4.0, 5.0, s_zozo, {"mb": lambda lb: 5 if lb < 0.32 else 1}),
    (5.0, 7.0, s_cluster, {}),
    (7.0, 8.0, s_ribbon, {}),
    (8.0, 10.0, s_signs, {"mb": lambda lb: 4 if (lb % 0.5) < 0.25 and lb < 1.3 else 1}),
    (10.0, 12.0, s_collage, {"mb": lambda lb: 3 if lb < 0.5 or 1.0 <= lb < 1.3 else 1}),
    (12.0, 14.0, s_stickers, {}),
    (14.0, 16.0, s_rings, {}),
    (16.0, 17.0, s_donut, {}),
    (17.0, 19.0, s_blob, {}),
    (19.0, 20.0, s_sky, {}),
]

TRANS = [
    (5.0, "zoom", 0.15, 0.25, {"streak": [BLUE, SKY, PINK]}),
    (7.0, "implode", 0.3, 0.1, {}),
    (10.0, "whip", 0.12, 0.2, {"d": 1}),
    (12.0, "whip", 0.12, 0.2, {"d": 1, "axis": "y"}),
    (16.0, "blob", 0.3, 0.12, {"cols": [PINK, SKY]}),
    (17.0, "stripes", 0.22, 0.22, {"cols": [PINK, SKY, YEL, LAV, WHITE, PINK]}),
    (19.0, "flash", 0.06, 0.14, {}),
]

FXE = [
    (4.0, "chroma", 0.35, 12.0),
    (8.0, "chroma", 0.3, 9.0),
    (11.0, "chroma", 0.2, 6.0),
    (14.0, "chroma", 0.25, 6.0),
    (19.5, "chroma", 0.25, 8.0),
    (20.0, "flash", 0.25, 0.9, {"pre": 0.12}),
]

CAM = [(4.0, "shake", 16, 0.1), (4.0, "punch", 0.05, 0.15), (4.5, "punch", 0.04, 0.12),
       (8.0, "shake", 10, 0.1), (8.5, "punch", 0.03), (9.0, "punch", 0.03), (9.5, "punch", 0.03),
       (11.0, "punch", 0.05), (12.0, "punch", 0.03), (13.0, "punch", 0.03), (19.5, "shake", 12, 0.1)]
