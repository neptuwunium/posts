# SPDX-FileCopyrightText: 2026 Neptuwunium
#
# SPDX-License-Identifier: EUPL-1.2

import xml.etree.ElementTree as ET

from markdown import Extension
from markdown.inlinepatterns import InlineProcessor

ACCESSIBILITY_LABLES = {
    "C#": "C-Sharp",
}

LANG_BUBBLE_PATTERN = r'!Languages:\s([\w+#.]+)'  # !Languages: Lang1|Lang2|Lang3


class LanguageBubbleProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        container = ET.Element('span')
        prefix = ET.SubElement(container, 'span')
        prefix.set('aria-label', 'Languages include')
        for lang in m.group(1).split('|'):
            bubble = ET.SubElement(container, 'span')
            bubble.set('class', 'language-bubble')
            if lang in ACCESSIBILITY_LABLES:
                bubble.set('aria-label', ACCESSIBILITY_LABLES[lang])
        return container, m.start(0), m.end(0)


class LanguageBubbleExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(LanguageBubbleProcessor(LANG_BUBBLE_PATTERN, md), 'langbubble', 175)


def makeExtension(**kwargs):
    return LanguageBubbleExtension(**kwargs)
