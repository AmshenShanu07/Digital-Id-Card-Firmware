#!/usr/bin/env python3
"""Convert an animated GIF into a C header of JPEG frames for the ESP32.

Usage:
    python gif_to_header.py INPUT.gif OUTPUT_HEADER [--quality 75] [--slowdown 1.0]

Every frame is scaled and center-cropped to 240x280, JPEG-compressed, and
stored back to back in flash. The firmware decodes one frame at a time
with the JPEGDEC library, so a long GIF fits in a few hundred KB.
"""

import argparse
import io
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence

WIDTH = 240
HEIGHT = 280
BACKGROUND = (0, 0, 0)
MIN_FRAME_DELAY_MS = 20
BYTES_PER_LINE = 16


def encode_frame(frame: Image.Image, quality: int) -> bytes:
    """Composite onto a black background, fit to the screen, return JPEG bytes."""
    frame = frame.convert("RGBA")
    background = Image.new("RGBA", frame.size, BACKGROUND + (255,))
    background.alpha_composite(frame)

    frame = ImageOps.fit(
        background.convert("RGB"), (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS
    )

    buffer = io.BytesIO()
    frame.save(
        buffer,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=False,  # JPEGDEC cannot decode progressive JPEGs
        subsampling=2,
    )
    return buffer.getvalue()


def format_array(declaration: str, values: list) -> list:
    return [declaration + " = {", "  " + ", ".join(str(v) for v in values), "};", ""]


def convert_gif(input_path: Path, output_path: Path, quality: int, slowdown: float) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"GIF not found: {input_path}")

    gif = Image.open(input_path)

    jpeg_frames = []
    delays = []

    print("Converting GIF...")
    for index, frame in enumerate(ImageSequence.Iterator(gif)):
        # Read the duration before convert(), which drops frame.info
        delay = int(frame.info.get("duration", 100) * slowdown)

        jpeg = encode_frame(frame, quality)
        jpeg_frames.append(jpeg)
        delays.append(max(MIN_FRAME_DELAY_MS, delay))
        print(f"  Frame {index + 1}: {len(jpeg):,} bytes | {delay} ms")

    offsets, sizes, blob = [], [], bytearray()
    for jpeg in jpeg_frames:
        offsets.append(len(blob))
        sizes.append(len(jpeg))
        blob.extend(jpeg)

    lines = [
        "#pragma once",
        "#include <Arduino.h>",
        "",
        f"#define FRAME_COUNT {len(jpeg_frames)}",
        f"#define FRAME_WIDTH {WIDTH}",
        f"#define FRAME_HEIGHT {HEIGHT}",
        "",
        "const uint8_t animationData[] PROGMEM = {",
    ]
    for i in range(0, len(blob), BYTES_PER_LINE):
        chunk = blob[i : i + BYTES_PER_LINE]
        lines.append("  " + ", ".join(f"0x{b:02X}" for b in chunk) + ",")
    lines += ["};", ""]

    lines += format_array("const uint32_t frameOffsets[FRAME_COUNT] PROGMEM", offsets)
    lines += format_array("const uint32_t frameSizes[FRAME_COUNT] PROGMEM", sizes)
    lines += format_array("const uint16_t frameDelays[FRAME_COUNT] PROGMEM", delays)

    output_path.write_text("\n".join(lines))

    raw_size = WIDTH * HEIGHT * 2 * len(jpeg_frames)
    print("\n=== Conversion complete ===")
    print(f"Frames:          {len(jpeg_frames)}")
    print(f"Resolution:      {WIDTH} x {HEIGHT}")
    print(f"Raw RGB565 size: {raw_size:,} bytes")
    print(f"JPEG size:       {len(blob):,} bytes")
    print(f"Space saved:     {(1 - len(blob) / raw_size) * 100:.1f}%")
    print(f"Output:          {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input", type=Path, help="source GIF")
    parser.add_argument("output", type=Path, help="output header, e.g. animation.h")
    parser.add_argument("--quality", type=int, default=75, help="JPEG quality 1-95 (default 75)")
    parser.add_argument(
        "--slowdown",
        type=float,
        default=1.0,
        help="playback time multiplier: 1.0 = original speed, 2.0 = twice as slow",
    )
    args = parser.parse_args()
    convert_gif(args.input, args.output, args.quality, args.slowdown)


if __name__ == "__main__":
    main()
