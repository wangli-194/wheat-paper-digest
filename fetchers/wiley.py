"""
Wiley Online Library journal fetcher.

Fetches papers from Wiley journals (New Phytologist, Plant Journal, etc.)
via RSS feeds.
"""

import logging
import re
from datetime import date, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)


class WileyFetcher(BaseFetcher):
    """Fetcher for Wiley-published journals via RSS."""

    # Known Wiley plant journal RSS feeds
    KNOWN_FEEDS = {
        "New Phytologist": "https://nph.onlinelibrary.wiley.com/feed/14698137/most-recent",
        "The Plant Journal": "https://onlinelibrary.wiley.com/feed/1365313x/most-recent",
        "Plant, Cell & Environment": "https://onlinelibrary.wiley.com/feed/13653040/most-recent",
        "Plant Biotechnology Journal": "https://onlinelibrary.wiley.com/feed/14677652/most-recent",
        "Journal of Ecology": "https://besjournals.onlinelibrary.wiley.com/feed/13652745/most-recent",
        "Journal of Applied Ecology": "https://besjournals.onlinelibrary.wiley.com/feed/13652664/most-recent",
    }

    def __init__(
        self,
        source_name: str = "Wiley",
        journal_name: str = "New Phytologist",
        rss_url: str = "",
        max_results: int = 15,
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.journal_name = journal_name
        self.rss_url = rss_url or self.KNOWN_FEEDS.get(journal_name, "")
        if not self.rss_url:
            # Try to construct from journal name
            slug = journal_name.lower().replace(" ", "-")
            self.rss_url = f"https://onlinelibrary.wiley.com/feed/journal/most-recent?title={slug}"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperDigest/1.0 (mailto:paper-digest@example.com)",
        })

    def fetch(
        self, keywords: list[str], lookback_days: int = 1
    ) -> list[PaperMetadata]:
        """Fetch recent papers from Wiley journal RSS feed."""
        logger.info("[%s] Fetching from: %s", self.source_name, self.rss_url)

        papers = self._fetch_rss()
        logger.info("[%s] Retrieved %d papers from RSS", self.source_name, len(papers))

        # Filter by date
        cutoff = date.today() - timedelta(days=max(lookback_days, 1))
        recent = [p for p in papers if not p.published_date or p.published_date >= cutoff]
        if recent:
            logger.info("[%s] %d recent papers", self.source_name, len(recent))
        else:
            recent = papers

        # Filter by plant keywords
        filtered = self._filter_by_keywords(recent, keywords)
        filtered.sort(key=lambda p: p.published_date or date.today(), reverse=True)

        return filtered[:self.max_results]

    def _fetch_rss(self) -> list[PaperMetadata]:
        """Fetch and parse the RSS feed."""
        try:
            resp = self.session.get(self.rss_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("[%s] RSS fetch failed: %s", self.source_name, e)
            return []

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            logger.error("[%s] RSS XML parse error: %s", self.source_name, e)
            return []

        papers = []
        # Wiley uses Atom format; RSS 2.0 also possible
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "dc": "http://purl.org/dc/elements/1.1/",
            "prism": "http://prismstandard.org/namespaces/basic/2.0/",
        }

        # Try Atom format first (most Wiley feeds are Atom)
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            try:
                paper = self._parse_atom_entry(entry, namespaces)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning("[%s] Failed to parse Atom entry: %s", self.source_name, e)

        # If no Atom entries, try RSS items
        if not papers:
            for item in root.findall(".//item"):
                try:
                    paper = self._parse_rss_item(item, namespaces)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning("[%s] Failed to parse RSS item: %s", self.source_name, e)

        return papers

    def _parse_atom_entry(
        self, entry: ET.Element, namespaces: dict
    ) -> Optional[PaperMetadata]:
        """Parse an Atom feed entry."""
        ns = "http://www.w3.org/2005/Atom"

        title = entry.findtext(f"{{{ns}}}title", "").strip()
        if not title:
            return None

        # Link
        link = ""
        for link_elem in entry.findall(f"{{{ns}}}link"):
            if link_elem.get("rel") in ("alternate", None, ""):
                link = link_elem.get("href", "")
                break

        # DOI
        doi = ""
        if link:
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            if doi_match:
                doi = doi_match.group()

        # Summary / abstract
        summary = entry.findtext(f"{{{ns}}}summary", "").strip() or entry.findtext(f"{{{ns}}}content", "").strip()
        abstract = BeautifulSoup(summary, "lxml").get_text().strip() if summary else ""

        # Authors
        authors = []
        for author_elem in entry.findall(f"{{{ns}}}author"):
            name = author_elem.findtext(f"{{{ns}}}name", "")
            if name:
                authors.append(name.strip())

        # Published date
        pub_date_str = entry.findtext(f"{{{ns}}}published", "") or entry.findtext(f"{{{ns}}}updated", "")
        pub_date = self._parse_date(pub_date_str) if pub_date_str else None

        # Categories
        keywords = []
        for cat_elem in entry.findall(f"{{{ns}}}category"):
            term = cat_elem.get("term", "")
            if term:
                keywords.append(term)

        return PaperMetadata(
            title=title,
            source=self.journal_name,
            authors=authors,
            affiliations=[],
            abstract=abstract[:2500],
            doi=doi,
            url=link,
            published_date=pub_date,
            keywords=keywords,
            category=", ".join(keywords),
        )

    def _parse_rss_item(
        self, item: ET.Element, namespaces: dict
    ) -> Optional[PaperMetadata]:
        """Parse an RSS 2.0 item element (fallback)."""
        title = item.findtext("title", "").strip()
        if not title:
            return None

        link = item.findtext("link", "").strip()
        description = item.findtext("description", "").strip()
        abstract = BeautifulSoup(description, "lxml").get_text().strip() if description else ""

        doi = ""
        if link:
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            if doi_match:
                doi = doi_match.group()

        authors = []
        for creator in item.findall("dc:creator", namespaces):
            author = (creator.text or "").strip()
            if author:
                authors.append(author)

        pub_date_str = item.findtext("pubDate", "") or item.findtext("dc:date", "", namespaces)
        pub_date = self._parse_date(pub_date_str) if pub_date_str else None

        return PaperMetadata(
            title=title,
            source=self.journal_name,
            authors=authors,
            affiliations=[],
            abstract=abstract[:2500],
            doi=doi,
            url=link,
            published_date=pub_date,
        )
