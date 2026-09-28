"""Core drawing library: timing, easing, colour, fonts + kinetic text, assets, shapes, backgrounds, UI."""
from __future__ import annotations

import functools
import math
import os

import cv2
import numpy as np
import skia

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1280, 660, 30
CX, CY = W / 2.0, H / 2.0
F0, FPB = 5, 20                 # beat b sits on frame 5 + 20 b (90 BPM @ 30 fps)
SPB = 2.0 / 3.0
END_B = 67.5                    # hard cut to black on the drop hit
NFRAMES = 1370


def f2b(f):
    return (f - F0) / FPB


def b2f(b):
    return F0 + FPB * b


def b2t(b):
    return (F0 + FPB * b) / FPS


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def seg(x, a, b):
    return clamp((x - a) / (b - a)) if b != a else float(x >= a)


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def in_cubic(t):
    return clamp(t) ** 3


def inout_cubic(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_quart(t):
    return 1 - (1 - clamp(t)) ** 4


def out_quint(t):
    return 1 - (1 - clamp(t)) ** 5


def out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def in_expo(t):
    t = clamp(t)
    return 0.0 if t <= 0 else 2 ** (10 * t - 10)


def inout_expo(t):
    t = clamp(t)
    if t <= 0 or t >= 1:
        return t
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def inout_sine(t):
    return -(math.cos(math.pi * clamp(t)) - 1) / 2


def out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def in_back(t, s=1.70158):
    t = clamp(t)
    return t * t * ((s + 1) * t - s)


def out_elastic(t, per=0.32):
    t = clamp(t)
    if t <= 0 or t >= 1:
        return t
    return 2 ** (-10 * t) * math.sin((t - per / 4) * (2 * math.pi) / per) + 1


def out_bounce(t):
    t = clamp(t)
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def pulse(x, w=0.12):
    """1 at x=0 decaying exponentially (x in beats since hit)."""
    return math.exp(-x / w) if x >= 0 else 0.0


def step(t, fps=12.0):
    """Quantise a time (seconds) for on-twos jitter."""
    return math.floor(t * fps) / fps


def hash01(*xs) -> float:
    h = 2166136261
    for x in xs:
        h ^= int(x) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 4294967296.0


def hr(a, b, *xs):
    return a + (b - a) * hash01(*xs)


def hsgn(*xs):
    return 1.0 if hash01(*xs) < 0.5 else -1.0


def vnoise(x, seed=0):
    """Smooth 1-D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a, b = hash01(seed, i) * 2 - 1, hash01(seed, i + 1) * 2 - 1
    return lerp(a, b, f * f * (3 - 2 * f))


# ------------------------------------------------------------------ colour
def hexc(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


WHITE = (255, 255, 255)
OFF = (247, 246, 251)
BLACK = (8, 7, 12)
INK = (22, 20, 34)
PINK = hexc("F06FA0")
HOT = hexc("FF3E9A")
ROSE = hexc("D38C9C")
BLUE = hexc("3A7FD0")
SKY = hexc("8FCBF6")
BABY = hexc("CFE8FF")
LAV = hexc("C9B8F2")
LILAC = hexc("E9E0FF")
YEL = hexc("FFD43B")
INDIGO = hexc("5B4DE8")
RED = hexc("F04438")
GREEN = hexc("35C77A")
ORANGE = hexc("FF9A3C")
PURPLE = hexc("9B5DE5")
MINT = hexc("9FF0D5")
CREAM = hexc("FFF4D8")
PEACH = hexc("FFD6C9")
MAG = hexc("FF2EA6")
DRED = hexc("6E0A1E")
CRIM = hexc("D0103A")
DPURP = hexc("1B0A30")
CYAN = hexc("3CF2FF")
TEAL = hexc("138A8A")
TERM = hexc("5BFF7A")
GREY = hexc("B9B7C6")


def mix(c1, c2, t):
    t = clamp(t)
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def rgba(c, a=1.0):
    return skia.ColorSetARGB(int(round(clamp(a) * 255)), int(c[0]), int(c[1]), int(c[2]))


def cf4(c, a=1.0):
    return skia.Color4f(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, clamp(a))


PLUS = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen
MULT = skia.BlendMode.kMultiply
DIFF = skia.BlendMode.kDifference
SRCIN = skia.BlendMode.kSrcIn
DSTOUT = skia.BlendMode.kDstOut
OVERLAY = skia.BlendMode.kOverlay


def paint(col=WHITE, a=1.0, stroke=None, blend=None, blur=None, shader=None, cap=None, join=None, pe=None, aa=True):
    p = skia.Paint()
    p.setAntiAlias(aa)
    p.setColor(rgba(col, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(float(stroke))
        p.setStrokeJoin(join if join is not None else skia.Paint.kRound_Join)
        p.setStrokeCap(cap if cap is not None else skia.Paint.kRound_Cap)
    if blend is not None:
        p.setBlendMode(blend)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, float(blur)))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(clamp(a))
    if pe is not None:
        p.setPathEffect(pe)
    return p


def lin(x0, y0, x1, y1, cols, pos=None, a=1.0):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                          [rgba(c, a) for c in cols], pos)


def rad(cx, cy, r, cols, pos=None, a=1.0):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1e-3, r), [rgba(c, a) for c in cols], pos)


def sweep(cx, cy, cols, pos=None, a=1.0):
    return skia.GradientShader.MakeSweep(cx, cy, [rgba(c, a) for c in cols], pos)


# ------------------------------------------------------------------ surfaces / layers
BGRA = skia.ColorType.kBGRA_8888_ColorType
PREMUL = skia.AlphaType.kPremul_AlphaType
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
SAMPN = skia.SamplingOptions(skia.FilterMode.kNearest)


def surface(arr):
    return skia.Surface(arr, colorType=BGRA, alphaType=PREMUL)


def layer(w=W, h=H):
    arr = np.zeros((h, w, 4), np.uint8)
    s = surface(arr)
    return arr, s, s.getCanvas()


def as_image(arr):
    return skia.Image.fromarray(np.ascontiguousarray(arr), BGRA, PREMUL)


def blit(c, arr, a=1.0, x=0.0, y=0.0, blend=None, samp=SAMP):
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    if blend is not None:
        p.setBlendMode(blend)
    c.drawImage(as_image(arr), float(x), float(y), samp, p)


def blit_rect(c, arr, dst, a=1.0, blend=None):
    im = as_image(arr)
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    if blend is not None:
        p.setBlendMode(blend)
    c.drawImageRect(im, skia.Rect(0, 0, im.width(), im.height()), dst, SAMP, p)


def over(dst, src, a=1.0):
    """Premultiplied src over dst, both HxWx4 uint8 (in place on dst)."""
    s = src.astype(np.float32) * a
    k = 1.0 - s[..., 3:4] / 255.0
    dst[:] = np.clip(dst.astype(np.float32) * k + s + 0.5, 0, 255).astype(np.uint8)
    return dst


# ------------------------------------------------------------------ fonts / text
FONT_DIR = os.path.join(ROOT, "fonts")
FONT_FILES = {
    "anton": "Anton-Regular.ttf", "bebas": "BebasNeue-Regular.ttf", "archivo": "ArchivoBlack-Regular.ttf",
    "mono": "SpaceMono-Regular.ttf", "monob": "SpaceMono-Bold.ttf", "dela": "DelaGothicOne-Regular.ttf",
    "round": "MPLUSRounded1c-Black.ttf", "roundx": "MPLUSRounded1c-ExtraBold.ttf", "unb": "Unbounded-VF.ttf",
}
REF = 100.0
_VP = skia.FontArguments.VariationPosition


@functools.lru_cache(maxsize=None)
def _tf(name):
    base = "unb" if name.startswith("unb") else name
    tf = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, FONT_FILES[base]))
    if tf is None:
        raise FileNotFoundError(FONT_FILES[base])
    if base == "unb":
        wght = float(name[3:] or 900)
        # Keep coords/vp alive through makeClone: skia-python's VariationPosition only points at the
        # Coordinates buffer, so a temporary chain can be freed first and silently yield the default wght.
        for _ in range(5):
            coords = _VP.Coordinates([_VP.Coordinate(0x77676874, wght)])
            vp = _VP(coords)
            fa = skia.FontArguments()
            fa.setVariationDesignPosition(vp)
            clone = tf.makeClone(fa)
            pos = clone.getVariationDesignPosition() or []
            if any(c.axis == 0x77676874 and abs(c.value - wght) < 0.5 for c in pos):
                return clone
        raise RuntimeError(f"variable font clone failed for {name}")
    return tf


@functools.lru_cache(maxsize=None)
def _font(name, size=REF):
    f = skia.Font(_tf(name), float(size))
    f.setSubpixel(True)
    f.setLinearMetrics(True)
    f.setHinting(skia.FontHinting.kNone)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


@functools.lru_cache(maxsize=None)
def glyph(name, ch):
    """(path at REF size, advance at REF) with CJK fallback."""
    for fn in (name, "round", "dela"):
        f = _font(fn)
        g = f.unicharToGlyph(ord(ch))
        if g or ch == " ":
            p = f.getPath(g) if g else None
            return (p if p is not None else skia.Path()), f.getWidths([g])[0]
    return skia.Path(), REF * 0.5


@functools.lru_cache(maxsize=None)
def cap_of(name):
    return _font(name).getMetrics().fCapHeight / REF


def text_w(s, size, font="anton", track=0.0):
    return sum(glyph(font, ch)[1] for ch in s) * size / REF + track * max(0, len(s) - 1)


def trim_path(path, p, start=0.0):
    """Each contour drawn from start..p of its own length (draw-on)."""
    if p >= 1 and start <= 0:
        return path
    out = skia.Path()
    if p <= start:
        return out
    pm = skia.PathMeasure(path, False)
    while True:
        L = pm.getLength()
        if L > 0:
            d = skia.Path()
            pm.getSegment(L * start, L * p, d, True)
            out.addPath(d)
        if not pm.nextContour():
            break
    return out


SCR = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#%&*+=<>/?!"
SCRJ = "ぼっちひとりギターロックバンド結束後藤星下北沢ヒーロー"


def scramble_ch(ch, seed, i, tick, jp=False):
    pool = SCRJ if jp else SCR
    return pool[int(hash01(seed, i, tick) * len(pool))]


def txt(c, s, x, y, size, font="anton", col=WHITE, a=1.0, align="c", va="m", track=0.0,
        sx=1.0, sy=1.0, rot=0.0, skx=0.0, gfn=None, fill=1.0, stroke=0.0, scol=None, draw=None,
        ext=None, shadow=None, glow=None, shader=None, ghost=None, bands=None, blend=None, sw_join=None):
    """Kinetic text.  Glyph fn gfn(i, n, ch) -> dict(dx, dy, s, sx, sy, rot, skx, a, col, ch, hide, draw).
    ext=(n, dx, dy, col_near, col_far); shadow=(dx, dy, blur, col, a); glow=(blur, col, a);
    ghost=(dx, dy, colA, colB, a[, blend]); bands=[(y0, y1, dx), ...] in cap-height fractions.
    Returns (width, cap_px)."""
    if not s or a <= 0.001:
        return 0.0, 0.0
    k = size / REF
    chars = list(s)
    n = len(chars)
    advs = [glyph(font, ch)[1] * k for ch in chars]
    total = sum(advs) + track * max(0, n - 1)
    cap = cap_of(font) * size
    ox = {"l": 0.0, "c": -total / 2.0, "r": -total}[align]
    base = {"m": cap / 2.0, "b": 0.0, "t": cap}[va]
    items = []
    cx = ox
    for i, ch in enumerate(chars):
        adv = advs[i]
        if ch != " ":
            d = gfn(i, n, ch) if gfn else None
            if not (d and d.get("hide")):
                d = d or {}
                gch = d.get("ch", ch)
                gp, gadv = glyph(font, gch)
                gw = gadv * k
                pdraw = d.get("draw", draw)
                gs = d.get("s", 1.0)
                m = skia.Matrix()
                m.setTranslate(cx + adv / 2.0 + d.get("dx", 0.0), base - cap / 2.0 + d.get("dy", 0.0))
                if d.get("rot"):
                    m.preRotate(d["rot"])
                if d.get("skx"):
                    m.preSkew(d["skx"], 0)
                m.preScale(gs * d.get("sx", 1.0), gs * d.get("sy", 1.0))
                m.preTranslate(-gw / 2.0, cap / 2.0)
                m.preScale(k, k)
                p = skia.Path(gp)
                p.transform(m)
                tp = None
                if pdraw is not None:
                    tp = trim_path(gp, pdraw)
                    tp = skia.Path(tp)
                    tp.transform(m)
                items.append((p, tp, d.get("col", col), a * d.get("a", 1.0)))
        cx += adv + track
    if not items:
        return total, cap
    M = skia.Matrix()
    M.setTranslate(x, y)
    if rot:
        M.preRotate(rot)
    if skx:
        M.preSkew(skx, 0)
    M.preScale(sx, sy)

    def passes(cc):
        allp = None
        if shadow or ext or ghost or glow:
            allp = skia.Path()
            for p, _, _, _ in items:
                allp.addPath(p)
        if shadow:
            dx, dy, bl, scc, sa = shadow
            cc.save()
            cc.translate(dx, dy)
            cc.drawPath(allp, paint(scc, sa * a, blur=bl if bl else None))
            cc.restore()
        if ext:
            en, edx, edy, c_near, c_far = ext[:5]
            ea = ext[5] if len(ext) > 5 else 1.0
            for j in range(int(en), 0, -1):
                cc.save()
                cc.translate(edx * j, edy * j)
                cc.drawPath(allp, paint(mix(c_near, c_far, j / en), ea * a))
                cc.restore()
        if ghost:
            gdx, gdy, ca, cb, ga = ghost[:5]
            gb = ghost[5] if len(ghost) > 5 else None
            for sgn, gc in ((-1, ca), (1, cb)):
                cc.save()
                cc.translate(sgn * gdx, sgn * gdy)
                cc.drawPath(allp, paint(gc, ga * a, blend=gb))
                cc.restore()
        if glow:
            bl, gc, ga = glow
            cc.drawPath(allp, paint(gc, ga * a, blur=bl, blend=PLUS if len(glow) < 4 else glow[3]))
        for p, tp, gc, ga in items:
            if fill > 0 and ga > 0:
                pp = paint(gc, ga * fill, blend=blend, shader=shader)
                cc.drawPath(p, pp)
            if stroke > 0 and ga > 0:
                cc.drawPath(tp if tp is not None else p, paint(scol or gc, ga, stroke=stroke, blend=blend, join=sw_join))

    c.save()
    c.concat(M)
    if bands:
        top = base - cap
        for y0, y1, bdx in bands:
            c.save()
            c.clipRect(skia.Rect(ox - 4000, top + y0 * cap, ox + total + 4000, top + y1 * cap))
            c.translate(bdx, 0)
            passes(c)
            c.restore()
    else:
        passes(c)
    c.restore()
    return total, cap


def text_path(s, x, y, size, font="anton", align="c", va="m", track=0.0):
    """Whole string as one path (for masks / clipping)."""
    k = size / REF
    advs = [glyph(font, ch)[1] * k for ch in s]
    total = sum(advs) + track * max(0, len(s) - 1)
    cap = cap_of(font) * size
    cx = x + {"l": 0.0, "c": -total / 2.0, "r": -total}[align]
    by = y + {"m": cap / 2.0, "b": 0.0, "t": cap}[va]
    out = skia.Path()
    for ch, adv in zip(s, advs):
        if ch != " ":
            m = skia.Matrix()
            m.setTranslate(cx, by)
            m.preScale(k, k)
            p = skia.Path(glyph(font, ch)[0])
            p.transform(m)
            out.addPath(p)
        cx += adv + track
    return out


def label(c, s, x, y, size, font="monob", col=WHITE, a=1.0, align="l", va="m", track=0.0):
    """Cheap single-line text via TextBlob (small UI text)."""
    if not s or a <= 0.001:
        return 0.0
    f = _font(font, float(size))
    need_fb = any(f.unicharToGlyph(ord(ch)) == 0 and ch != " " for ch in s)
    if need_fb or track:
        return txt(c, s, x, y, size, font, col, a, align, va, track)[0]
    w = f.measureText(s)
    cap = cap_of(font) * size
    ox = x - w * {"l": 0.0, "c": 0.5, "r": 1.0}[align]
    by = y + {"m": cap / 2.0, "b": 0.0, "t": cap}[va]
    c.drawString(s, ox, by, f, paint(col, a))
    return w


def type_on(s, p, cursor=True, tick=0):
    """Typewriter reveal; returns visible string (+ cursor bar if blinking on)."""
    n = len(s)
    k = int(clamp(p) * (n + 0.999))
    out = s[:k]
    if cursor and (p < 1.0 or tick % 2 == 0):
        out += "|"
    return out


# ------------------------------------------------------------------ assets
ASSET_DIR = os.path.join(ROOT, "assets")


@functools.lru_cache(maxsize=None)
def _asset_np(name):
    arr = cv2.imread(os.path.join(ASSET_DIR, f"bocchi_{name}.png"), cv2.IMREAD_UNCHANGED)
    if arr is None:
        raise FileNotFoundError(name)
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])
    return arr


def _premul_img(arr):
    a = arr[..., 3:4].astype(np.float32) / 255.0
    pm = arr.copy()
    pm[..., :3] = np.clip(arr[..., :3].astype(np.float32) * a + 0.5, 0, 255).astype(np.uint8)
    return skia.Image.fromarray(np.ascontiguousarray(pm), BGRA, PREMUL).withDefaultMipmaps()


def _bgr(col):
    return np.array([col[2], col[1], col[0]], np.float32)


def treat(arr, fx):
    """fx tuples: ('sil', col) ('duo', dark, light) ('stk', r, col) ('tint', col, amt) ('gray',) ('inv',)
    ('manga',) ('poster', n) ('glow', col) ('hue', deg)."""
    kind = fx[0]
    out = arr.copy()
    rgb = arr[..., :3].astype(np.float32)
    if kind == "sil":
        out[..., :3] = _bgr(fx[1]).astype(np.uint8)
    elif kind in ("duo", "tri"):
        lum = (rgb @ np.array([0.114, 0.587, 0.299], np.float32)) / 255.0
        lum = np.clip((lum - 0.08) / 0.84, 0, 1)[..., None]
        if kind == "duo":
            out[..., :3] = np.clip(_bgr(fx[1]) * (1 - lum) + _bgr(fx[2]) * lum, 0, 255).astype(np.uint8)
        else:
            lo, mid, hi = _bgr(fx[1]), _bgr(fx[2]), _bgr(fx[3])
            t = lum[..., 0]
            res = np.where((t < 0.5)[..., None], lo * (1 - 2 * t[..., None]) + mid * 2 * t[..., None],
                           mid * (2 - 2 * t[..., None]) + hi * (2 * t[..., None] - 1))
            out[..., :3] = np.clip(res, 0, 255).astype(np.uint8)
    elif kind == "stk":
        r = int(fx[1])
        pad = r + 2
        big = cv2.copyMakeBorder(arr, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
        al = big[..., 3]
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        dil = cv2.dilate((al > 20).astype(np.uint8) * 255, k)
        dil = cv2.GaussianBlur(dil, (0, 0), 1.0)
        a = big[..., 3:4].astype(np.float32) / 255.0
        col = _bgr(fx[2] if len(fx) > 2 else WHITE)
        res = np.empty_like(big)
        res[..., :3] = np.clip(big[..., :3] * a + col * (1 - a), 0, 255).astype(np.uint8)
        res[..., 3] = np.maximum(dil, big[..., 3])
        return res
    elif kind == "tint":
        out[..., :3] = np.clip(rgb * (1 - fx[2]) + _bgr(fx[1]) * fx[2], 0, 255).astype(np.uint8)
    elif kind == "gray":
        lum = rgb @ np.array([0.114, 0.587, 0.299], np.float32)
        out[..., :3] = np.clip(lum, 0, 255).astype(np.uint8)[..., None]
    elif kind == "inv":
        out[..., :3] = 255 - arr[..., :3]
    elif kind == "manga":
        g = (rgb @ np.array([0.114, 0.587, 0.299], np.float32)).astype(np.uint8)
        edges = cv2.adaptiveThreshold(cv2.GaussianBlur(g, (3, 3), 0), 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 6)
        hh, ww = g.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        dots = ((np.sin(xx * 0.9) * np.sin(yy * 0.9)) * 0.5 + 0.5) * 255
        tone = np.where(g < 90, 0, np.where(g < 170, np.where(dots > g, 0, 255), 255)).astype(np.uint8)
        v = np.minimum(edges, tone)
        out[..., :3] = v[..., None]
    elif kind == "poster":
        q = 255.0 / (fx[1] - 1)
        out[..., :3] = (np.round(rgb / q) * q).clip(0, 255).astype(np.uint8)
    elif kind == "hue":
        hsv = cv2.cvtColor(arr[..., :3], cv2.COLOR_BGR2HSV)
        hsv[..., 0] = ((hsv[..., 0].astype(np.int32) + int(fx[1] / 2)) % 180).astype(np.uint8)
        out[..., :3] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return out


@functools.lru_cache(maxsize=96)
def asset(name, fx=None):
    arr = _asset_np(name)
    if fx:
        arr = treat(arr, fx)
    return _premul_img(arr)


def asset_size(name):
    a = _asset_np(name)
    return a.shape[1], a.shape[0]


def img(c, name, x, y, h, fx=None, ax=0.5, ay=0.5, rot=0.0, a=1.0, sx=1.0, sy=1.0, flip=False, blend=None,
        cfilter=None, blur=None):
    """Draw asset with height h, anchor (ax, ay) placed at (x, y).  Returns drawn width."""
    if a <= 0.001 or h <= 0.5:
        return 0.0
    im = asset(name, fx)
    w = h * im.width() / im.height()
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(sx * (-1 if flip else 1), sy)
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    if blend is not None:
        p.setBlendMode(blend)
    if cfilter is not None:
        p.setColorFilter(cfilter)
    if blur:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    c.drawImageRect(im, skia.Rect(0, 0, im.width(), im.height()), skia.Rect(-w * ax, -h * ay, w * (1 - ax), h * (1 - ay)),
                    SAMP, p)
    c.restore()
    return w


def photo(c, name, x, y, w, h, u=0.5, v=0.5, z=1.0, r=0.0, a=1.0, fx=None, rot=0.0):
    """Cover-crop asset into rect (x, y, w, h), optional rounded corners."""
    if a <= 0.001:
        return
    im = asset(name, fx)
    iw, ih = im.width(), im.height()
    sc = max(w / iw, h / ih) * z
    sw, sh = w / sc, h / sc
    sx0 = clamp(u * iw - sw / 2, 0, max(0, iw - sw))
    sy0 = clamp(v * ih - sh / 2, 0, max(0, ih - sh))
    c.save()
    if rot:
        c.translate(x + w / 2, y + h / 2)
        c.rotate(rot)
        c.translate(-(x + w / 2), -(y + h / 2))
    dst = skia.Rect(x, y, x + w, y + h)
    if r:
        c.clipRRect(skia.RRect.MakeRectXY(dst, r, r), True)
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    c.drawImageRect(im, skia.Rect(sx0, sy0, sx0 + sw, sy0 + sh), dst, SAMP, p)
    c.restore()


# ------------------------------------------------------------------ shapes (paths)
def P_poly(cx, cy, r, n=3, rot=0.0):
    p = skia.Path()
    for i in range(n):
        t = math.radians(rot) + 2 * math.pi * i / n - math.pi / 2
        (p.moveTo if i == 0 else p.lineTo)(cx + r * math.cos(t), cy + r * math.sin(t))
    p.close()
    return p


def P_star(cx, cy, r1, r2, n=5, rot=0.0):
    p = skia.Path()
    for i in range(2 * n):
        r = r1 if i % 2 == 0 else r2
        t = math.radians(rot) + math.pi * i / n - math.pi / 2
        (p.moveTo if i == 0 else p.lineTo)(cx + r * math.cos(t), cy + r * math.sin(t))
    p.close()
    return p


def P_radial(cx, cy, fr, rot=0.0, steps=160):
    """Closed curve r(theta) = fr(theta)."""
    p = skia.Path()
    for i in range(steps):
        t = 2 * math.pi * i / steps
        r = fr(t)
        a = t + math.radians(rot)
        (p.moveTo if i == 0 else p.lineTo)(cx + r * math.cos(a), cy + r * math.sin(a))
    p.close()
    return p


def P_flower(cx, cy, r, petals=6, depth=0.3, rot=0.0):
    return P_radial(cx, cy, lambda t: r * (1 - depth + depth * abs(math.cos(petals * t / 2)) ** 0.6), rot)


def P_blob(cx, cy, r, seed=0, t=0.0, amp=0.16, k=5):
    ph = [hash01(seed, j) * 6.283 for j in range(k)]
    sp = [hr(0.4, 1.3, seed, j, 7) * hsgn(seed, j, 9) for j in range(k)]

    def fr(th):
        s = 0.0
        for j in range(k):
            s += math.sin((j + 2) * th + ph[j] + t * sp[j]) / (j + 2)
        return r * (1 + amp * s)
    return P_radial(cx, cy, fr, 0.0, 120)


def P_sparkle(cx, cy, r, rot=0.0, pinch=0.18):
    p = skia.Path()
    pts = []
    for i in range(4):
        a = math.radians(rot) + i * math.pi / 2 - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    p.moveTo(*pts[0])
    for i in range(4):
        nx, ny = pts[(i + 1) % 4]
        p.quadTo(cx + (pts[i][0] + nx - 2 * cx) * pinch, cy + (pts[i][1] + ny - 2 * cy) * pinch, nx, ny)
    p.close()
    return p


def P_ring(cx, cy, ro, ri):
    p = skia.Path()
    p.addCircle(cx, cy, ro)
    if ri > 0:
        p.addCircle(cx, cy, ri, skia.PathDirection.kCCW)
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p


def P_pie(cx, cy, r, a0, sweep_deg):
    p = skia.Path()
    if sweep_deg >= 359.9:
        p.addCircle(cx, cy, r)
        return p
    p.moveTo(cx, cy)
    p.arcTo(skia.Rect(cx - r, cy - r, cx + r, cy + r), a0, sweep_deg, False)
    p.close()
    return p


def P_arc(cx, cy, r, a0, sweep_deg):
    p = skia.Path()
    p.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), a0, sweep_deg)
    return p


def P_rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r))
    return p


def P_crescent(cx, cy, r, off=0.45, rot=0.0):
    a = skia.Path()
    a.addCircle(cx, cy, r)
    b = skia.Path()
    t = math.radians(rot)
    b.addCircle(cx + math.cos(t) * r * off, cy + math.sin(t) * r * off, r * 0.92)
    return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


def P_gear(cx, cy, r, teeth=8, depth=0.22, rot=0.0):
    return P_radial(cx, cy, lambda t: r * (1 - depth * (0.5 + 0.5 * math.tanh(4 * math.sin(teeth * t)))), rot, 240)


def P_heart(cx, cy, s, rot=0.0):
    p = skia.Path()
    for i in range(100):
        t = 2 * math.pi * i / 100
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    p.close()
    m = skia.Matrix()
    m.setTranslate(cx, cy)
    m.preRotate(rot)
    m.preScale(s / 16, s / 16)
    p.transform(m)
    return p


def P_cloud(cx, cy, w, seed=0):
    p = skia.Path()
    n = 5
    for i in range(n):
        u = (i + 0.5) / n
        r = w * (0.16 + 0.1 * math.sin(u * math.pi)) * hr(0.85, 1.15, seed, i)
        p.addCircle(cx - w / 2 + u * w, cy - r * 0.35 * math.sin(u * math.pi), r)
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(cx - w * 0.52, cy - w * 0.08, cx + w * 0.52, cy + w * 0.12), w * 0.1, w * 0.1))
    return skia.Op(p, skia.Path(), skia.PathOp.kUnion_PathOp) or p


def xform(path, tx=0.0, ty=0.0, rot=0.0, s=1.0, cx=0.0, cy=0.0, sx=1.0, sy=1.0):
    """Rotate/scale about (cx, cy) then translate."""
    m = skia.Matrix()
    m.setTranslate(cx + tx, cy + ty)
    if rot:
        m.preRotate(rot)
    m.preScale(s * sx, s * sy)
    m.preTranslate(-cx, -cy)
    q = skia.Path(path)
    q.transform(m)
    return q


def wave_path(x0, x1, y, amp, freq, phase=0.0, steps=120):
    p = skia.Path()
    for i in range(steps + 1):
        x = lerp(x0, x1, i / steps)
        yy = y + amp * math.sin(freq * (x - x0) / 100.0 + phase)
        (p.moveTo if i == 0 else p.lineTo)(x, yy)
    return p


def snowflake(c, cx, cy, r, col, a=1.0, rot=0.0, lw=None):
    lw = lw or max(1.5, r * 0.12)
    pt = paint(col, a, stroke=lw)
    for i in range(6):
        t = math.radians(rot + i * 60)
        ex, ey = cx + r * math.cos(t), cy + r * math.sin(t)
        c.drawLine(cx, cy, ex, ey, pt)
        for f in (0.55,):
            bx, by = cx + r * f * math.cos(t), cy + r * f * math.sin(t)
            for s in (-1, 1):
                t2 = t + s * math.radians(40)
                c.drawLine(bx, by, bx + r * 0.32 * math.cos(t2), by + r * 0.32 * math.sin(t2), pt)


# ------------------------------------------------------------------ backgrounds
def bg(c, col):
    c.clear(rgba(col))


def bg_grid(c, base, line, step=40.0, ox=0.0, oy=0.0, lw=1.0, a=1.0, major=0, mcol=None):
    c.clear(rgba(base))
    p = paint(line, a, stroke=lw, cap=skia.Paint.kButt_Cap)
    x = ox % step - step
    i = 0
    while x < W + step:
        c.drawLine(x, 0, x, H, p)
        x += step
    y = oy % step - step
    while y < H + step:
        c.drawLine(0, y, W, y, p)
        y += step
    if major:
        pm = paint(mcol or line, a, stroke=lw * 2, cap=skia.Paint.kButt_Cap)
        st = step * major
        x = ox % st - st
        while x < W + st:
            c.drawLine(x, 0, x, H, pm)
            x += st
        y = oy % st - st
        while y < H + st:
            c.drawLine(0, y, W, y, pm)
            y += st


def bg_checker(c, c1, c2, step=64.0, ox=0.0, oy=0.0, rot=0.0):
    c.clear(rgba(c1))
    c.save()
    if rot:
        c.translate(CX, CY)
        c.rotate(rot)
        c.translate(-CX, -CY)
    p = paint(c2)
    ext = int(max(W, H) / step) + 4
    x0 = ox % (2 * step) - 2 * step - (W if rot else 0) * 0.5
    y0 = oy % (2 * step) - 2 * step - (H if rot else 0) * 0.5
    path = skia.Path()
    rows = ext + (int(H / step) if rot else 0) + 4
    cols = ext + (int(W / step) if rot else 0) + 4
    for j in range(rows):
        for i in range(cols):
            if (i + j) % 2 == 0:
                path.addRect(skia.Rect.MakeXYWH(x0 + i * step, y0 + j * step, step, step))
    c.drawPath(path, p)
    c.restore()


@functools.lru_cache(maxsize=None)
def _grid_pts(step, extra):
    xs = np.arange(-step * extra, W + step * (extra + 1), step)
    ys = np.arange(-step * extra, H + step * (extra + 1), step)
    gx, gy = np.meshgrid(xs, ys)
    return list(map(skia.Point, gx.ravel().tolist(), gy.ravel().tolist()))


def dots(c, col, step=28.0, r=2.0, ox=0.0, oy=0.0, a=1.0):
    c.save()
    c.translate(ox % step - step, oy % step - step)
    c.drawPoints(skia.Canvas.kPoints_PointMode, _grid_pts(float(step), 1), paint(col, a, stroke=2 * r))
    c.restore()


@functools.lru_cache(maxsize=4)
def _nebula(seed, w=W // 2, h=H // 2):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w, 3), np.float32)
    cols = [np.array(v, np.float32) for v in ((90, 20, 120), (160, 30, 110), (40, 20, 90), (200, 60, 170))]
    for octave, sig in enumerate((60, 30, 14, 7)):
        n = rng.random((h, w)).astype(np.float32)
        n = cv2.GaussianBlur(n, (0, 0), sig)
        n = (n - n.min()) / (np.ptp(n) + 1e-6)
        n = np.clip((n - 0.45) * 2.2, 0, 1) ** 1.6
        acc += n[..., None] * cols[octave][::-1] * (0.9 / (octave + 1) ** 0.5)
    acc = np.clip(acc, 0, 255).astype(np.uint8)
    out = np.dstack([acc, np.full((h, w), 255, np.uint8)])
    return skia.Image.fromarray(np.ascontiguousarray(out), BGRA, PREMUL).withDefaultMipmaps()


def bg_galaxy(c, t, seed=3, drift=12.0, base=(10, 4, 20), tw=1.0):
    c.clear(rgba(base))
    im = _nebula(seed)
    s = 1.12 + 0.02 * math.sin(t * 0.3)
    wv, hv = W * s, H * s
    x = -(wv - W) / 2 + drift * math.sin(t * 0.21)
    y = -(hv - H) / 2 + drift * 0.6 * math.cos(t * 0.17)
    p = skia.Paint()
    c.drawImageRect(im, skia.Rect(0, 0, im.width(), im.height()), skia.Rect(x, y, x + wv, y + hv), SAMP, p)
    stars(c, t, seed, n=160, a=tw)


def stars(c, t, seed=0, n=150, a=1.0, col=WHITE, zoom=0.0):
    for i in range(n):
        x = hash01(seed, i, 1) * W
        y = hash01(seed, i, 2) * H
        if zoom:
            x = CX + (x - CX) * (1 + zoom * hash01(seed, i, 5))
            y = CY + (y - CY) * (1 + zoom * hash01(seed, i, 5))
        r = 0.6 + 1.6 * hash01(seed, i, 3) ** 3
        tw = 0.55 + 0.45 * math.sin(t * hr(1.5, 5, seed, i, 4) + i)
        c.drawCircle(x, y, r, paint(col, a * tw))
        if r > 1.7:
            pp = paint(col, a * tw * 0.6, stroke=0.8)
            c.drawLine(x - r * 3, y, x + r * 3, y, pp)
            c.drawLine(x, y - r * 3, x, y + r * 3, pp)


def bg_sky(c, t, top=(120, 186, 245), bot=(222, 240, 255), clouds=True, drift=10.0):
    p = paint(shader=lin(0, 0, 0, H, [top, bot]))
    c.drawPaint(p)
    if clouds:
        for i in range(7):
            x = (hash01(71, i) * (W + 400) - 200 + t * drift * hr(0.5, 1.5, 72, i)) % (W + 400) - 200
            y = hr(0.15, 0.95, 73, i) * H
            w = hr(220, 520, 74, i)
            c.drawPath(P_cloud(x, y, w, i), paint(WHITE, hr(0.55, 0.95, 75, i), blur=hr(2, 14, 76, i)))


def static_noise(seed, w=W, h=H, block=2, a=1.0):
    rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)
    n = rng.integers(0, 256, (h // block + 1, w // block + 1), dtype=np.uint8)
    n = cv2.resize(n, ((w // block + 1) * block, (h // block + 1) * block), interpolation=cv2.INTER_NEAREST)[:h, :w]
    rows = rng.random(h).astype(np.float32)
    band = (0.75 + 0.35 * rows)[:, None]
    g = np.clip(n.astype(np.float32) * band, 0, 255).astype(np.uint8)
    return np.dstack([g, g, g, np.full((h, w), 255, np.uint8)])


# ------------------------------------------------------------------ UI parts
def window(c, x, y, w, h, title="", col=INDIGO, body=WHITE, r=10.0, lw=3.0, bar=26.0, a=1.0, shadow=8.0,
           tcol=WHITE, font="monob", btn=True, body_a=1.0):
    """Flat retro window. Returns content rect (x, y, w, h)."""
    if a <= 0.001:
        return x, y + bar, w, h - bar
    rect = skia.Rect(x, y, x + w, y + h)
    if shadow:
        c.drawRRect(skia.RRect.MakeRectXY(rect.makeOffset(shadow, shadow), r, r), paint(col, 0.35 * a))
    c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), paint(body, a * body_a))
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(rect, r, r), True)
    c.drawRect(skia.Rect(x, y, x + w, y + bar), paint(col, a))
    c.restore()
    c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), paint(col, a, stroke=lw))
    if title:
        label(c, title, x + 10, y + bar / 2, min(13.0, bar * 0.5), font, tcol, a)
    if btn:
        for i in range(3):
            bx = x + w - 14 - i * 16
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(bx - 5, y + bar / 2 - 5, bx + 5, y + bar / 2 + 5), 2, 2),
                        paint(tcol, a * 0.9, stroke=1.8))
    return x, y + bar, w, h - bar


def button(c, x, y, w, h, text, col=INDIGO, fill=WHITE, tcol=None, a=1.0, r=8.0, size=14.0, font="monob", lw=2.5):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 4, y + 4, x + w + 4, y + h + 4), r, r), paint(col, a * 0.5))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r), paint(fill, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r), paint(col, a, stroke=lw))
    label(c, text, x + w / 2, y + h / 2, size, font, tcol or col, a, "c")


def warn(c, cx, cy, s, col=RED, a=1.0, rot=0.0, mark=WHITE):
    p = P_poly(0, s * 0.12, s, 3)
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.drawPath(p, paint(col, a))
    c.drawPath(p, paint(col, a, stroke=s * 0.28))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-s * 0.09, -s * 0.42, s * 0.09, s * 0.22), s * 0.09, s * 0.09), paint(mark, a))
    c.drawCircle(0, s * 0.42, s * 0.1, paint(mark, a))
    c.restore()


def progress(c, x, y, w, h, p, col=INDIGO, bgc=WHITE, a=1.0, r=None):
    r = h / 2 if r is None else r
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r), paint(bgc, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + max(h, w * clamp(p)), y + h), r, r), paint(col, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r), paint(col, a, stroke=2))


def confetti(c, seed, n, t, cols, cx=CX, cy=CY, spread=700.0, size=(5, 12), shapes="dtr", grav=0.0, a=1.0,
             spin=1.0, burst=None):
    """Deterministic confetti field.  burst=(t0, speed): particles explode from (cx, cy)."""
    for i in range(n):
        col = cols[int(hash01(seed, i, 1) * len(cols))]
        sz = hr(size[0], size[1], seed, i, 2)
        if burst is not None:
            ang = hash01(seed, i, 3) * 6.283
            sp = burst[1] * hr(0.3, 1.0, seed, i, 4)
            tt = max(0.0, t - burst[0])
            dist = sp * (1 - math.exp(-tt * 3.0)) / 3.0
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist + grav * tt * tt
        else:
            x = cx + (hash01(seed, i, 3) - 0.5) * spread * 1.9
            y = cy + (hash01(seed, i, 4) - 0.5) * spread + grav * t
            x += 14 * math.sin(t * hr(0.5, 2, seed, i, 5) + i)
        rot = hash01(seed, i, 6) * 360 + t * spin * hr(-200, 200, seed, i, 7)
        sh = shapes[int(hash01(seed, i, 8) * len(shapes))]
        pp = paint(col, a)
        if sh == "d":
            c.drawCircle(x, y, sz * 0.5, pp)
        elif sh == "t":
            c.drawPath(P_poly(x, y, sz * 0.7, 3, rot), pp)
        elif sh == "r":
            c.save()
            c.translate(x, y)
            c.rotate(rot)
            c.drawRect(skia.Rect(-sz * 0.5, -sz * 0.22, sz * 0.5, sz * 0.22), pp)
            c.restore()
        elif sh == "s":
            c.drawPath(P_sparkle(x, y, sz, rot), pp)
        elif sh == "o":
            c.drawCircle(x, y, sz * 0.45, paint(col, a, stroke=sz * 0.18))
