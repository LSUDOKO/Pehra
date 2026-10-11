"""Catch missing deployment assets and stale generated website templates."""

import base64
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[1]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AssetLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "img", "source"):
            self.urls.add(attrs.get("src", ""))
            for candidate in attrs.get("srcset", "").split(","):
                if candidate.strip():
                    self.urls.add(candidate.strip().split()[0])
        if tag == "link":
            self.urls.add(attrs.get("href", ""))


def test_home_asset_graph_is_public_and_has_correct_content_types(monkeypatch):
    app = load("functions/public_web/app.py", "web_asset_app")

    def no_database():
        raise AssertionError("Public pages and assets must not require database access")

    monkeypatch.setattr(app.repo, "table", no_database)

    def get(path):
        return app.handler({"rawPath": path, "requestContext": {"http": {"method": "GET"}}}, None)

    home = get("/")
    assert home["statusCode"] == 200
    parser = AssetLinks()
    parser.feed(home["body"])
    local = {urlsplit(url).path for url in parser.urls if url.startswith("/") and not url.startswith("/media/")}
    assert "/assets/home.css" in local and "/assets/home.js" in local
    for path in local | {"/site.css", "/audit", "/model-card"}:
        result = get(path)
        assert result["statusCode"] == 200, path
        assert result["headers"]["x-content-type-options"] == "nosniff"
        if path.endswith(".webp"):
            assert result["headers"]["content-type"] == "image/webp"
            assert result["isBase64Encoded"]
            data = base64.b64decode(result["body"])
            assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
        elif path.endswith(".js"):
            assert result["headers"]["content-type"].startswith("text/javascript")
        elif path.endswith(".css"):
            assert result["headers"]["content-type"].startswith("text/css")
    assert get("/assets/../app.py")["statusCode"] == 404
    assert get("/assets/not-public.js")["statusCode"] == 404
    assert get("/img/manifest.json")["statusCode"] == 404


def test_generated_pages_match_their_sources():
    build = load("scripts/build_pages.py", "web_page_builder")
    summary = json.loads((ROOT / "docs/results/audit_summary.json").read_text())
    home = build.home_page(summary)
    assert "{{" not in home
    assert home == (ROOT / "web/home/index.html").read_text()
    assert build.audit_page(summary) == (ROOT / "web/audit/index.html").read_text()
    assert build.model_card_page((ROOT / "docs/MODEL_CARD.md").read_text()) == (
        ROOT / "web/model_card/index.html").read_text()


def test_home_numbers_stay_driven_by_audit_data():
    build = load("scripts/build_pages.py", "web_page_builder_numbers")
    summary = json.loads((ROOT / "docs/results/audit_summary.json").read_text())
    summary["total"]["invisible_days_shade"] = 123456
    summary["total"]["heavy_rain_days"] = 321
    home = build.home_page(summary)
    assert 'data-count="123456">123,456</strong>' in home
    assert f"in {len(summary['districts'])} cities" in home
