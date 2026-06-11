"""
Cell Press / Elsevier journal fetcher.

Fetches papers from Cell, Current Biology, Molecular Plant,
The Plant Cell (via OUP RSS) and other life science journals.
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


class CellFetcher(BaseFetcher):
    """Fetcher for Cell Press journals (Cell, Current Biology, Molecular Plant, etc.)."""

    CELL_RSS_PATTERNS = {
        "Cell": "https://www.cell.com/cell/inpress.rss",
        "Current Biology": "https://www.cell.com/current-biology/inpress.rss",
        "Molecular Plant": "https://www.cell.com/molecular-plant/inpress.rss",
        "Developmental Cell": "https://www.cell.com/developmental-cell/inpress.rss",
        "Plant Communications": "https://www.cell.com/plant-communications/inpress.rss",
    }

    def __init__(
        self,
        source_name: str = "Cell",
        journal_name: str = "Cell",
        rss_url: str = "",
        max_results: int = 10,
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.journal_name = journal_name
        self.rss_url = rss_url or self.CELL_RSS_PATTERNS.get(journal_name, "")
        if not self.rss_url:
            # Generate a generic Cell Press RSS URL
            slug = journal_name.lower().replace(" ", "-")
            self.rss_url = f"https://www.cell.com/{slug}/inpress.rss"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperDigest/1.0 (mailto:paper-digest@example.com)",
        })

    def fetch(
        self, keywords: list[str], lookback_days: int = 1
    ) -> list[PaperMetadata]:
        """Fetch recent papers from Cell Press RSS feed."""
        logger.info("[%s] Fetching from: %s", self.source_name, self.rss_url)

        papers = self._fetch_rss()
        logger.info("[%s] Retrieved %d papers from RSS", self.source_name, len(papers))

        # Filter by date
        cutoff = date.today() - timedelta(days=max(lookback_days, 1))
        recent = [p for p in papers if not p.published_date or p.published_date >= cutoff]

        if recent:
            logger.info("[%s] %d recent papers", self.source_name, len(recent))
        else:
            # If no date info, return all (likely all in-press / recent)
            recent = papers
            logger.info("[%s] %d papers (date filtering skipped)", self.source_name, len(recent))

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
        namespaces = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "prism": "http://prismstandard.org/namespaces/basic/2.0/",
            "content": "http://purl.org/rss/1.0/modules/content/",
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
        title = item.findtext("title", "").strip()
        if not title:
            return None

        link = item.findtext("link", "").strip()

        # DOI — Cell RSS often has prism:doi
        doi = item.findtext("prism:doi", "", namespaces).strip()
        if not doi and link:
            doi_match = re.search(r'10\.\d{4,}/[^\s?#]+', link)
            if doi_match:
                doi = doi_match.group()

        # Abstract from description
        description = item.findtext("description", "").strip()
        # Clean HTML tags from description
        abstract = BeautifulSoup(description, "lxml").get_text().strip() if description else ""

        # Better abstract from content:encoded
        content = item.findtext("content:encoded", "", namespaces)
        if content:
            content_text = BeautifulSoup(content, "lxml").get_text().strip()
            if len(content_text) > len(abstract):
                abstract = content_text[:2500]

        # Authors
        authors = []
        for creator in item.findall("dc:creator", namespaces):
            author = (creator.text or "").strip()
            if author:
                authors.append(author)

        # Publication date
        pub_date_str = (
            item.findtext("prism:publicationDate", "", namespaces)
            or item.findtext("dc:date", "", namespaces)
            or item.findtext("pubDate", "")
        )
        pub_date = self._parse_date(pub_date_str) if pub_date_str else None

        # Keywords / subjects
        keywords = []
        for subj in item.findall("dc:subject", namespaces):
            subj_text = (subj.text or "").strip()
            if subj_text:
                keywords.append(subj_text)

        for cat in item.findall("category"):
            cat_text = (cat.text or "").strip()
            if cat_text and cat_text not in keywords:
                keywords.append(cat_text)

        # PDF URL
        pdf_url = ""
        if doi:
            pdf_url = f"https://www.cell.com/article/{doi}/pdf"

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
            pdf_url=pdf_url,
        )
