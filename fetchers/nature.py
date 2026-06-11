"""
Nature Publishing Group journal fetcher.

Fetches papers from Nature journals via RSS feeds and the Nature API.
Supported journals: Nature, Nature Plants, Nature Communications, etc.
"""

import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)


class NatureFetcher(BaseFetcher):
    """Fetcher for Nature Publishing Group journals."""

    BASE_URL = "https://www.nature.com"

    def __init__(
        self,
        source_name: str = "Nature",
        journal_name: str = "Nature Plants",
        rss_url: str = "",
        max_results: int = 20,
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.journal_name = journal_name
        self.rss_url = rss_url or self._infer_rss_url()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperDigest/1.0 (mailto:paper-digest@example.com)",
            "Accept": "application/xml, application/rss+xml, text/html",
        })

    def _infer_rss_url(self) -> str:
        """Infer RSS URL from journal name."""
        slug_map = {
            "Nature": "nature",
            "Nature Plants": "nplants",
            "Nature Communications": "ncomms",
            "Nature Genetics": "ng",
            "Nature Biotechnology": "nbt",
            "Nature Methods": "nmeth",
        }
        slug = slug_map.get(self.journal_name, self.journal_name.lower().replace(" ", ""))
        return f"https://www.nature.com/{slug}.rss"

    def fetch(
        self, keywords: list[str], lookback_days: int = 1
    ) -> list[PaperMetadata]:
        """Fetch recent papers from Nature journal RSS feed."""
        logger.info(
            "[%s] Fetching from RSS: %s", self.source_name, self.rss_url
        )

        papers = self._fetch_rss()
        logger.info("[%s] Retrieved %d papers from RSS", self.source_name, len(papers))

        # Filter by date
        cutoff = date.today() - timedelta(days=max(lookback_days, 1))
        recent = [p for p in papers if p.published_date and p.published_date >= cutoff]
        logger.info(
            "[%s] %d papers within lookback window (%d days)",
            self.source_name, len(recent), lookback_days,
        )

        # Filter by plant keywords
        filtered = self._filter_by_keywords(recent, keywords)
        filtered.sort(key=lambda p: p.published_date or date.min, reverse=True)

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

        # RSS 2.0 namespace
        namespaces = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "prism": "http://prismstandard.org/namespaces/basic/2.0/",
        }

        for item in root.findall(".//item"):
            try:
                paper = self._parse_rss_item(item, namespaces)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning("[%s] Failed to parse RSS item: %s", self.source_name, e)

        return papers

    def _parse_rss_item(
        self, item: ET.Element, namespaces: dict
    ) -> Optional[PaperMetadata]:
        """Parse a single RSS item element."""
        # Title
        title = item.findtext("title", "").strip()
        if not title:
            return None

        # Remove journal name prefix from title if present
        # e.g., "A new plant hormone..." or "Nature Plants: A new plant..."
        title = re.sub(rf'^{re.escape(self.journal_name)}:\s*', '', title)

        # Link / DOI
        link = item.findtext("link", "").strip()

        # Extract DOI from link or dc:identifier
        doi = ""
        for id_elem in item.findall("dc:identifier", namespaces):
            id_text = (id_elem.text or "").strip()
            if id_text.startswith("doi:"):
                doi = id_text[4:]
                break
        if not doi and link:
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            if doi_match:
                doi = doi_match.group()

        # Description / abstract
        description = item.findtext("description", "").strip()
        # Some feeds put HTML in description — strip tags for abstract
        abstract = BeautifulSoup(description, "lxml").get_text().strip() if description else ""

        # Full content (sometimes has better abstract)
        content_encoded = item.findtext("content:encoded", "", namespaces)
        if content_encoded and len(content_encoded) > len(abstract):
            full_text = BeautifulSoup(content_encoded, "lxml").get_text().strip()
            abstract = full_text[:2000]  # Limit abstract length

        # Authors (dc:creator)
        authors = []
        for creator in item.findall("dc:creator", namespaces):
            author = (creator.text or "").strip()
            if author:
                authors.append(author)

        # Publication date
        pub_date_str = (
            item.findtext("pubDate", "")
            or item.findtext("dc:date", "", namespaces)
            or item.findtext("prism:publicationDate", "", namespaces)
        )
        pub_date = self._parse_date(pub_date_str) if pub_date_str else None

        # Category / subject
        categories = []
        for cat in item.findall("category"):
            cat_text = (cat.text or "").strip()
            if cat_text:
                categories.append(cat_text)

        # Extract subject area from dc:subject
        for subj in item.findall("dc:subject", namespaces):
            subj_text = (subj.text or "").strip()
            if subj_text and subj_text not in categories:
                categories.append(subj_text)

        return PaperMetadata(
            title=title,
            source=self.journal_name,
            authors=authors,
            affiliations=[],  # RSS usually doesn't have affiliations
            abstract=abstract[:2500],
            doi=doi,
            url=link,
            published_date=pub_date,
            keywords=categories,
            category=", ".join(categories),
        )

    def _enrich_with_web_scrape(self, paper: PaperMetadata) -> PaperMetadata:
        """
        Optionally scrape the paper's webpage for affiliations and other metadata.
        This is slow — use sparingly.
        """
        if not paper.url:
            return paper

        try:
            resp = self.session.get(paper.url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Try to extract affiliations
            aff_elements = soup.select('.c-article-author-affiliation__address, '
                                      '[data-test="author-affiliations"] li, '
                                      '.affiliations li')
            for aff in aff_elements:
                text = aff.get_text().strip()
                if text and text not in paper.affiliations:
                    paper.affiliations.append(text)

        except Exception as e:
            logger.debug("[%s] Web scrape failed for %s: %s", self.source_name, paper.title[:50], e)

        return paper
