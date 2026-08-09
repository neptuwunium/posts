# SPDX-FileCopyrightText: 2026 Neptuwunium
#
# SPDX-License-Identifier: EUPL-1.2

from color import *
import xml.etree.ElementTree as ET
from markdown import Extension
from markdown.inlinepatterns import InlineProcessor

TIERS = [
    (0x1e, 0x7f, 0xb7),
    (0xe3, 0xe3, 0xe3),
    (0x36, 0xa9, 0x0c),
    (0x83, 0x2e, 0xf7),
    (0xff, 0xb1, 0x55),
    (0xc5, 0x35, 0x35),
]

NAMES = [
    ("Ice", "Preparing to move to On Ice",),
    ("Minimal", None),
    ("Low", None),
    ("Normal", None),
    ("High", None),
    ("EX", "Extremely High")
]

TIER_BUBBLE_PATTERN = r'!Tier\s(\d)'  # !Tier: 1


def tier_to_color_id(tier: int) -> str:
    r, g, b = TIERS[tier]
    rD, gD, bD = adjust_luminance((r, g, b), 1.2 if calculate_luminance((r, g, b)) > 0.1 else 0.7)
    return f'#{r:02x}{g:02x}{b:02x}', f'#{rD:02x}{gD:02x}{bD:02x}', get_contrast_ratio((r, g, b), (255, 255, 255)) < 3


class TierBubbleProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        container = ET.Element('span')
        prefix = ET.SubElement(container, 'span')
        prefix.set('aria-label', 'Interest level is ')
        bubble = ET.SubElement(container, 'span')
        bubble.set('class', 'tier bubble')
        tier = int(m.group(1), 10)
        color, border, black_fg = tier_to_color_id(tier)
        style = f'background-color: {color}; border-color: {border}'
        if black_fg:
            style += '; color: black'
        bubble.set('style', style)
        name, alt = NAMES[tier]
        if alt:
            bubble.set('aria-text', alt)
        bubble.text = name
        return container, m.start(0), m.end(0)


class TierBubbleExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(TierBubbleProcessor(TIER_BUBBLE_PATTERN, md), 'tierbubble', 175)


def makeExtension(**kwargs):
    return TierBubbleExtension(**kwargs)
