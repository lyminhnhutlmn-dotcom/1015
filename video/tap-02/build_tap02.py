#!/usr/bin/env python3
"""Dựng animatic Tập 02 — Cửa khoá hết.

8 still 9:16 + Ken Burns + phụ đề + 1 câu TTS + bước chân + khoá từ.
Output: 1080×1920, 30 fps, đúng 60.000 giây.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
STILLS = ROOT / "stills"
AUDIO = ROOT / "audio"
OUT = ROOT / "tap-02-cua-khoa-het.mp4"
FONT = Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")
W, H, FPS = 1080, 1920, 30

SHOTS = [
    ("shot-01-gieng.jpg", 3.0, (1.00, 1.14, 0.15, 0.45)),
    ("shot-02-leo.jpg", 5.0, (1.02, 1.16, 0.55, 0.30)),
    ("shot-03-duoi.jpg", 10.0, (1.00, 1.18, 0.20, 0.40)),
    ("shot-04-tang12.jpg", 10.0, (1.00, 1.12, 0.45, 0.35)),
    ("shot-05-tang14.jpg", 10.0, (1.00, 1.12, 0.40, 0.28)),
    ("shot-06-mat.jpg", 10.0, (1.02, 1.14, 0.30, 0.22)),
    ("shot-07-mui-ten.jpg", 6.0, (1.00, 1.16, 0.50, 0.35)),
    ("shot-08-buoc.jpg", 4.0, (1.04, 1.16, 0.25, 0.40)),
    ("shot-07-mui-ten.jpg", 2.0, (1.16, 1.16, 0.35, 0.35)),
]

CAPTIONS = [
    (8.00, 14.00, "Bước dưới. Đều."),
    (20.00, 27.40, "TẦNG 12 · KHOÁ TỪ"),
    (32.00, 35.80, "TẦNG 14 · KHOÁ TỪ"),
    (36.00, 39.60, "HÀ: Mười bốn cũng khoá."),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd[:8]), "..." if len(cmd) > 8 else "")
    subprocess.run(cmd, check=True)


def stamp_world_text(im: Image.Image, text: str, y_frac: float = 0.72) -> Image.Image:
    """Chữ thế giới trên still nguồn 720×1280 — scale theo ảnh."""
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    w, h = im.size
    size = max(28, int(w * 0.07))
    font = ImageFont.truetype(str(FONT), size)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = int(h * y_frac)
    pad = 10
    d.rectangle((x - pad, y - 6, x + tw + pad, y + th + 10), fill=(0, 0, 0))
    d.text((x - bbox[0], y - bbox[1]), text, font=font, fill=(236, 220, 120))
    return im


def prepare_stills(src_dir: Path) -> None:
    STILLS.mkdir(parents=True, exist_ok=True)
    mapping = {
        "tap02-shot-01-gieng.jpg": "shot-01-gieng.jpg",
        "tap02-shot-02-leo.jpg": "shot-02-leo.jpg",
        "tap02-shot-03-duoi.jpg": "shot-03-duoi.jpg",
        "tap02-shot-04-tang12.jpg": "shot-04-tang12.jpg",
        "tap02-shot-05-tang14.jpg": "shot-05-tang14.jpg",
        "tap02-shot-06-mat.jpg": "shot-06-mat.jpg",
        "tap02-shot-07-mui-ten.jpg": "shot-07-mui-ten.jpg",
        "tap02-shot-08-buoc.jpg": "shot-08-buoc.jpg",
    }
    for src_name, dest_name in mapping.items():
        src = src_dir / src_name
        dest = STILLS / dest_name
        im = Image.open(src)
        if dest_name == "shot-07-mui-ten.jpg":
            im = stamp_world_text(im, "SÂN THƯỢNG", 0.78)
            im.save(dest, quality=92)
        else:
            shutil.copy2(src, dest)


def _draw_text_centered(
    d: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
    tracking: int = 0,
) -> None:
    glyphs = list(text)
    widths = []
    for g in glyphs:
        b = d.textbbox((0, 0), g, font=font)
        widths.append(b[2] - b[0])
    total = sum(widths) + tracking * max(0, len(glyphs) - 1)
    x = (W - total) // 2
    for g, gw in zip(glyphs, widths):
        d.text((x, y), g, font=font, fill=fill)
        x += gw + tracking


def make_end_card(path: Path) -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(H * 0.56), W, int(H * 0.88)), fill=(0, 0, 0, 185))
    title = ImageFont.truetype(str(FONT), 62)
    sub = ImageFont.truetype(str(FONT), 44)
    _draw_text_centered(d, int(H * 0.63), "CHỈ CÒN MỘT CỬA", title, (255, 255, 255, 255), 2)
    _draw_text_centered(d, int(H * 0.73), "TẬP SAU", sub, (228, 206, 140, 255), 6)
    im.save(path)


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w in words:
        trial = w if not cur else f"{cur} {w}"
        b = tmp.textbbox((0, 0), trial, font=font)
        if b[2] - b[0] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def make_caption_png(text: str, path: Path) -> None:
    font = ImageFont.truetype(str(FONT), 44)
    lines = _wrap(text, font, 900)
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    sizes = [tmp.textbbox((0, 0), ln, font=font) for ln in lines]
    line_h = max(s[3] - s[1] for s in sizes) + 8
    tw = max(s[2] - s[0] for s in sizes)
    th = line_h * len(lines)
    pad_x, pad_y = 36, 22
    box_w, box_h = tw + pad_x * 2, th + pad_y * 2
    y0 = 1280
    x0 = (W - box_w) // 2
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), radius=18, fill=(0, 0, 0, 165))
    for i, ln in enumerate(lines):
        b = sizes[i]
        ln_w = b[2] - b[0]
        od.text(
            (x0 + (box_w - ln_w) // 2 - b[0], y0 + pad_y + i * line_h - b[1]),
            ln,
            font=font,
            fill=(255, 255, 255, 255),
        )
    overlay.save(path)


async def synth_voices() -> None:
    import edge_tts

    AUDIO.mkdir(parents=True, exist_ok=True)
    dest = AUDIO / "ha.mp3"
    if dest.exists():
        print("tts cache hit")
        return
    comm = edge_tts.Communicate(
        "Mười bốn cũng khoá.",
        "vi-VN-HoaiMyNeural",
        rate="-18%",
        pitch="-8Hz",
    )
    await comm.save(str(dest))
    print("tts", dest, dest.stat().st_size)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def make_ambience(path: Path) -> None:
    # Hầm thang: ầm thấp + tiếng bước hai nhịp + hai tiếng khoá từ.
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=color=brown:amplitude=0.20:sample_rate=48000:duration=60",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=52:sample_rate=48000:duration=60",
            "-f",
            "lavfi",
            "-i",
            "aevalsrc=0.55*sin(2*PI*68*t)*exp(-22*mod(t\\,0.58)):s=48000:d=60",
            "-f",
            "lavfi",
            "-i",
            "aevalsrc=0.42*sin(2*PI*55*t)*exp(-20*mod(t+0.29\\,0.64)):s=48000:d=60",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1350:sample_rate=48000:duration=0.14",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1180:sample_rate=48000:duration=0.16",
            "-filter_complex",
            "[0]lowpass=f=380,volume=0.9[a];"
            "[1]volume=0.08[b];"
            "[2]highpass=f=40,volume=0.55[c];"
            "[3]highpass=f=40,volume=0.45[d];"
            "[4]adelay=22000|22000,volume=0.9[lock1];"
            "[5]adelay=33000|33000,volume=0.9[lock2];"
            "[a][b][c][d][lock1][lock2]amix=inputs=6:duration=first:normalize=0,"
            "alimiter=limit=0.45",
            "-t",
            "60",
            str(path),
        ]
    )


def ken_burns_clip(src: Path, dest: Path, dur: float, kb: tuple[float, float, float, float]) -> None:
    z0, z1, y0, y1 = kb
    frames = max(1, int(round(dur * FPS)))
    z_expr = f"{z0:.4f}+({z1:.4f}-{z0:.4f})*on/{frames}"
    y_expr = f"({y0:.4f}+({y1:.4f}-{y0:.4f})*on/{frames})*(ih-ih/zoom)"
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='{y_expr}':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(src),
            "-vf",
            vf,
            "-frames:v",
            str(frames),
            "-r",
            str(FPS),
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-an",
            str(dest),
        ]
    )


def overlay_end_card(clip: Path, card: Path, dest: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(clip),
            "-i",
            str(card),
            "-filter_complex",
            "[0:v]eq=brightness=-0.18:saturation=0.85[v];[v][1:v]overlay=0:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def concat_clips(clips: list[Path], dest: Path) -> None:
    lst = dest.with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            str(dest),
        ]
    )


def burn_subs_and_mix(
    video: Path,
    caps: list[Path],
    amb: Path,
    ha: Path,
    dest: Path,
) -> None:
    v_in = ["-i", str(video), "-i", str(amb), "-i", str(ha)]
    overlays = []
    last = "0:v"
    for i, ((a, b, _t), png) in enumerate(zip(CAPTIONS, caps)):
        v_in += ["-i", str(png)]
        src = str(3 + i)
        nxt = f"v{i}"
        overlays.append(
            f"[{last}][{src}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]"
        )
        last = nxt
    vf = ";".join(overlays)
    fc = (
        "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,volume=0.85[amb];"
        "[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
        "adelay=36000|36000,volume=2.4,lowpass=f=4000[ha];"
        "[amb][ha]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.90[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            *v_in,
            "-filter_complex",
            f"{vf};{fc}",
            "-map",
            f"[{last}]",
            "-map",
            "[a]",
            "-t",
            "60",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )


def main() -> None:
    src_dir = Path(os.environ.get("TAP02_SRC", "/opt/cursor/artifacts/assets"))
    prepare_stills(src_dir)
    asyncio.run(synth_voices())

    work = Path(tempfile.mkdtemp(prefix="tap02-"))
    print("work", work)
    card = work / "endcard.png"
    amb = work / "amb.wav"
    caps: list[Path] = []
    for i, (_a, _b, text) in enumerate(CAPTIONS):
        p = work / f"cap-{i:02d}.png"
        make_caption_png(text, p)
        caps.append(p)
    make_end_card(card)
    make_ambience(amb)

    clips: list[Path] = []
    for i, (name, dur, kb) in enumerate(SHOTS):
        clip = work / f"clip-{i:02d}.mp4"
        ken_burns_clip(STILLS / name, clip, dur, kb)
        if i == len(SHOTS) - 1:
            frozen = work / "clip-end.mp4"
            overlay_end_card(clip, card, frozen)
            clips.append(frozen)
        else:
            clips.append(clip)

    silent = work / "silent.mp4"
    concat_clips(clips, silent)
    burn_subs_and_mix(silent, caps, amb, AUDIO / "ha.mp3", OUT)

    dur = probe_duration(OUT)
    print(f"DONE {OUT} duration={dur:.3f}s size={OUT.stat().st_size}")
    if abs(dur - 60.0) > 0.15:
        raise SystemExit(f"duration {dur} != 60")


if __name__ == "__main__":
    main()
