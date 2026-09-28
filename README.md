# MotionGraphic-Bochi

motion graphic Bocchi, full Python. 1280x660, 60 fps, sekitar 45 detik, dengan efek VHS/CRT.

nggak perlu file referensi. source, font, gambar, dan audio yang dipakai render sudah ada di repo.

## cara paling malas

Windows, tinggal copy-paste:

```bat
git clone https://github.com/Xelszy/MotionGraphic-Bochi.git
cd MotionGraphic-Bochi
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python render.py --full --fps 60 --workers 8 --crf 16 --out MotionGraphic-Bochi.mp4
```

hasilnya ada di:

```text
build/MotionGraphic-Bochi.mp4
```

Linux/macOS beda aktivasi saja:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python render.py --full --fps 60 --workers 8 --crf 16 --out MotionGraphic-Bochi.mp4
```

## kalau cuma mau lihat beberapa frame

lebih cepat daripada render video penuh:

```bat
python render.py --beats 4,20,44,67 --workers 4
```

hasil PNG masuk ke `build/stills/`.

mau contact sheet:

```bat
python render.py --sheet 0:68:2 --name preview --workers 4
```

hasil JPG masuk ke `out/sheet_preview*.jpg`.

## cek hasil render

```bat
python tools/verify.py build/MotionGraphic-Bochi.mp4
```

ini mengecek jumlah frame, durasi, sinkronisasi audio, beat, frame hitam terakhir, dan kecocokan frame dengan engine.

cek flashing secara terpisah:

```bat
python tools/flashscan.py build/MotionGraphic-Bochi.mp4
```

## file yang biasanya diedit

- `shots_a.py` — bagian awal.
- `shots_b.py` — bagian tengah.
- `shots_c.py` — bagian gelap sampai ending.
- `core.py` — drawing, font, warna, timing, dan asset loader.
- `kin.py` — animasi teks.
- `trans.py` — transisi.
- `fx.py` — glitch, grading, VHS, dan CRT.
- `engine.py` — timeline dan compositing.
- `render.py` — render frame, sheet, dan MP4.

habis edit shot, jangan langsung full render. cek beat yang diubah dulu:

```bat
python render.py --beats 20,20.5,21 --workers 4
```

kalau sudah aman baru render penuh.

## catatan

- target environment: Python `3.11.2`.
- versi package dikunci di `requirements.txt`.
- audio render ada di `audio/song.mp3`.
- file referensi, hasil render, virtual environment, dan file kerja memang tidak ikut Git.
- video menggunakan flashing dan glitch yang cukup intens.
- pastikan penggunaan ulang audio, font, dan gambar sesuai hak yang kamu miliki.
