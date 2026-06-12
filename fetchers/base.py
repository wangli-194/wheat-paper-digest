"""
Base fetcher class and common data structures for paper fetching.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PaperMetadata:
    """Standardized paper metadata across all sources."""

    # Required fields
    title: str
    source: str  # Journal/source name (e.g., "Nature Plants", "bioRxiv")

    # Optional fields
    authors: list[str] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    abstract: str = ""
    doi: str = ""
    url: str = ""
    published_date: Optional[date] = None
    keywords: list[str] = field(default_factory=list)
    category: str = ""  # Subject category
    pdf_url: str = ""

    # Internal
    unique_id: str = ""  # Computed hash for deduplication

    def __post_init__(self):
        if not self.unique_id:
            # 有 DOI 就用 DOI 去重，避免同一篇论文被不同来源重复收录
            if self.doi:
                raw = self.doi.strip().lower()
            else:
                # 没有 DOI 用标题（标准化处理：小写+去除空格）
                raw = self.title.lower().strip()
            self.unique_id = hashlib.md5(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published_date"] = self.published_date.isoformat() if self.published_date else ""
        return d

    @property
    def first_author(self) -> str:
        return self.authors[0] if self.authors else "Unknown"

    @property
    def author_str(self) -> str:
        if len(self.authors) <= 5:
            return ", ".join(self.authors)
        return ", ".join(self.authors[:3]) + f", et al. ({len(self.authors)} authors)"

    @property
    def affiliation_str(self) -> str:
        return "; ".join(self.affiliations[:3]) if self.affiliations else "Not specified"


class BaseFetcher(ABC):
    """Abstract base class for paper fetchers."""

    def __init__(self, source_name: str = "", max_results: int = 50):
        self.source_name = source_name
        self.max_results = max_results

    @abstractmethod
    def fetch(self, keywords: list[str], lookback_days: int = 1) -> list[PaperMetadata]:
        """
        Fetch recent papers matching the given keywords.

        Args:
            keywords: List of search keywords
            lookback_days: Number of days to look back

        Returns:
            List of PaperMetadata objects
        """
        ...

    def _filter_by_keywords(
        self, papers: list[PaperMetadata], keywords: list[str]
    ) -> list[PaperMetadata]:
        """
        Filter papers by whether their title/abstract contains any keyword.
        Case-insensitive matching.
        """
        if not keywords:
            return papers

        filtered = []
        kw_lower = [k.lower() for k in keywords]

        for paper in papers:
            text = f"{paper.title} {paper.abstract} {paper.category} {' '.join(paper.keywords)}".lower()
            if any(kw in text for kw in kw_lower):
                filtered.append(paper)

        logger.info(
            "[%s] Filtered %d → %d papers by keywords",
            self.source_name, len(papers), len(filtered),
        )
        return filtered

    @staticmethod
    def _parse_date(date_str: str) -> Optional[date]:
        """Try to parse a date string in various formats."""
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        # Try ISO format parsing via dateutil
        try:
            from dateutil.parser import parse
            return parse(date_str).date()
        except Exception:
            pass

        return None
