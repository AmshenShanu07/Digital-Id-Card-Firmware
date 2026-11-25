#!/usr/bin/env python3
"""Convert an image into a C header holding a 240x280 RGB565 bitmap.

Usage:
    python image_to_header.py INPUT_IMAGE OUTPUT_HEADER [--name imageOne]

The header defines `const uint16_t <name>Data[240 * 280] PROGMEM`.
The image is scaled and center-cropped to fill the screen.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageOps

WIDTH = 240
HEIGHT = 280
VALUES_PER_LINE = 12


def rgb888_to_rgb565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def convert_image(input_path: Path, output_path: Path, name: str) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    image = Image.open(input_path).convert("RGB")
    image = ImageOps.fit(
        image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )

    raw = image.tobytes()  # R, G, B bytes per pixel
    pixels = [rgb888_to_rgb565(*raw[i : i + 3]) for i in range(0, len(raw), 3)]

    lines = [
        "#pragma once",
        "#include <Arduino.h>",
        "",
        f"const uint16_t {name}Data[{WIDTH * HEIGHT}] PROGMEM = {{",
    ]
    for i in range(0, len(pixels), VALUES_PER_LINE):
        row = ", ".join(f"0x{p:04X}" for p in pixels[i : i + VALUES_PER_LINE])
        lines.append(f"  {row},")
    lines += ["};", ""]

    output_path.write_text("\n".join(lines))
    print(f"Wrote {output_path} ({WIDTH}x{HEIGHT}, array '{name}Data')")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input", type=Path, help="source image (PNG, JPG, ...)")
    parser.add_argument("output", type=Path, help="output header, e.g. image_one.h")
    parser.add_argument(
        "--name",
        default="imageOne",
        help="array name prefix; the array is called <name>Data (default: imageOne)",
    )
    args = parser.parse_args()
    convert_image(args.input, args.output, args.name)


if __name__ == "__main__":
    main()
