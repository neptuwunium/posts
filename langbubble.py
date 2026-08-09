# SPDX-FileCopyrightText: 2026 Neptuwunium
#
# SPDX-License-Identifier: EUPL-1.2

from color import *
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

LANG_BUBBLE_PATTERN = r'!Languages:\s([\w+#.|]+)'  # !Languages: Lang1|Lang2|Lang3


def string_to_color_id(text: str) -> str:
    r, g, b = COLOR_LABELS[text] if text in COLOR_LABELS else hash_color(text)
    rD, gD, bD = adjust_luminance((r, g, b), 1.2 if calculate_luminance((r, g, b)) > 0.1 else 0.7)
    return f'#{r:02x}{g:02x}{b:02x}', f'#{rD:02x}{gD:02x}{bD:02x}', get_contrast_ratio((r, g, b), (255, 255, 255)) < 3


class LanguageBubbleProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        container = ET.Element('span')
        prefix = ET.SubElement(container, 'span')
        prefix.set('aria-label', 'Languages include')
        labels = ET.SubElement(container, 'span')
        for lang in m.group(1).split('|'):
            bubble = ET.SubElement(labels, 'span')
            bubble.set('class', 'language bubble')
            if lang in ACCESSIBILITY_LABLES:
                bubble.set('aria-label', ACCESSIBILITY_LABLES[lang])
            color, border, black_fg = string_to_color_id(lang)
            style = f'background-color: {color}; border-color: {border}'
            if black_fg:
                style += '; color: black'
            bubble.set('style', style)

            bubble.text = lang
        return container, m.start(0), m.end(0)


class LanguageBubbleExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(LanguageBubbleProcessor(LANG_BUBBLE_PATTERN, md), 'langbubble', 175)


def makeExtension(**kwargs):
    return LanguageBubbleExtension(**kwargs)
