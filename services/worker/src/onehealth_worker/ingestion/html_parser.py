from __future__ import annotations

import re
from datetime import datetime
from email.message import Message
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .models import FetchedDocument, ParsedDocument
from .html_text import render_dom_text

SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
DATE_RE = re.compile(
    r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(20\d{2})\b",
    flags=re.IGNORECASE,
)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _find_published_at(soup: BeautifulSoup, visible_text: str) -> datetime | None:
    for attr in (
        {"property": "article:published_time"},
        {"name": "date"},
        {"name": "article:published_time"},
        {"itemprop": "datePublished"},
    ):
        node = soup.find("meta", attrs=attr)
        if node and node.get("content"):
            parsed = _parse_iso_datetime(node.get("content"))
            if parsed:
                return parsed

    time_node = soup.find("time")
    if time_node:
        parsed = _parse_iso_datetime(time_node.get("datetime"))
        if parsed:
            return parsed

    match = DATE_RE.search(visible_text)
    if match:
        day = int(match.group(1))
        month = SPANISH_MONTHS[match.group(2).lower()]
        year = int(match.group(3))
        try:
            return datetime(year, month, day, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
        except ValueError:
            return None
    return None


def _extract_title(soup: BeautifulSoup) -> str | None:
    # Prefer explicit page metadata: government sites may expose a site-wide H1
    # (for example, "Presidencia de la Nación") before the article headline.
    for selector in (
        ('meta[property="og:title"]', "content"),
        ('meta[name="twitter:title"]', "content"),
    ):
        node = soup.select_one(selector[0])
        if node and node.get(selector[1]):
            title = str(node.get(selector[1])).strip()
            if title:
                return title

    # Then prefer headings scoped to the actual content container.
    for selector in ("article h1", "main h1"):
        node = soup.select_one(selector)
        if node:
            title = " ".join(node.stripped_strings).strip()
            if title:
                return title

    # Generic fallback for sites without article/main semantics.
    h1 = soup.find("h1")
    if h1:
        title = " ".join(h1.stripped_strings).strip()
        if title:
            return title

    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if title.endswith(" | Argentina.gob.ar"):
            title = title.removesuffix(" | Argentina.gob.ar").strip()
        return title
    return None


def parse_html_document(fetched: FetchedDocument) -> ParsedDocument:
    content_type = Message()
    content_type["content-type"] = fetched.mime_type or ""
    declared_encoding = content_type.get_content_charset()
    soup = BeautifulSoup(fetched.body, "html.parser", from_encoding=declared_encoding)

    for tag in soup(["script", "style", "noscript", "svg", "nav", "header", "footer", "aside"]):
        tag.decompose()

    title = _extract_title(soup)
    language = soup.html.get("lang") if soup.html else None

    main = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = []
    for node in main.find_all(["p", "li"]):
        # A containing list item already serializes its nested paragraphs/items.
        if any(parent.name in {"p", "li"} for parent in node.parents if parent is not main):
            continue
        text = render_dom_text(node)
        if text:
            paragraphs.append(text)

    if not paragraphs:
        fallback = render_dom_text(main)
        paragraphs = [fallback] if fallback else []

    # Stable de-duplication while preserving order.
    seen: set[str] = set()
    unique_paragraphs: list[str] = []
    for paragraph in paragraphs:
        if paragraph not in seen:
            seen.add(paragraph)
            unique_paragraphs.append(paragraph)

    text = "\n\n".join(unique_paragraphs)
    visible_text = " ".join(soup.stripped_strings)
    published_at = _find_published_at(soup, visible_text)

    return ParsedDocument(
        url=fetched.url,
        title=title,
        published_at=published_at,
        language=language,
        text=text,
        metadata={
            "http_status": fetched.status_code,
            "response_headers": fetched.headers,
            "parser": "beautifulsoup-html-v0.2.5",
            "http_charset": declared_encoding,
            "text_encoding": soup.original_encoding,
            "paragraph_count": len(unique_paragraphs),
        },
    )
