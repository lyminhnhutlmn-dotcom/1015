#!/usr/bin/env python3
"""Dựng animatic Tập 01 — Số trên lòng bàn tay.

8 still 9:16 + Ken Burns + phụ đề + TTS tiếng Việt + ambience hầm xe.
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
OUT = ROOT / "tap-01-so-tren-long-ban-tay.mp4"
FONT = Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")
FONT_REG = Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf")
W, H, FPS = 1080, 1920, 30

SHOTS = [
    # file, seconds, ken-burns (z0, z1, y0, y1) as 0–1 fractions of leftover
    ("shot-01-den.jpg", 3.0, (1.00, 1.16, 0.50, 0.20)),
    ("shot-02-chay.jpg", 5.0, (1.04, 1.18, 0.85, 0.35)),
    ("shot-03-may.jpg", 6.0, (1.00, 1.20, 0.45, 0.40)),
    ("shot-04-ha.jpg", 14.0, (1.02, 1.14, 0.35, 0.28)),
    ("shot-05-1015.jpg", 10.0, (1.00, 1.22, 0.55, 0.45)),
    ("shot-06-giay.jpg", 10.0, (1.00, 1.12, 0.70, 0.45)),
    ("shot-07-hai-doi.jpg", 6.0, (1.02, 1.10, 0.55, 0.40)),
    ("shot-08-cua.jpg", 4.0, (1.04, 1.18, 0.50, 0.25)),
    ("shot-07-hai-doi.jpg", 2.0, (1.10, 1.10, 0.40, 0.40)),  # đóng băng + card
]

CAPTIONS = [
    (6.00, 8.20, "MAI: Mai đây, để lại lời nhắn nha."),
    (14.00, 19.80, "HÀ: Nếu chị có chuyện gì… nhớ số này."),
    (20.00, 25.40, "1015. Chỗ của hai chị em."),
    (25.60, 28.00, "Chị thương em."),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd[:8]), "..." if len(cmd) > 8 else "")
    subprocess.run(cmd, check=True)


def fix_mai_label(src: Path, dest: Path) -> None:
    """Che chữ lỗi trên màn, viết lại Mai cùng tone kính nứt."""
    im = Image.open(src).convert("RGB")
    # dán mảng kính nứt (phía trên tên) lên toàn bộ chữ cũ — không để viên đen
    glass = im.crop((260, 500, 470, 590)).resize((230, 70))
    im.paste(glass, (250, 605))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(FONT_REG), 34)
    text = "Mai"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = 365 - tw // 2
    y = 628
    draw.text((x, y), text, font=font, fill=(236, 236, 236))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, quality=92)


def prepare_stills(src_dir: Path) -> None:
    STILLS.mkdir(parents=True, exist_ok=True)
    mapping = {
        "tap01-shot-01-den.jpg": "shot-01-den.jpg",
        "tap01-shot-02-chay.jpg": "shot-02-chay.jpg",
        "tap01-shot-03-may.jpg": "shot-03-may.jpg",
        "tap01-shot-04-ha.jpg": "shot-04-ha.jpg",
        "tap01-shot-05-1015.jpg": "shot-05-1015.jpg",
        "tap01-shot-06-giay.jpg": "shot-06-giay.jpg",
        "tap01-shot-07-hai-doi.jpg": "shot-07-hai-doi.jpg",
        "tap01-shot-08-cua.jpg": "shot-08-cua.jpg",
    }
    for src_name, dest_name in mapping.items():
        src = src_dir / src_name
        dest = STILLS / dest_name
        if dest_name == "shot-03-may.jpg":
            fix_mai_label(src, dest)
        else:
            shutil.copy2(src, dest)


def _draw_text_centered(
    d: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
    stroke: int = 0,
    stroke_fill: tuple[int, ...] | None = None,
    tracking: int = 0,
) -> None:
    """Vẽ một dòng, căn giữa, có tracking (px giữa chữ)."""
    glyphs = list(text)
    widths = []
    for g in glyphs:
        b = d.textbbox((0, 0), g, font=font, stroke_width=stroke)
        widths.append(b[2] - b[0])
    total = sum(widths) + tracking * max(0, len(glyphs) - 1)
    x = (W - total) // 2
    for g, gw in zip(glyphs, widths):
        d.text(
            (x, y),
            g,
            font=font,
            fill=fill,
            stroke_width=stroke,
            stroke_fill=stroke_fill,
        )
        x += gw + tracking


def make_end_card(path: Path) -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, int(H * 0.56), W, int(H * 0.88)), fill=(0, 0, 0, 185))
    title = ImageFont.truetype(str(FONT), 68)
    sub = ImageFont.truetype(str(FONT), 44)
    _draw_text_centered(
        d, int(H * 0.63), "AI Ở DƯỚI HẦM?", title, (255, 255, 255, 255), tracking=2
    )
    _draw_text_centered(
        d, int(H * 0.73), "TẬP SAU", sub, (228, 206, 140, 255), tracking=6
    )
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
    """Phụ đề PIL — Noto Sans, có khoảng trắng, không phụ thuộc libass."""
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
    od.rounded_rectangle(
        (x0, y0, x0 + box_w, y0 + box_h), radius=18, fill=(0, 0, 0, 165)
    )
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
    if (AUDIO / "mai.mp3").exists() and (AUDIO / "ha.mp3").exists():
        print("tts cache hit")
        return
    jobs = [
        (
            "Mai đây, để lại lời nhắn nha.",
            AUDIO / "mai.mp3",
            "+6%",
            "+4Hz",
        ),
        (
            "Mai... nếu chị có chuyện gì. Em nhớ số này. "
            "Một không một năm. Chỗ của hai chị em. Em sẽ hiểu. Chị thương em.",
            AUDIO / "ha.mp3",
            "-16%",
            "-8Hz",
        ),
    ]
    for text, path, rate, pitch in jobs:
        comm = edge_tts.Communicate(
            text, "vi-VN-HoaiMyNeural", rate=rate, pitch=pitch
        )
        await comm.save(str(path))
        print("tts", path, "bytes", path.stat().st_size)


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
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=color=brown:amplitude=0.22:sample_rate=48000:duration=60",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=58:sample_rate=48000:duration=60",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=10400:sample_rate=48000:duration=60",
            "-filter_complex",
            "[0]lowpass=f=400[a];[1]volume=0.07[b];[2]volume=0.012[c];"
            "[a][b][c]amix=inputs=3:weights=1 0.6 0.4:duration=first,"
            "alimiter=limit=0.35",
            "-t",
            "60",
            str(path),
        ]
    )


def ken_burns_clip(src: Path, dest: Path, dur: float, kb: tuple[float, float, float, float]) -> None:
    z0, z1, y0, y1 = kb
    frames = max(1, int(round(dur * FPS)))
    # zoompan d = số frame. Input scale lớn hơn canvas để zoom còn chỗ.
    # y0/y1: 0 = top, 1 = bottom of leftover.
    z_expr = f"{z0:.4f}+({z1:.4f}-{z0:.4f})*on/{frames}"
    y_expr = (
        f"({y0:.4f}+({y1:.4f}-{y0:.4f})*on/{frames})*(ih-ih/zoom)"
    )
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
    mai: Path,
    ha: Path,
    dest: Path,
) -> None:
    ha_dur = probe_duration(ha)
    target = 13.6
    tempo = ha_dur / target if ha_dur > target else 1.0
    tempo = min(max(tempo, 1.0), 1.25)
    ha_filter = f"atempo={tempo:.4f}," if tempo > 1.001 else ""

    # overlay từng tấm phụ đề theo đồng hồ
    v_in = ["-i", str(video), "-i", str(amb), "-i", str(mai), "-i", str(ha)]
    overlays = []
    last = "0:v"
    for i, ((a, b, _t), png) in enumerate(zip(CAPTIONS, caps)):
        v_in += ["-i", str(png)]
        src = str(4 + i)
        nxt = f"v{i}"
        overlays.append(
            f"[{last}][{src}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]"
        )
        last = nxt
    vf = ";".join(overlays)
    fc = (
        f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,volume=0.32[amb];"
        f"[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
        f"adelay=6000|6000,volume=2.6[mai];"
        f"[3:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
        f"{ha_filter}adelay=14000|14000,volume=2.2,lowpass=f=4200[ha];"
        f"[amb][mai][ha]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.92[a]"
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
    src_dir = Path(os.environ.get("TAP01_SRC", "/opt/cursor/artifacts/assets"))
    prepare_stills(src_dir)
    asyncio.run(synth_voices())

    work = Path(tempfile.mkdtemp(prefix="tap01-"))
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
    burn_subs_and_mix(silent, caps, amb, AUDIO / "mai.mp3", AUDIO / "ha.mp3", OUT)

    dur = probe_duration(OUT)
    print(f"DONE {OUT} duration={dur:.3f}s size={OUT.stat().st_size}")
    if abs(dur - 60.0) > 0.15:
        raise SystemExit(f"duration {dur} != 60")


if __name__ == "__main__":
    main()
