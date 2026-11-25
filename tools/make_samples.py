#!/usr/bin/env python3
"""Generate the neutral sample images/GIF in ../assets (run from anywhere)."""

import math
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 240, 280
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def gradient(top, bottom, label):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (WIDTH, y)], fill=color)
    draw.ellipse((60, 80, 180, 200), outline="white", width=4)
    draw.text((85, 134), label, fill="white")
    return image


def main():
    ASSETS.mkdir(exist_ok=True)
    gradient((20, 40, 120), (120, 40, 160), "SAMPLE IMAGE 1").save(ASSETS / "sample_image_1.png")
    gradient((10, 100, 90), (20, 30, 60), "SAMPLE IMAGE 2").save(ASSETS / "sample_image_2.png")

    frames = []
    for i in range(12):
        frame = Image.new("RGB", (WIDTH, HEIGHT), (15, 15, 30))
        draw = ImageDraw.Draw(frame)
        angle = 2 * math.pi * i / 12
        x = WIDTH / 2 + 70 * math.cos(angle)
        y = HEIGHT / 2 + 70 * math.sin(angle)
        draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=(255, 200, 60))
        draw.text((92, 136), "SAMPLE GIF", fill="white")
        frames.append(frame)
    frames[0].save(
        ASSETS / "sample.gif", save_all=True, append_images=frames[1:], duration=100, loop=0
    )


if __name__ == "__main__":
    main()
