"""Check the published artifact's crawlability and agreement with the source dataset."""
from __future__ import annotations

import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_site import build, render_page
from catalog import MODELS, REMOVED, SITE_URL, load_json, rank


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.elements = []
        self.text = []
        self.structured_data = []
        self.in_schema = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_schema = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_schema = False

    def handle_data(self, data):
        (self.structured_data if self.in_schema else self.text).append(data)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        build(cls.root)
        cls.models, cls.removed = load_json(MODELS), load_json(REMOVED)
        cls.html = (cls.root / "index.html").read_text(encoding="utf-8")
        cls.page = Page(cls.html)

    def test_search_metadata_and_canonical(self):
        meta = {attrs.get("name", attrs.get("property")): attrs.get("content")
                for tag, attrs in self.page.elements if tag == "meta"}
        self.assertEqual(sum(tag == "h1" for tag, _ in self.page.elements), 1)
        self.assertEqual(sum(tag == "title" for tag, _ in self.page.elements), 1)
        self.assertIn(("html", {"lang": "en"}), self.page.elements)
        self.assertTrue(meta.get("description"))
        self.assertIn("width=device-width", meta["viewport"])
        self.assertNotIn("noindex", meta["robots"])
        canonical = [a["href"] for tag, a in self.page.elements if tag == "link" and a.get("rel") == "canonical"]
        self.assertEqual(canonical, [SITE_URL])
        self.assertEqual(meta["og:url"], SITE_URL)
        self.assertEqual(meta["og:description"], meta["description"])

    def test_catalog_is_in_html_without_javascript(self):
        visible_text = " ".join(self.page.text)
        for model in self.models + self.removed:
            self.assertIn(model["id"], visible_text)
            self.assertIn(model["name"], visible_text)
        scripts = [a for tag, a in self.page.elements if tag == "script"]
        self.assertEqual(scripts, [{"type": "application/ld+json"}])
        active = rank([m for m in self.models if m["category"] == "llm" and m["endpoint_status"] == "Free Endpoint"])
        positions = [visible_text.index(m["id"]) for m in active]
        self.assertEqual(positions, sorted(positions))

    def test_local_links_resolve_under_project_path(self):
        ids = [a["id"] for _, a in self.page.elements if "id" in a]
        self.assertEqual(len(ids), len(set(ids)), "duplicate HTML IDs")
        for _, attrs in self.page.elements:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                url = urlsplit(urljoin(SITE_URL, attrs[key]))
                if url.netloc != urlsplit(SITE_URL).netloc:
                    continue
                base_path = urlsplit(SITE_URL).path
                self.assertTrue(url.path.startswith(base_path), attrs[key])
                relative = url.path[len(base_path):] or "index.html"
                self.assertTrue((self.root / relative).is_file(), attrs[key])
                if url.fragment and relative == "index.html":
                    self.assertIn(url.fragment, ids)

    def test_structured_data_matches_visible_downloads(self):
        schema = json.loads("".join(self.page.structured_data))
        self.assertEqual(schema["@type"], "Dataset")
        self.assertEqual(schema["url"], SITE_URL)
        visible_text = " ".join(self.page.text)
        for field in ("name", "description"):
            self.assertIn(schema[field], visible_text)
        self.assertIn(schema["creator"]["name"], visible_text)
        self.assertIn(schema["license"], self.html)
        for download in schema["distribution"]:
            self.assertIn(download["contentUrl"].removeprefix(SITE_URL), self.html)
            self.assertTrue((self.root / download["contentUrl"].removeprefix(SITE_URL)).is_file())
        self.assertEqual(json.loads((self.root / "data/models.json").read_text(encoding="utf-8")), self.models)
        csv_rows = list(csv.DictReader(io.StringIO((self.root / "data/models.csv").read_text(encoding="utf-8"))))
        self.assertEqual([m["id"] for m in csv_rows], [m["id"] for m in self.models])

    def test_sitemap_and_missing_page(self):
        xml = ElementTree.parse(self.root / "sitemap.xml")
        locations = [node.text for node in xml.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(locations, [SITE_URL])
        error = Page((self.root / "404.html").read_text(encoding="utf-8"))
        self.assertIn(("meta", {"name": "robots", "content": "noindex"}), error.elements)

    def test_model_text_is_escaped(self):
        models = copy.deepcopy(self.models)
        models[0]["name"] = '<script>alert("test")</script> & Model'
        html = render_page(models, [])
        self.assertNotIn('<script>alert("test")', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn(models[0]["name"], " ".join(Page(html).text))


if __name__ == "__main__":
    unittest.main()
