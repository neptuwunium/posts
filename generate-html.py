from markdown import Markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from glob import glob
from codecs import open as cope
from datetime import datetime, timezone
from os.path import basename, splitext
from json import dumps as json_serialize
from lxml.etree import CDATA, tostring as xml_serialize
from lxml import etree
from lxml.builder import ElementMaker, E as elem
from email.utils import format_datetime

BLOG_NAME = "ada's blog"
BLOG_ROOT = "https://chronovore.dev/posts"
BLOG_WHOAMI = "Ada"
BLOG_DESCRIPTION = "just a collection of thoughts~"
BLOG_ID = "tag:chronovore.dev,posts:root"
BLOG_POST_ID = "tag:chronovore.dev,posts:"

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

with cope('post.html', 'r', 'utf8') as post_template:
    POST_TEMPLATE = post_template.read().strip().replace('\r\n', '\n') + '\n'

with cope('index.html', 'r', 'utf8') as index_template:
    INDEX_TEMPLATE = index_template.read().strip().replace('\r\n', '\n') + '\n'

with cope('docs/index.html', 'w', 'utf8') as index:
    index_lines = ''
    for md_file in reversed(sorted(glob('markdown/*.md'))):
        with cope(md_file, 'r', 'utf8') as md:
            markdown = Markdown(extensions=['meta', 'tables', 'smarty', 'fenced_code', 'codehilite', 'footnotes', 'toc', 'admonition'])
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

            folder = 'private/'
            rel = '../'
            if 'private' not in meta:
                index_lines += f'<li><a href="{name}.html">{meta['title'][0]}</a></li>\n'
                folder = ''
                rel = ''
                md_data_nohead = md_data.split('---', 2)[-1].strip()
                feed_data = CDATA(md_data_nohead)

                atom_feed.append(
                    elem.entry(
                        elem.title(meta['title'][0]),
                        elem.link(href=f"{BLOG_ROOT}/{name}.html"),
                        elem.updated(upd_date_iso),
                        elem.published(pub_date_iso),
                        elem.summary(meta['short'][0]),
                        elem.id(BLOG_POST_ID + name),
                        elem.content(feed_data, type="text/markdown")
                    )
                )

                rss_feed.append(
                    elem.item(
                        elem.title(meta['title'][0]),
                        elem.link(f"{BLOG_ROOT}/{name}.html"),
                        elem.pubDate(format_datetime(pub_date_t)),
                        elem.description(meta['short'][0]),
                        elem.author(BLOG_WHOAMI),
                        elem.guid(BLOG_POST_ID + name),
                        ATOM_NS.content(feed_data, type="text/markdown")
                    )
                )

                json_feed.append({
                    "title": meta['title'][0],
                    "url": f"{BLOG_ROOT}/{name}.html",
                    "id": BLOG_POST_ID + name,
                    "summary": meta['short'][0],
                    "date_published": pub_date_iso,
                    "date_modified": upd_date_iso,
                    "content_text": md_data_nohead,
                })

            print(name)
            with cope(f'docs/{folder}{name}.html', 'w', 'utf8') as html:
                html.write(POST_TEMPLATE.format(title=meta['title'][0], short=meta['short'][0], url=name, time=upd_date[0], isotime=upd_date_iso, pub_time=date[0], pub_isotime=pub_date_iso, body=text, rel=rel))
    index.write(INDEX_TEMPLATE.format(body=index_lines))

atom = elem.feed(*atom_feed, xmlns="http://www.w3.org/2005/Atom")
with cope('docs/feed.atom', 'wb') as atom_file:
    atom_file.write(xml_serialize(atom, pretty_print=True, xml_declaration=True, encoding='utf-8'))

rss = etree.Element("rss", nsmap={'atom': "http://www.w3.org/2005/Atom"})
rss.set("version", "2.0")
rss.append(elem.channel(*rss_feed))
with cope('docs/feed.rss', 'wb') as rss_file:
    rss_file.write(xml_serialize(rss, pretty_print=True, xml_declaration=True, encoding='utf-8'))

with cope('docs/feed.json', 'w') as json_file:
    json_file.write(json_serialize(json_root, indent=2)+'\n')
