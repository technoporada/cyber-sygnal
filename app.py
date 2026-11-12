#!/usr/bin/env python3
"""A small, local-only RSS reader for cybersecurity news."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import threading
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET


MAX_FEED_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT = 10
SOURCES = (
    {
        "name": "Niebezpiecznik",
        "url": "https://feeds.feedburner.com/niebezpiecznik/",
        "host": "feeds.feedburner.com",
    },
    {
        "name": "Sekurak",
        "url": "https://sekurak.pl/feed/",
        "host": "sekurak.pl",
    },
)

DATA_DIR = Path(__file__).parent / "data"
STORAGE_FILE = DATA_DIR / "items.json"

CATEGORY_KEYWORDS = {
    "Phishing": (
        "phishing",
        "phish",
        "wyłudz",
        "oszust",
        "podszyw",
        "fałszyw",
        "scam",
    ),
    "Wycieki": (
        "wyciek",
        "leak",
        "expos",
        "dane osob",
        "hasła",
        "password dump",
    ),
    "Podatności": (
        "cve-",
        "podatn",
        "vulnerab",
        "exploit",
        "zero-day",
        "zero day",
        "0day",
    ),
    "Ataki": (
        "ransomware",
        "atak",
        "malware",
        "botnet",
        "haker",
        "hack",
        "ddos",
    ),
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    names = tuple(name.lower() for name in names)
    for child in element:
        if _local_name(child.tag) in names:
            if child.attrib.get("href"):
                return child.attrib["href"].strip()
            return "".join(child.itertext()).strip()
    return ""


def classify(title: str, summary: str) -> str:
    text = f"{title} {summary}".casefold()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Inne"


def _date_order(value: str) -> float:
    if not value:
        return 0.0
    try:
        published = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            published = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    try:
        return published.timestamp()
    except (OverflowError, OSError):
        return 0.0


def _load_stored_items() -> list[dict[str, str]]:
    """Wczytaj wcześniej zapisane wpisy z pliku JSON."""
    try:
        if STORAGE_FILE.exists():
            data = json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _save_stored_items(items: list[dict[str, str]]) -> None:
    """Zapisz wpisy do pliku JSON (lokalna baza wycieków i innych wpisów)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_feed(data: bytes, source: str) -> list[dict[str, str]]:
    upper_data = data.upper()
    if b"<!DOCTYPE" in upper_data or b"<!ENTITY" in upper_data:
        raise ValueError("Feed zawiera niedozwoloną deklarację XML.")

    root = ET.fromstring(data)
    entries = [element for element in root.iter() if _local_name(element.tag) in {"item", "entry"}]
    items: list[dict[str, str]] = []
    seen: set[str] = set()

    for entry in entries:
        title = _plain_text(_child_text(entry, "title"))
        raw_link = _child_text(entry, "link")
        parsed_link = urlsplit(raw_link)
        if (
            parsed_link.scheme != "https"
            or not parsed_link.hostname
            or parsed_link.username
            or parsed_link.password
        ):
            continue
        link = parsed_link.geturl()
        summary = _plain_text(_child_text(entry, "description", "summary", "encoded"))
        published = _plain_text(_child_text(entry, "pubdate", "published", "updated", "date"))
        identifier = _child_text(entry, "guid", "id") or link

        if not title or identifier in seen:
            continue
        seen.add(identifier)
        items.append(
            {
                "title": title,
                "link": link,
                "summary": summary[:600],
                "published": published,
                "source": source,
                "category": classify(title, summary),
            }
        )
    return items


class _AllowedRedirects(HTTPRedirectHandler):
    def __init__(self, allowed_host: str) -> None:
        super().__init__()
        self.allowed_host = allowed_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destination = urlsplit(urljoin(req.full_url, newurl))
        if destination.scheme != "https" or destination.hostname != self.allowed_host:
            raise URLError("Feed przekierował poza dozwolony adres HTTPS.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_source(source: dict[str, str]) -> list[dict[str, str]]:
    opener = build_opener(_AllowedRedirects(source["host"]))
    request = Request(
        source["url"],
        headers={
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            "User-Agent": "cyber-sygnal/0.1 (local RSS reader)",
        },
    )
    with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
        final_url = urlsplit(response.geturl())
        if final_url.scheme != "https" or final_url.hostname != source["host"]:
            raise URLError("Adres źródła RSS różni się od dozwolonego adresu.")
        data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise ValueError("Feed jest większy niż dozwolone 2 MB.")
    return parse_feed(data, source["name"])


class FeedStore:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.refresh_lock = threading.Lock()
        self.items: list[dict[str, str]] = _load_stored_items()
        self.errors: list[dict[str, str]] = []
        self.updated_at: str | None = None

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            return {
                "items": list(self.items),
                "errors": list(self.errors),
                "updated_at": self.updated_at,
                "sources": [source["name"] for source in SOURCES],
            }

    def refresh(self) -> dict[str, object]:
        with self.refresh_lock:
            fetched: list[dict[str, str]] = []
            errors: list[dict[str, str]] = []
            for source in SOURCES:
                try:
                    fetched.extend(fetch_source(source))
                except (ET.ParseError, OSError, TimeoutError, ValueError, URLError) as exc:
                    errors.append({"source": source["name"], "message": str(exc)})

            # Scal nowe wpisy z zapisowanymi lokalnie (bez duplikatów po linku).
            # Dzięki temu wycieki i inne ważne wpisy nie giną po kolejnym odświeżeniu.
            merged: dict[str, dict[str, str]] = {}
            for item in self.items:
                merged[item["link"]] = item
            for item in fetched:
                merged.setdefault(item["link"], item)

            ordered_items = sorted(
                merged.values(),
                key=lambda item: _date_order(item["published"]),
                reverse=True,
            )
            with self.lock:
                self.items = ordered_items
                self.errors = errors
                self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            _save_stored_items(ordered_items)
            return self.snapshot()


STORE = FeedStore()
WEB_ROOT = Path(__file__).parent / "static"


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "CyberSygnal/0.1"

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
            "base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, value: dict[str, object]) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", body)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            try:
                body = (WEB_ROOT / "index.html").read_bytes()
            except OSError:
                self._send_json(500, {"error": "Nie udało się wczytać strony."})
                return
            self._send(200, "text/html; charset=utf-8", body)
        elif path == "/app.js":
            try:
                body = (WEB_ROOT / "app.js").read_bytes()
            except OSError:
                self._send_json(500, {"error": "Nie udało się wczytać skryptu."})
                return
            self._send(200, "text/javascript; charset=utf-8", body)
        elif path == "/style.css":
            try:
                body = (WEB_ROOT / "style.css").read_bytes()
            except OSError:
                self._send_json(500, {"error": "Nie udało się wczytać stylów."})
                return
            self._send(200, "text/css; charset=utf-8", body)
        elif path == "/api/items":
            self._send_json(200, STORE.snapshot())
        elif path == "/api/leaks":
            snapshot = STORE.snapshot()
            leaks = [item for item in snapshot["items"] if item.get("category") == "Wycieki"]
            self._send_json(200, {"items": leaks, "updated_at": snapshot["updated_at"]})
        else:
            self._send_json(404, {"error": "Nie znaleziono strony."})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/refresh":
            self._send_json(404, {"error": "Nie znaleziono strony."})
            return
        self._send_json(200, STORE.refresh())

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Uruchom lokalny Cyber Sygnał.")
    parser.add_argument("--port", type=int, default=8777)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), RequestHandler)
    print(f"Cyber Sygnał działa lokalnie: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZamykanie serwera.")
    finally:
        server.server_close()


def _background_refresh() -> None:
    """Pobierz kanały RSS w tle tuż po starcie serwera."""
    try:
        STORE.refresh()
    except Exception:  # pragma: no cover - nie blokujemy startu serwera
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uruchom lokalny Cyber Sygnał.")
    parser.add_argument("--port", type=int, default=8777)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), RequestHandler)
    threading.Thread(target=_background_refresh, daemon=True).start()
    print(f"Cyber Sygnał działa lokalnie: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZamykanie serwera.")
    finally:
        server.server_close()
