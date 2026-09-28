"""Transitions trans(A, B, p, **kw) -> frame.  p linear 0..1, A at p=0, B at p=1 (JIZURA contract)."""
from __future__ import annotations

import math

import cv2
import numpy as np
import skia

import fx
from core import (W, H, CX, CY, WHITE, BLACK, PINK, SKY, BLUE, YEL, LAV, clamp, lerp, seg, hash01, hr, hsgn,
                  in_expo, out_expo, inout_expo, inout_cubic, out_cubic, in_cubic, smooth, out_back, paint, rgba,
                  surface, layer, as_image, P_pie, P_blob, P_ring, P_poly, mix as cmix, SAMP, lin, rad)


def _mask(draw, blur=0.0):
    arr, s, c = layer()
    draw(c)
    m = arr[..., 3].astype(np.float32) * (1.0 / 255.0)
    if blur > 0.3:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    return m


def _canvas(img):
    img = np.ascontiguousarray(img)
    return img, surface(img).getCanvas()


def t_cut(A, B, p, **kw):
    return A if p < 0.5 else B


def t_fade(A, B, p, **kw):
    return fx.mix(A, B, smooth(p))


def t_flash(A, B, p, col=WHITE, **kw):
    base = A if p < 0.5 else B
    a = 1.0 - abs(2 * p - 1) ** kw.get("sharp", 0.6)
    return fx.flash(base, a, col)


def t_zoom(A, B, p, cx=CX, cy=CY, amt=1.4, streak=None, **kw):
    """Zoom-through: A pushes in with radial blur, B arrives from smaller scale."""
    if p < 0.5:
        q = p / 0.5
        e = in_expo(q)
        img = fx.affine(A, s=1 + amt * e, cx=cx, cy=cy)
        img = fx.zoom_blur(img, 0.05 + 0.55 * e, cx, cy)
    else:
        q = (p - 0.5) / 0.5
        e = 1 - out_expo(q)
        img = fx.affine(B, s=1 - 0.45 * e, cx=cx, cy=cy, border=cv2.BORDER_REFLECT)
        img = fx.zoom_blur(img, 0.02 + 0.6 * e, cx, cy)
    if streak:
        img, c = _canvas(img.copy())
        k = 1 - abs(2 * p - 1)
        for i in range(46):
            ang = hash01(9, i) * 6.283
            r0 = hr(60, 380, 9, i, 1) * (1.4 - k)
            ln = hr(120, 520, 9, i, 2) * k
            col = streak[i % len(streak)]
            c.drawLine(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0, cx + math.cos(ang) * (r0 + ln),
                       cy + math.sin(ang) * (r0 + ln), paint(col, 0.85 * k, stroke=hr(2, 7, 9, i, 3)))
    if kw.get("flash"):
        img = fx.flash(img, (1 - abs(2 * p - 1)) ** 3 * kw["flash"])
    return img


def t_implode(A, B, p, cx=CX, cy=CY, bgcol=WHITE, **kw):
    if p < 0.6:
        q = p / 0.6
        e = in_expo(q)
        img = fx.affine(A, s=max(0.02, 1 - 0.98 * e), cx=cx, cy=cy, border=cv2.BORDER_CONSTANT,
                        val=(bgcol[2], bgcol[1], bgcol[0], 255))
        img = fx.zoom_blur(img, 0.5 * e, cx, cy)
        return fx.flash(img, seg(q, 0.7, 1.0), bgcol)
    q = (p - 0.6) / 0.4
    return fx.flash(B, 1 - out_cubic(q), bgcol)


def t_whip(A, B, p, d=1, axis="x", blur=320, **kw):
    u = inout_expo(p) if kw.get("expo", True) else inout_cubic(p)
    size = W if axis == "x" else H
    off = int(round(u * size))
    out = np.empty_like(A)
    if axis == "x":
        if d > 0:
            out[:, :W - off] = A[:, off:]
            out[:, W - off:] = B[:, :off]
        else:
            out[:, off:] = A[:, :W - off]
            out[:, :off] = B[:, W - off:]
    else:
        if d > 0:
            out[:H - off] = A[off:]
            out[H - off:] = B[:off]
        else:
            out[off:] = A[:H - off]
            out[:off] = B[H - off:]
    L = blur * math.sin(math.pi * clamp(p)) ** 3
    return fx.hblur(out, L) if axis == "x" else fx.vblur(out, L)


def t_push(A, B, p, d=1, axis="x", **kw):
    return t_whip(A, B, p, d, axis, blur=kw.get("blur", 40), expo=False)


def t_cover(A, B, p, d=1, **kw):
    u = out_expo(p)
    off = int(round((1 - u) * W))
    out = A.copy()
    if off < W:
        if d > 0:
            out[:, off:] = B[:, :W - off]
        else:
            out[:, :W - off] = B[:, off:]
    return out


def t_pie(A, B, p, cx=CX, cy=CY, a0=-90.0, edge=None, **kw):
    e = inout_cubic(p)
    m = _mask(lambda c: c.drawPath(P_pie(cx, cy, 2400, a0, 360 * e), paint(WHITE)))
    out = fx.mask_mix(A, B, m)
    if edge and 0 < e < 1:
        out, c = _canvas(out)
        ang = math.radians(a0 + 360 * e)
        for i, col in enumerate(edge):
            c.drawPath(P_pie(cx, cy, 2400, a0 + 360 * e - 8 * (i + 1), 8), paint(col))
    return out


def t_iris(A, B, p, cx=CX, cy=CY, rims=(), reverse=False, **kw):
    R = math.hypot(max(cx, W - cx), max(cy, H - cy)) + 40
    e = in_cubic(p) if reverse else out_cubic(inout_cubic(p))
    out = A.copy()
    out, c = _canvas(out)
    lead = 70.0
    for i, col in enumerate(rims):
        r = e * (R + lead * len(rims)) - lead * i
        if r > 0:
            c.drawCircle(cx, cy, r, paint(col))
    rb = e * (R + lead * len(rims)) - lead * len(rims)
    if rb <= 0:
        return out
    m = _mask(lambda cc: cc.drawCircle(cx, cy, rb, paint(WHITE)))
    return fx.mask_mix(out, B, m)


def t_blob(A, B, p, cx=CX, cy=CY, cols=(PINK, SKY), seed=4, **kw):
    R = math.hypot(W, H) * 0.62
    e = inout_cubic(p)
    out, c = _canvas(A.copy())
    n = len(cols)
    for i, col in enumerate(cols):
        r = e * R * (1 + 0.28 * n) - R * 0.28 * i
        if r > 2:
            if isinstance(col, tuple) and len(col) == 2 and isinstance(col[0], tuple):
                sh = lin(cx - r, cy - r, cx + r, cy + r, list(col))
                c.drawPath(P_blob(cx, cy, r, seed + i, p * 4, 0.2), paint(shader=sh))
            else:
                c.drawPath(P_blob(cx, cy, r, seed + i, p * 4, 0.2), paint(col))
    rb = e * R * (1 + 0.28 * n) - R * 0.28 * n
    if rb <= 2:
        return out
    m = _mask(lambda cc: cc.drawPath(P_blob(cx, cy, rb, seed + 9, p * 4, 0.2), paint(WHITE)))
    return fx.mask_mix(out, B, m)


def _halfplane(f, slope):
    pth = skia.Path()
    pth.moveTo(-3 * W, -20)
    pth.lineTo(f - slope * (CY + 20), -20)
    pth.lineTo(f + slope * (H + 20 - CY), H + 20)
    pth.lineTo(-3 * W, H + 20)
    pth.close()
    return pth


def t_diag(A, B, p, cols=(SKY, (80, 200, 120), (240, 70, 60), PINK), slope=-0.45, d=1, gap=0.09, **kw):
    """Diagonal coloured panels sweep across, B trails the last panel."""
    n = len(cols)
    span = W * (1 + 2 * abs(slope)) + 200

    def front(i):
        q = clamp((p - i * gap) / (1 - n * gap))
        return -abs(slope) * H - 100 + span * inout_cubic(q)
    out, c = _canvas(A.copy())
    if d < 0:
        c.translate(W, 0)
        c.scale(-1, 1)
    for i, col in enumerate(cols):
        c.drawPath(_halfplane(front(i), slope), paint(col))
    fb = front(n)

    def mk(cc):
        if d < 0:
            cc.translate(W, 0)
            cc.scale(-1, 1)
        cc.drawPath(_halfplane(fb, slope), paint(WHITE))
    m = _mask(mk)
    return fx.mask_mix(out, B, m)


def t_slice(A, B, p, n=9, d=1, **kw):
    out = B.copy()
    bh = H / n
    for i in range(n):
        y0, y1 = int(i * bh), int((i + 1) * bh)
        q = clamp((p - 0.04 * i) / (1 - 0.04 * n))
        off = int(in_expo(q) * W * 1.05) * (1 if (i % 2 == 0) == (d > 0) else -1)
        if abs(off) >= W:
            continue
        if off >= 0:
            out[y0:y1, off:] = A[y0:y1, :W - off]
        else:
            out[y0:y1, :W + off] = A[y0:y1, -off:]
    return fx.hblur(out, 140 * math.sin(math.pi * p) ** 2)


def t_blinds(A, B, p, n=10, axis="x", **kw):
    def mk(c):
        sz = (W if axis == "x" else H) / n
        for i in range(n):
            q = clamp((p - 0.03 * i) / (1 - 0.03 * n))
            w = sz * inout_cubic(q)
            if axis == "x":
                c.drawRect(skia.Rect(i * sz + (sz - w) / 2, 0, i * sz + (sz + w) / 2, H), paint(WHITE))
            else:
                c.drawRect(skia.Rect(0, i * sz + (sz - w) / 2, W, i * sz + (sz + w) / 2), paint(WHITE))
    return fx.mask_mix(A, B, _mask(mk))


def t_checker(A, B, p, cell=110, **kw):
    def mk(c):
        nx, ny = int(W / cell) + 1, int(H / cell) + 1
        for j in range(ny):
            for i in range(nx):
                d = ((i + j) % 2) * 0.45 + hash01(i, j, 3) * 0.15
                q = clamp((p - d) / 0.4)
                s = out_back(q) * cell * 0.5
                if s > 0.5:
                    x, y = i * cell + cell / 2, j * cell + cell / 2
                    c.drawRect(skia.Rect(x - s, y - s, x + s, y + s), paint(WHITE))
    return fx.mask_mix(A, B, _mask(mk))


def t_blocks(A, B, p, cell=48, seed=5, **kw):
    nx, ny = W // cell + 1, H // cell + 1
    th = np.array([[hash01(seed, i, j) for i in range(nx)] for j in range(ny)], np.float32)
    m = (th < p).astype(np.float32)
    m = cv2.resize(m, (nx * cell, ny * cell), interpolation=cv2.INTER_NEAREST)[:H, :W]
    out = fx.mask_mix(A, B, m)
    k = math.sin(math.pi * p)
    if k > 0.1:
        out = fx.blocks(out, seed + int(p * 12), n=int(10 * k), amp=60 * k)
    return out


def t_pixelate(A, B, p, peak=48, **kw):
    px = 1 + peak * math.sin(math.pi * p) ** 2
    return fx.mosaic(A if p < 0.5 else B, px)


def t_static(A, B, p, seed=0, **kw):
    base = A if p < 0.5 else B
    k = 1 - abs(2 * p - 1)
    st = fx.mix(base, _static(seed + int(p * 30)), clamp(k * 1.6))
    return fx.slices(st, seed + int(p * 20), n=int(8 * k) + 1, amp=80 * k)


def _static(seed):
    from core import static_noise
    return static_noise(seed)


def t_glitch(A, B, p, seed=7, tint=(255, 40, 60), **kw):
    k = math.sin(math.pi * p)
    base = fx.mix(A, B, smooth(seg(p, 0.35, 0.65)))
    img = fx.slices(base, seed + int(p * 16), n=int(14 * k) + 1, amp=140 * k, hmax=70)
    img = fx.blocks(img, seed + int(p * 16) + 3, n=int(16 * k), amp=90 * k)
    img = fx.rgb_split(img, 18 * k, 0)
    if tint:
        tl = fx.solid(tint)
        img = cv2.addWeighted(img, 1 - 0.35 * k, tl, 0.35 * k, 0)
    return img


def _shards(seed, nx=9, ny=5):
    pts = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = i * W / nx + (hr(-0.35, 0.35, seed, i, j) * W / nx if 0 < i < nx else 0)
            y = j * H / ny + (hr(-0.35, 0.35, seed, j, i, 1) * H / ny if 0 < j < ny else 0)
            pts[i, j] = (x, y)
    tris = []
    for j in range(ny):
        for i in range(nx):
            a, b, c_, d = pts[i, j], pts[i + 1, j], pts[i + 1, j + 1], pts[i, j + 1]
            if hash01(seed, i, j, 2) < 0.5:
                tris += [(a, b, c_), (a, c_, d)]
            else:
                tris += [(a, b, d), (b, c_, d)]
    return tris


def t_shatter(A, B, p, seed=11, ix=CX, iy=CY, **kw):
    out, c = _canvas(B.copy())
    im = as_image(A)
    sh = im.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, SAMP)
    for k, tri in enumerate(_shards(seed)):
        gx = sum(v[0] for v in tri) / 3
        gy = sum(v[1] for v in tri) / 3
        dist = math.hypot(gx - ix, gy - iy) / math.hypot(W, H)
        q = clamp((p - dist * 0.35) / 0.65)
        if q >= 1:
            continue
        e = in_cubic(q)
        ang = math.atan2(gy - iy, gx - ix)
        tx = math.cos(ang) * e * hr(150, 500, seed, k) + hr(-40, 40, seed, k, 1) * e
        ty = math.sin(ang) * e * hr(150, 400, seed, k, 2) + 900 * e * e
        rot = hr(-160, 160, seed, k, 3) * e
        s = 1 - 0.35 * e
        pth = skia.Path()
        pth.moveTo(*tri[0])
        pth.lineTo(*tri[1])
        pth.lineTo(*tri[2])
        pth.close()
        c.save()
        c.translate(gx + tx, gy + ty)
        c.rotate(rot)
        c.scale(s, s)
        c.translate(-gx, -gy)
        pp = skia.Paint(AntiAlias=True)
        pp.setShader(sh)
        c.drawPath(pth, pp)
        c.drawPath(pth, paint(WHITE, 0.55 * (1 - q) + 0.2, stroke=1.6))
        c.restore()
    return out


def t_peel(A, B, p, **kw):
    """Page peel from bottom-right corner toward top-left."""
    e = inout_cubic(p)
    diag = math.hypot(W, H)
    nx, ny = -W / diag, -H / diag
    dist = e * diag * 1.05
    px, py = W + nx * dist * 0.5, H + ny * dist * 0.5
    # peeled region: points with (x-px)*(-nx)+(y-py)*(-ny) > 0  (toward the corner)
    big = 4000
    tx, ty = -ny, nx
    half = skia.Path()
    half.moveTo(px + tx * big, py + ty * big)
    half.lineTo(px - tx * big, py - ty * big)
    half.lineTo(px - tx * big - nx * big, py - ty * big - ny * big)
    half.lineTo(px + tx * big - nx * big, py + ty * big - ny * big)
    half.close()
    scr = skia.Path()
    scr.addRect(skia.Rect(0, 0, W, H))
    peeled = skia.Op(scr, half, skia.PathOp.kIntersect_PathOp)
    if peeled is None or peeled.isEmpty():
        return A
    m = _mask(lambda c: c.drawPath(peeled, paint(WHITE)))
    out = fx.mask_mix(A, B, m)
    th = math.degrees(math.atan2(ty, tx))
    R = skia.Matrix()
    R.setTranslate(px, py)
    R.preRotate(th)
    R.preScale(1, -1)
    R.preRotate(-th)
    R.preTranslate(-px, -py)
    flap = skia.Path(peeled)
    flap.transform(R)
    flap = skia.Op(flap, scr, skia.PathOp.kIntersect_PathOp) or flap
    out, c = _canvas(out)
    c.save()
    c.translate(-nx * 14, -ny * 14)
    c.drawPath(flap, paint(BLACK, 0.35, blur=18))
    c.restore()
    g = lin(px, py, px + nx * 260, py + ny * 260, [(250, 250, 252), (200, 200, 210)])
    c.drawPath(flap, paint(shader=g))
    c.drawPath(flap, paint((160, 160, 170), 0.6, stroke=1.5))
    return out


def t_tear(A, B, p, seed=3, **kw):
    e = in_cubic(p) if p < 0.35 else inout_cubic(p)
    gap = e * W * 0.62
    out, c = _canvas(B.copy())
    im = as_image(A)
    sh = im.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, SAMP)
    edge = [(CX + hr(-28, 28, seed, j), j * H / 22) for j in range(23)]
    for side in (-1, 1):
        pth = skia.Path()
        xs = 0 if side < 0 else W
        pth.moveTo(xs, -2)
        for x, y in edge:
            pth.lineTo(x, y)
        pth.lineTo(xs, H + 2)
        pth.close()
        c.save()
        c.translate(side * gap, 0)
        c.rotate(side * 3 * e)
        pp = skia.Paint(AntiAlias=True)
        pp.setShader(sh)
        c.drawPath(pth, pp)
        for x, y in edge[:-1]:
            pass
        ep = skia.Path()
        ep.moveTo(*edge[0])
        for x, y in edge[1:]:
            ep.lineTo(x, y)
        c.drawPath(ep, paint(WHITE, 0.9, stroke=5))
        c.restore()
    return out


def t_burst(A, B, p, col=WHITE, cx=CX, cy=CY, seed=2, **kw):
    if p < 0.5:
        q = p / 0.5
        out, c = _canvas(A.copy())
        for i in range(36):
            a0 = hash01(seed, i) * 360
            w = hr(2, 9, seed, i, 1) * (0.3 + q)
            ln = 1600 * out_expo(q * hr(0.6, 1.3, seed, i, 2))
            pth = skia.Path()
            pth.moveTo(cx, cy)
            pth.arcTo(skia.Rect(cx - ln, cy - ln, cx + ln, cy + ln), a0, w, False)
            pth.close()
            c.drawPath(pth, paint(col, 0.9))
        c.drawCircle(cx, cy, 30 + 900 * in_expo(q), paint(col, 1.0, blur=40))
        return fx.flash(out, in_cubic(q), col)
    q = (p - 0.5) / 0.5
    return fx.flash(B, 1 - out_cubic(q), col)


def t_stripes(A, B, p, cols=(PINK, SKY, YEL, LAV, WHITE), n=6, **kw):
    out = (A if p < 0.5 else B).copy()
    out, c = _canvas(out)
    bh = H / n
    for i in range(n):
        d = 0.05 * i
        if p < 0.5:
            q = clamp((p / 0.5 - d) / (1 - 0.05 * n))
            e = out_expo(q)
            side = 1 if i % 2 == 0 else -1
            x0 = -W + e * W if side > 0 else W - e * W
        else:
            q = clamp(((p - 0.5) / 0.5 - d) / (1 - 0.05 * n))
            e = in_expo(q)
            side = 1 if i % 2 == 0 else -1
            x0 = e * W * side
        c.drawRect(skia.Rect(x0, i * bh - 1, x0 + W, (i + 1) * bh + 1), paint(cols[i % len(cols)]))
    return out


def t_shutter(A, B, p, col=(20, 20, 24), n=4, **kw):
    out = (A if p < 0.5 else B).copy()
    out, c = _canvas(out)
    k = out_expo(p / 0.5) if p < 0.5 else 1 - in_expo((p - 0.5) / 0.5)
    bw = CX / n
    for side in (-1, 1):
        for i in range(n):
            q = clamp(k * 1.25 - 0.08 * i)
            x_in = bw * (n - i)
            w = bw * q
            if side < 0:
                x0 = CX - x_in
                c.drawRect(skia.Rect(x0, 0, x0 + w + 1, H), paint(col))
            else:
                x1 = CX + x_in
                c.drawRect(skia.Rect(x1 - w - 1, 0, x1, H), paint(col))
    return out


def t_luma(A, B, p, soft=0.12, **kw):
    lum = cv2.cvtColor(A[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    m = np.clip((p * (1 + soft) - lum) / soft, 0, 1)
    return fx.mask_mix(A, B, m)


def t_spin(A, B, p, **kw):
    if p < 0.5:
        q = p / 0.5
        img = fx.affine(A, rot=-90 * in_cubic(q), s=1 + 0.5 * in_cubic(q))
        return fx.spin_blur(img, 40 * in_cubic(q))
    q = (p - 0.5) / 0.5
    img = fx.affine(B, rot=90 * (1 - out_cubic(q)), s=1 + 0.5 * (1 - out_cubic(q)))
    return fx.spin_blur(img, 40 * (1 - out_cubic(q)))


TRANS = {k[2:]: v for k, v in globals().items() if k.startswith("t_") and callable(v)}


def apply(kind, A, B, p, **kw):
    return TRANS[kind](A, B, clamp(p), **kw)
