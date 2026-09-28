"""Frame-level effects on HxWx4 uint8 BGRA frames (alpha ignored unless stated)."""
from __future__ import annotations

import functools
import math

import cv2
import numpy as np

from core import W, H, CX, CY, clamp, hash01, hr, lerp

WH = (W, H)


def affine(img, dx=0.0, dy=0.0, rot=0.0, s=1.0, cx=CX, cy=CY, border=cv2.BORDER_REFLECT, val=(0, 0, 0, 255)):
    if abs(dx) + abs(dy) + abs(rot) < 1e-3 and abs(s - 1) < 1e-5:
        return img
    M = cv2.getRotationMatrix2D((cx, cy), rot, s)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img, M, WH, flags=cv2.INTER_LINEAR, borderMode=border, borderValue=val)


def zoom_blur(img, amt, cx=CX, cy=CY, passes=2):
    """Radial zoom blur (outward).  amt = total scale spread, e.g. 0.3."""
    if amt < 0.004:
        return img
    f = img.astype(np.float32)
    n = 4
    base = (1.0 + amt) ** (1.0 / (n ** passes - 1))
    for ps in range(passes):
        st = base ** (n ** ps)
        acc = f.copy()
        for i in range(1, n):
            sc = st ** i
            M = np.float32([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]])
            acc += cv2.warpAffine(f, M, WH, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        f = acc * (1.0 / n)
    return np.clip(f + 0.5, 0, 255).astype(np.uint8)


def spin_blur(img, deg, cx=CX, cy=CY, n=8):
    if abs(deg) < 0.2:
        return img
    f = img.astype(np.float32)
    acc = f.copy()
    for i in range(1, n):
        M = cv2.getRotationMatrix2D((cx, cy), deg * i / (n - 1) - deg / 2, 1.0)
        acc += cv2.warpAffine(f, M, WH, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(acc / n + 0.5, 0, 255).astype(np.uint8)


def hblur(img, L):
    L = int(abs(L))
    return cv2.blur(img, (L, 1)) if L >= 2 else img


def vblur(img, L):
    L = int(abs(L))
    return cv2.blur(img, (1, L)) if L >= 2 else img


def gblur(img, s):
    return cv2.GaussianBlur(img, (0, 0), s) if s > 0.3 else img


def shift(ch, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(ch, M, WH, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def rgb_split(img, dx, dy=0.0):
    if abs(dx) + abs(dy) < 0.3:
        return img
    out = img.copy()
    out[..., 2] = shift(img[..., 2], dx, dy)
    out[..., 0] = shift(img[..., 0], -dx, -dy)
    return out


def radial_chroma(img, amt, cx=CX, cy=CY):
    """amt in px at the frame edge."""
    if amt < 0.3:
        return img
    out = img.copy()
    for ch, k in ((2, 1.0), (0, -1.0)):
        s = 1.0 + k * amt / (W / 2)
        M = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
        out[..., ch] = cv2.warpAffine(img[..., ch], M, WH, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


def slices(img, seed, n=8, amp=60.0, hmin=6, hmax=60, tint=True):
    out = img.copy()
    for i in range(n):
        y = int(hash01(seed, i, 1) * H)
        y1 = min(H, y + int(hr(hmin, hmax, seed, i, 2)))
        dx = int(hr(-amp, amp, seed, i, 3))
        out[y:y1] = np.roll(img[y:y1], dx, axis=1)
        if tint:
            r = hash01(seed, i, 4)
            if r < 0.2:
                out[y:y1, :, :3] = out[y:y1, :, 2::-1][:, :, :3]
            elif r < 0.3:
                out[y:y1, :, :3] = 255 - out[y:y1, :, :3]
    return out


def blocks(img, seed, n=14, smin=16, smax=110, amp=90.0, inv=0.25):
    out = img.copy()
    for i in range(n):
        w = int(hr(smin, smax * 2.2, seed, i, 1))
        h = int(hr(smin * 0.5, smax, seed, i, 2))
        x = int(hash01(seed, i, 3) * max(1, W - w))
        y = int(hash01(seed, i, 4) * max(1, H - h))
        sx = int(clamp(x + hr(-amp, amp, seed, i, 5), 0, W - w))
        sy = int(clamp(y + hr(-amp, amp, seed, i, 6) * 0.3, 0, H - h))
        out[y:y + h, x:x + w] = img[sy:sy + h, sx:sx + w]
        r = hash01(seed, i, 7)
        if r < inv:
            out[y:y + h, x:x + w, :3] = 255 - out[y:y + h, x:x + w, :3]
        elif r < inv + 0.2:
            out[y:y + h, x:x + w, :3] = out[y:y + h, x:x + w, [1, 2, 0]]
    return out


def mosaic(img, px):
    px = int(px)
    if px < 2:
        return img
    small = cv2.resize(img, (max(1, W // px), max(1, H // px)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, WH, interpolation=cv2.INTER_NEAREST)


def flash(img, a, col=(255, 255, 255)):
    if a <= 0.003:
        return img
    a = clamp(a)
    out = img.copy()
    c = np.array([col[2], col[1], col[0]], np.float32)
    out[..., :3] = np.clip(img[..., :3].astype(np.float32) * (1 - a) + c * a + 0.5, 0, 255).astype(np.uint8)
    return out


def invert(img, a=1.0):
    out = img.copy()
    if a >= 1:
        out[..., :3] = 255 - img[..., :3]
    else:
        f = img[..., :3].astype(np.float32)
        out[..., :3] = np.clip(f * (1 - a) + (255 - f) * a, 0, 255).astype(np.uint8)
    return out


def mix(a, b, t):
    if t <= 0:
        return a
    if t >= 1:
        return b
    return cv2.addWeighted(a, 1 - t, b, t, 0)


def mask_mix(a, b, m):
    """m float32 HxW in [0,1]: 0 -> a, 1 -> b."""
    m3 = m[..., None]
    return np.clip(a.astype(np.float32) * (1 - m3) + b.astype(np.float32) * m3 + 0.5, 0, 255).astype(np.uint8)


def duotone(img, dark, light, a=1.0):
    g = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None] / 255.0
    d = np.array([dark[2], dark[1], dark[0]], np.float32)
    l = np.array([light[2], light[1], light[0]], np.float32)
    res = d * (1 - g) + l * g
    out = img.copy()
    out[..., :3] = np.clip(img[..., :3] * (1 - a) + res * a, 0, 255).astype(np.uint8)
    return out


def bloom(img, thr=0.6, amt=0.6):
    small = cv2.resize(img[..., :3], (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    k = np.clip((small.max(axis=2, keepdims=True) - thr) / (1 - thr), 0, 1)
    br = small * k
    bl = cv2.GaussianBlur(br, (0, 0), 3) * 0.5 + cv2.GaussianBlur(br, (0, 0), 10) * 0.4 + cv2.GaussianBlur(br, (0, 0), 24) * 0.3
    bl = cv2.resize(bl, WH, interpolation=cv2.INTER_LINEAR)
    f = img[..., :3].astype(np.float32) / 255.0
    f = 1 - (1 - f) * (1 - np.clip(bl * amt, 0, 1))
    out = img.copy()
    out[..., :3] = np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


@functools.lru_cache(maxsize=4)
def _vig(strength, power):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - CX) / CX) ** 2 + ((yy - CY) / CY) ** 2) / math.sqrt(2)
    return (1 - strength * r ** power).astype(np.float32)[..., None]


def vignette(img, strength=0.4, power=2.2):
    if strength <= 0.01:
        return img
    out = img.copy()
    out[..., :3] = np.clip(img[..., :3] * _vig(round(strength, 2), power), 0, 255).astype(np.uint8)
    return out


@functools.lru_cache(maxsize=1)
def _grain_tile():
    rng = np.random.default_rng(99)
    return np.clip(np.round(rng.normal(0, 1.0, (H + 64, W + 64))), -4, 4).astype(np.float32)


def grain(img, fi, amt=3.0):
    if amt <= 0.1:
        return img
    ox, oy = int(hash01(fi, 1) * 64), int(hash01(fi, 2) * 64)
    g = (_grain_tile()[oy:oy + H, ox:ox + W] * amt).astype(np.int16)[..., None]
    out = img.copy()
    out[..., :3] = np.clip(img[..., :3].astype(np.int16) + g, 0, 255).astype(np.uint8)
    return out


@functools.lru_cache(maxsize=1)
def _finish_fields():
    """Low-resolution UV/light fields; spatial work is shared by every frame."""
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    u, v = xx / (W // 4 - 1), yy / (H // 4 - 1)
    radius = ((u - 0.5) * 1.35) ** 2 + ((v - 0.5) * 1.1) ** 2
    return u, v, radius


def finish_shader(img, t, dark, fi):
    """Image-space glass/film shader: moving light, halation and soft split tone.

    Highlights stay neutral and text geometry stays untouched. The procedural
    lighting and bloom run at quarter resolution, then composite in one pass.
    """
    u, v, radius = _finish_fields()
    small = cv2.resize(img[..., :3], (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    threshold = lerp(0.82, 0.66, dark)
    bright = small * np.clip((small.max(axis=2, keepdims=True) - threshold) / (1 - threshold), 0, 1)
    glow = cv2.GaussianBlur(bright, (0, 0), 2.5) * 0.65
    glow += cv2.GaussianBlur(bright, (0, 0), 11) * 0.35
    glow *= lerp(0.13, 0.38, dark)
    # Broad cyan/rose reflections drift continuously, never a full-frame flash.
    phase = u * 2.6 + v * 1.4 - t * 0.12
    sheen = (0.5 + 0.5 * np.cos(phase * math.tau)) ** 8
    tint = np.empty_like(small)
    tint[..., 0] = 0.018 + 0.030 * sheen
    tint[..., 1] = -0.006 + 0.010 * sheen
    tint[..., 2] = 0.012 + 0.036 * (1 - sheen)
    tint *= lerp(0.65, 1.0, dark)
    light = cv2.resize(tint, WH, interpolation=cv2.INTER_LINEAR)
    bloom_field = cv2.resize(glow, WH, interpolation=cv2.INTER_LINEAR)
    vignette_field = cv2.resize(1 - radius * lerp(0.07, 0.30, dark), WH, interpolation=cv2.INTER_LINEAR)[..., None]
    f = img[..., :3].astype(np.float32) / 255.0
    # A midtone mask keeps paper whites clean and deep blacks anchored.
    lum = f[..., 2:3] * 0.2126 + f[..., 1:2] * 0.7152 + f[..., 0:1] * 0.0722
    f += light * (4 * lum * (1 - lum))
    f = 1 - (1 - f) * (1 - bloom_field)
    f *= vignette_field
    ox, oy = int(hash01(fi, 1) * 64), int(hash01(fi, 2) * 64)
    f += _grain_tile()[oy:oy + H, ox:ox + W, None] * (lerp(0.65, 1.25, dark) / 255)
    out = img.copy()
    out[..., :3] = np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


def scanlines(img, a=0.2, period=3):
    out = img.copy()
    out[::period, :, :3] = (out[::period, :, :3].astype(np.float32) * (1 - a)).astype(np.uint8)
    return out


def smear(img, seed, n=6, hmin=10, hmax=80, frac=(0.2, 0.8)):
    """Pixel-sort-ish smear: horizontal bands stretched from a pivot column."""
    out = img.copy()
    for i in range(n):
        y = int(hash01(seed, i, 1) * H)
        y1 = min(H, y + int(hr(hmin, hmax, seed, i, 2)))
        x0 = int(hr(frac[0], frac[1], seed, i, 3) * W)
        if hash01(seed, i, 4) < 0.5:
            out[y:y1, x0:] = img[y:y1, x0:x0 + 1]
        else:
            out[y:y1, :x0] = img[y:y1, x0:x0 + 1]
    return out


@functools.lru_cache(maxsize=8)
def _fish_maps(k):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - CX) / CX, (yy - CY) / CX
    r2 = nx * nx + ny * ny
    f = 1 + k * r2
    return (CX + nx * CX / f).astype(np.float32), (CY + ny * CX / f).astype(np.float32)


def fisheye(img, k):
    if abs(k) < 0.01:
        return img
    mx, my = _fish_maps(round(k, 2))
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


@functools.lru_cache(maxsize=1)
def _crt_fields():
    """Fixed convex tube geometry and phosphor raster, shared by all scenes."""
    xx, yy = _base_grid()
    nx, ny = (xx - CX) / CX, (yy - CY) / CY
    # Inverse barrel mapping bows the picture edges without cropping to 4:3.
    sx = nx * (1.006 + 0.055 * ny * ny)
    sy = ny * (1.006 + 0.055 * nx * nx)
    mx, my = (CX + sx * CX).astype(np.float32), (CY + sy * CY).astype(np.float32)
    # Rounded tube corners in source space, with a two-pixel feather.
    radius = 24.0
    qx = np.abs(sx * CX) - (CX - radius)
    qy = np.abs(sy * CY) - (CY - radius)
    distance = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2)
    distance += np.minimum(np.maximum(qx, qy), 0) - radius
    aperture = np.clip(0.5 - distance / 2, 0, 1)
    edge = 1 - 0.11 * ((nx * nx + ny * ny) / 2) ** 1.4
    rows = np.arange(H, dtype=np.float32)[:, None]
    scan = 0.965 + 0.035 * np.cos(rows * (math.tau / 3))
    return mx, my, (aperture * edge)[..., None], rows, scan[..., None]


def vhs_crt(img, t, fi):
    """Uniform VHS signal + subtly curved CRT; never modulated by shot or beat."""
    mx, my, glass, rows, scan = _crt_fields()
    # VHS loses horizontal colour bandwidth before luminance detail.
    ycc = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2YCrCb)
    chroma = cv2.resize(ycc[..., 1:], (W // 4, H), interpolation=cv2.INTER_AREA)
    chroma = cv2.GaussianBlur(chroma, (5, 1), 0.8)
    chroma = cv2.resize(chroma, WH, interpolation=cv2.INTER_LINEAR)
    chroma = cv2.warpAffine(chroma, np.float32([[1, 0, 1.5], [0, 1, 0]]), WH,
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ycc[..., 1:] = np.clip((chroma.astype(np.float32) - 128) * 0.93 + 128, 0, 255).astype(np.uint8)
    ycc[..., 0] = cv2.GaussianBlur(ycc[..., 0], (3, 1), 0.55)
    signal = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2BGR).astype(np.float32)
    # Gentle pedestal/shoulder, fine tape noise and slow brightness roll.
    signal *= 0.965
    signal += 3.0
    ox, oy = int(hash01(fi, 81) * 64), int(hash01(fi, 83) * 64)
    signal += _grain_tile()[oy:oy + H, ox:ox + W, None] * 1.25
    signal *= 1 - 0.010 * (0.5 + 0.5 * np.sin(rows[..., None] / H * math.tau - t * 1.1))
    # A restrained moving head-switching band gives the tape a physical
    # transport cue while leaving titles and faces legible.
    track_y = (H * (0.16 + 0.76 * ((t * 0.075) % 1.0)))
    track = np.exp(-((rows - track_y) / 15.0) ** 2)[..., None]
    signal += (2.2 * track) * (0.55 + 0.45 * np.sin(t * 7.0))
    # Subpixel time-base drift, not the large random jumps of a damaged tape.
    drift = 0.30 * math.sin(t * 2.1) + 0.24 * np.sin(rows * 0.023 + t * 1.7)
    curved = cv2.remap(signal, mx + drift, my, cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    curved *= scan * glass
    out = img.copy()
    out[..., :3] = np.clip(curved + 0.5, 0, 255).astype(np.uint8)
    return out


@functools.lru_cache(maxsize=2)
def _base_grid():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return xx, yy


def wave_warp(img, t, amp=8.0, freq=0.02, axis=0):
    xx, yy = _base_grid()
    if axis == 0:
        mx = xx + amp * np.sin(yy * freq + t)
        my = yy
    else:
        mx = xx
        my = yy + amp * np.sin(xx * freq + t)
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def swirl(img, t, strength=1.5, radius=520.0, cx=CX, cy=CY):
    xx, yy = _base_grid()
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy)
    a = strength * np.exp(-(r / radius) ** 2) + 0 * t
    ca, sa = np.cos(a), np.sin(a)
    mx = cx + dx * ca - dy * sa
    my = cy + dx * sa + dy * ca
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def levels(img, gain=1.0, bias=0.0):
    out = img.copy()
    out[..., :3] = np.clip(img[..., :3].astype(np.float32) * gain + bias, 0, 255).astype(np.uint8)
    return out


def black():
    a = np.zeros((H, W, 4), np.uint8)
    a[..., 3] = 255
    return a


def solid(col):
    a = np.empty((H, W, 4), np.uint8)
    a[..., 0], a[..., 1], a[..., 2], a[..., 3] = col[2], col[1], col[0], 255
    return a
