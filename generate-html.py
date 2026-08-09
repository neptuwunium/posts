#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "markdown",
#   "python-markdown-math",
#   "lxml",
#   "beautifulsoup4",
#   "libsass"
# ]
# ///
#
# SPDX-FileCopyrightText: 2026 Neptuwunium
#
# SPDX-License-Identifier: EUPL-1.2

from glob import glob
from io import StringIO
from json import dumps as json_serialize
from os.path import basename, splitext, exists

from lxml import etree
from lxml.builder import ElementMaker, E as elem
from lxml.etree import CDATA, tostring as xml_serialize
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

from markdown import Markdown
from markdown.extensions.codehilite import CodeHiliteExtension

from email.utils import format_datetime
from datetime import datetime, timezone

from langbubble import LanguageBubbleExtension
from tierbubble import TierBubbleExtension

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()


def strip_html(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


BLOG_NAME = "np93's blog"
BLOG_ROOT = "https://neptuwunium.space/posts"
BLOG_WHOAMI = "Neptuwunium"
BLOG_DESCRIPTION = "just a collection of thoughts~"
BLOG_ID = "tag:neptuwunium.space,posts:root"
BLOG_POST_ID = "tag:neptuwunium.space,posts:"

atom_feed = [
    elem.title(BLOG_NAME),
    elem.link(href=BLOG_ROOT),
    elem.link(rel="self", href=f'{BLOG_ROOT}/feed.atom'),
    elem.updated(datetime.now(timezone.utc).isoformat()),
    elem.author(elem.name(BLOG_WHOAMI)),
    elem.generator("pumpkin"),
    elem.id(BLOG_ID)
]

ATOM_NS = ElementMaker(namespace="http://www.w3.org/2005/Atom", nsmap={'atom': "http://www.w3.org/2005/Atom"})

rss_feed = [
    elem.title(BLOG_NAME),
    elem.link(BLOG_ROOT),
    ATOM_NS.link(rel="self", href=f'{BLOG_ROOT}/feed.rss'),
    elem.description(BLOG_DESCRIPTION),
    elem.lastBuildDate(format_datetime(datetime.now(timezone.utc))),
    elem.generator("pumpkin"),
    elem.language("en")
]


json_feed = []
json_root = {
    "version": "https://jsonfeed.org/version/1.1",
    "title": BLOG_NAME,
    "description": BLOG_DESCRIPTION,
    "home_page_url": BLOG_ROOT,
    "feed_url": f"{BLOG_ROOT}/feed.json",
    "authors": [{"name": BLOG_WHOAMI}],
    "generator": "pumpkin",
    "language": "en",
    "items": json_feed
}

with open('post.html', 'r', encoding='utf8') as post_template:
    POST_TEMPLATE = post_template.read().strip().replace('\r\n', '\n') + '\n'

with open('index.html', 'r', encoding='utf8') as index_template:
    INDEX_TEMPLATE = index_template.read().strip().replace('\r\n', '\n') + '\n'

with open('docs/index.html', 'w', encoding='utf8') as index:
    index_lines = ''
    for md_file in reversed(sorted(glob('markdown/*.md'))):
        with open(md_file, 'r', encoding='utf8') as md:
            markdown = Markdown(extensions=['meta', 'tables', 'smarty', 'fenced_code', 'codehilite', 'footnotes', 'toc', 'admonition', 'mdx_math', 'langbubble', 'tierbubble'])
            md_data = md.read().strip()
            text = markdown.convert(md_data)
            meta = markdown.Meta
            name = splitext(basename(md_file))[0]

            if not 'title' in meta:
                continue

            if 'draft' in meta:
                continue

            date = meta['date'] if 'date' in meta else datetime.now(timezone.utc).strftime('%Y-%m-%d %I:%M %p')
            upd_date = meta['updated'] if 'updated' in meta else date
            pub_date_t = datetime.strptime(date[0], '%Y-%m-%d %I:%M %p').astimezone(timezone.utc)
            upd_date_t = datetime.strptime(upd_date[0], '%Y-%m-%d %I:%M %p').astimezone(timezone.utc)
            pub_date_iso = pub_date_t.isoformat()
            upd_date_iso = upd_date_t.isoformat()
            title = meta['title'][0]
            short = meta['short'][0]
            title_safe = strip_html(title)
            short_safe = strip_html(short)

            folder = 'private/'
            rel = '../'
            if 'private' not in meta:
                folder = ''
                rel = ''
                if 'unlist' in meta:
                    index_lines += f'<!-- unlisted: <li><a href="{name}.html">{title}</a></li> -->\n'
                else:
                    index_lines += f'<li><a href="{name}.html">{title}</a></li>\n'
                    md_data_nohead = md_data.split('---', 2)[-1].strip()
                    feed_data = CDATA(md_data_nohead)

                    atom_feed.append(
                        elem.entry(
                            elem.title(title_safe),
                            elem.link(href=f"{BLOG_ROOT}/{name}.html"),
                            elem.updated(upd_date_iso),
                            elem.published(pub_date_iso),
                            elem.summary(short_safe),
                            elem.id(BLOG_POST_ID + name),
                            elem.content(feed_data, type="text/markdown")
                        )
                    )

                    rss_feed.append(
                        elem.item(
                            elem.title(title_safe),
                            elem.link(f"{BLOG_ROOT}/{name}.html"),
                            elem.pubDate(format_datetime(pub_date_t)),
                            elem.description(short_safe),
                            elem.author(BLOG_WHOAMI),
                            elem.guid(BLOG_POST_ID + name),
                            ATOM_NS.content(feed_data, type="text/markdown")
                        )
                    )

                    json_feed.append({
                        "title": title_safe,
                        "url": f"{BLOG_ROOT}/{name}.html",
                        "id": BLOG_POST_ID + name,
                        "summary": short_safe,
                        "date_published": pub_date_iso,
                        "date_modified": upd_date_iso,
                        "content_text": md_data_nohead,
                    })

            headers = ''
            if 'headers' in meta:
                for header_name in meta['headers']:
                    if not exists(f'headers/{header_name}.html'): continue
                    with open(f'headers/{header_name}.html', 'r', encoding='utf8') as header:
                        headers = f'{headers}{header.read()}'
                if len(headers) > 0:
                    header = '\n' + headers

            print(name)
            with open(f'docs/{folder}{name}.html', 'w', encoding='utf8') as html:
                html.write(POST_TEMPLATE.format(title=title, short=short, title_safe=title_safe, short_safe=short_safe, url=name, time=upd_date[0], isotime=upd_date_iso, pub_time=date[0], pub_isotime=pub_date_iso, body=text, rel=rel, headers=headers))
    index.write(INDEX_TEMPLATE.format(body=index_lines))

atom = elem.feed(*atom_feed, xmlns="http://www.w3.org/2005/Atom")
with open('docs/feed.atom', 'wb') as atom_file:
    atom_file.write(xml_serialize(atom, pretty_print=True, xml_declaration=True, encoding='utf-8'))

rss = etree.Element("rss", nsmap={'atom': "http://www.w3.org/2005/Atom"})
rss.set("version", "2.0")
rss.append(elem.channel(*rss_feed))
with open('docs/feed.rss', 'wb') as rss_file:
    rss_file.write(xml_serialize(rss, pretty_print=True, xml_declaration=True, encoding='utf-8'))

with open('docs/feed.json', 'w') as json_file:
    json_file.write(json_serialize(json_root, indent=2)+'\n')
