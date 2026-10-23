#!/usr/bin/env python3
"""Check the deployed migration using real HTTP responses and verified TLS.

Run after publishing and configuring DNS: python3 scripts/verify-domain.py
No third-party dependencies. Exits nonzero while any migration check fails.
"""

from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET


CANONICAL = "https://haoyux.ai"
ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def request(url, method="HEAD"):
    # Default TLS validation remains enabled; never bypass certificate errors.
    opener = build_opener(NoRedirect())
    req = Request(url, method=method, headers={"User-Agent": "haoyux-domain-check/1.0"})
    try:
        response = opener.open(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        body = response.read().decode("utf-8") if method == "GET" else ""
        return response.status, response.headers, body


def asset_paths():
    page = Page((ROOT / "index.html").read_text())
    paths = set()
    for tag, attrs in page.tags:
        value = attrs.get("src")
        if tag == "link" and attrs.get("rel") in {
            "stylesheet", "icon", "apple-touch-icon", "manifest"
        }:
            value = attrs.get("href")
        if value and not urlsplit(value).netloc and not urlsplit(value).scheme:
            paths.add(urlsplit(urljoin(CANONICAL + "/", value)).path)
    manifest = json.loads((ROOT / "themes/mit/assets/favicon/manifest.webmanifest").read_text())
    paths.update(icon["src"] for icon in manifest["icons"])
    return paths


def check_route(item):
    origin, path, expected_status = item
    url = origin + path
    destination = CANONICAL + path
    try:
        status, headers, _ = request(url)
        if origin == CANONICAL:
            if status != expected_status:
                raise ValueError(f"expected {expected_status}, got {status}")
            return True, f"{url} -> {status}"

        if status != 301:
            raise ValueError(f"expected 301, got {status}")
        location = urljoin(url, headers.get("Location", ""))
        # For HTTP, allow an HTTPS upgrade before the host redirect, or vice versa.
        # HTTPS aliases must redirect directly to the exact canonical URL.
        if origin.startswith("http://"):
            for _ in range(3):
                if location == destination:
                    break
                parsed = urlsplit(location)
                wanted = urlsplit(destination)
                if (parsed.path, parsed.query) != (wanted.path, wanted.query):
                    raise ValueError(f"path/query changed: {location}")
                if parsed.hostname not in {"haoyu-x.github.io", "www.haoyux.ai", "haoyux.ai"}:
                    raise ValueError(f"unexpected redirect host: {location}")
                status, headers, _ = request(location)
                if status != 301:
                    raise ValueError(f"expected another 301, got {status} at {location}")
                location = urljoin(location, headers.get("Location", ""))
        if location != destination:
            raise ValueError(f"expected Location {destination}, got {location}")
        return True, f"{url} -> 301 -> {destination}"
    except (OSError, URLError, ValueError) as error:
        return False, f"{url}: {error}"


def check_metadata():
    status, _, html = request(CANONICAL + "/", "GET")
    if status != 200:
        raise ValueError(f"homepage returned {status}")
    page = Page(html)
    canonicals = [a.get("href") for t, a in page.tags if t == "link" and a.get("rel") == "canonical"]
    if canonicals != [CANONICAL + "/"]:
        raise ValueError(f"incorrect canonical tags: {canonicals}")
    metadata = {a.get("property", a.get("name")): a.get("content") for t, a in page.tags if t == "meta"}
    for name, value in {
        "og:url": CANONICAL + "/",
        "og:image": CANONICAL + "/images/headshot.jpeg",
        "twitter:image": CANONICAL + "/images/headshot.jpeg",
    }.items():
        if metadata.get(name) != value:
            raise ValueError(f"incorrect {name}: {metadata.get(name)}")
    status, _, sitemap = request(CANONICAL + "/sitemap.xml", "GET")
    if status != 200:
        raise ValueError(f"sitemap returned {status}")
    locations = [node.text for node in ET.fromstring(sitemap).findall("{*}url/{*}loc")]
    if CANONICAL + "/" not in locations or any(not url.startswith(CANONICAL + "/") for url in locations):
        raise ValueError(f"incorrect sitemap URLs: {locations}")
    status, _, robots = request(CANONICAL + "/robots.txt", "GET")
    if status != 200 or f"Sitemap: {CANONICAL}/sitemap.xml" not in robots or "Disallow: /" in robots:
        raise ValueError("robots.txt is missing, blocks crawling, or has the wrong sitemap")


def main():
    paths = {
        "/": 200,
        "/?ref=test&value=a%2Fb%20c&ref=second": 200,
        "/index.html?ref=test": 200,
        "/xxx": 404,
        "/projects/demo?ref=test": 404,
        "/simple-mobile/?ref=test": 200,
        "/simple-mobile/assets/unbox.gif": 200,
        "/simple-mobile/assets/simple-mobile-teaser.png": 200,
        "/robots.txt": 200,
        "/sitemap.xml": 200,
        **{path: 200 for path in asset_paths()},
    }
    aliases = ["https://haoyu-x.github.io", "https://www.haoyux.ai"]
    checks = [(origin, path, status) for origin in [CANONICAL, *aliases] for path, status in paths.items()]
    checks += [(origin, path, paths[path]) for origin in [
        "http://haoyu-x.github.io", "http://haoyux.ai", "http://www.haoyux.ai"
    ] for path in ["/", "/projects/demo?ref=test", "/simple-mobile/?ref=test"]]
    failures = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for ok, detail in pool.map(check_route, checks):
            print(f"{'PASS' if ok else 'FAIL'} {detail}")
            failures += not ok
    try:
        check_metadata()
        print("PASS deployed canonical, social metadata, sitemap, and robots.txt")
    except (OSError, URLError, ValueError, ET.ParseError) as error:
        print(f"FAIL deployed metadata: {error}")
        failures += 1
    print(f"\n{len(checks) + 1} checks; {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
