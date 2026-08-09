# SPDX-FileCopyrightText: 2026 Neptuwunium
#
# SPDX-License-Identifier: EUPL-1.2

import binascii
import colorsys
import xml.etree.ElementTree as ET
from markdown import Extension
from markdown.inlinepatterns import InlineProcessor

ACCESSIBILITY_LABLES = {
    'C#': 'C-Sharp',
}

COLOR_LABELS = {
    'Swift': (0xf0, 0x51, 0x38),
    "C#": (0x51, 0x2b, 0xd4),
    "C++": (0xf3, 0x4b, 0x7d),
    "C": (0x55, 0x55, 0x55),
    "Rust": (0xde, 0xa5, 0x84),
    "TypeScript": (0x31, 0x78, 0xc6),
    "Blender": (0xe8, 0x7d, 0x0d),
    "Godot": (0x35, 0x55, 0x70),
    "Python": (0xff, 0xd4, 0x3b),
    "Preact": (0x67, 0x3a, 0xb8),
}

LANG_BUBBLE_PATTERN = r'!Tier:\s(\d)'  # !Tier: 1


def srgb_to_linear(color_val):
    c = color_val / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def calculate_luminance(rgb):
    r = srgb_to_linear(rgb[0])
    g = srgb_to_linear(rgb[1])
    b = srgb_to_linear(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def get_contrast_ratio(rgb1, rgb2):
    lum1 = calculate_luminance(rgb1)
    lum2 = calculate_luminance(rgb2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def adjust_luminance(rgb, factor):
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    new_l = max(0.0, l * factor)
    new_r, new_g, new_b = colorsys.hls_to_rgb(h, new_l, s)
    return tuple(int(round(x * 255)) for x in (new_r, new_g, new_b))


def hash_color(text):
    print(f"warn: hashing {text}")
    hash_val = abs(binascii.crc32(text.encode('utf-8')))
    r = (hash_val & 0xFF0000) >> 16
    g = (hash_val & 0x00FF00) >> 8
    b = hash_val & 0x0000FF

    return r, g, b
