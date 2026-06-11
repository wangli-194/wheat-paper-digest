"""
bioRxiv / medRxiv paper fetcher.

Uses the bioRxiv Content API:
https://api.biorxiv.org/details/biorxiv/<date_range>/<cursor>/<max_results>

Reference: https://www.biorxiv.org/about/tdm
"""

import logging
import time
from datetime import date, timedelta
from typing import Optional

import requests

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)

# bioRxiv subject areas relevant to plant biology
PLANT_COLLECTIONS = [
    "plant_biology",
    "genetics",
    "genomics",
    "molecular_biology",
    "developmental_biology",
    "ecology",
    "evolutionary_biology",
    "microbiology",
    "systems_biology",
    "synthetic_biology",
    "agricultural_sciences",
]

# Core plant-related subject area that we always search
PRIMARY_COLLECTION = "plant_biology"


class BioRxivFetcher(BaseFetcher):
    """Fetcher for bioRxiv preprint server."""

    API_BASE = "https://api.biorxiv.org"

    def __init__(
        self,
        source_name: str = "bioRxiv",
        server: str = "biorxiv",
        max_results: int = 50,
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.server = server  # "biorxiv" or "medrxiv"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PaperDigest/1.0 (mailto:paper-digest@example.com)",
            "Accept": "application/json",
        })

    def fetch(
        self, keywords: list[str], lookback_days: int = 1
    ) -> list[PaperMetadata]:
        """
        Fetch recent plant-related papers from bioRxiv.

        Strategy:
        1. Query the plant_biology collection for recent dates
        2. Also search any papers with plant keywords in title/abstract
        3. Deduplicate and filter
        """
        today = date.today()
        start_date = today - timedelta(days=max(lookback_days, 3))
        all_papers: list[PaperMetadata] = []

        # Fetch from plant biology collection
        logger.info(
            "[%s] Fetching papers from %s to %s (collection: plant_biology)",
            self.source_name, start_date, today,
        )

        papers = self._fetch_date_range(start_date, today)
        logger.info("[%s] Retrieved %d papers from date range", self.source_name, len(papers))

        # Filter by plant keywords
        filtered = self._filter_by_keywords(papers, keywords)
        # Sort by date descending
        filtered.sort(key=lambda p: p.published_date or date.min, reverse=True)

        return filtered[:self.max_results]

    def _fetch_date_range(
        self, start: date, end: date
    ) -> list[PaperMetadata]:
        """
        Fetch papers from bioRxiv within a date range using the content API.
        Uses cursor-based pagination.
        """
        papers = []
        cursor = 0
        max_pages = 5  # Safety limit

        date_interval = f"{start.isoformat()}/{end.isoformat()}"

        for _ in range(max_pages):
            url = f"{self.API_BASE}/details/{self.server}/{date_interval}/{cursor}/100"

            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                logger.error("[%s] API request failed: %s", self.source_name, e)
                break
            except ValueError as e:
                logger.error("[%s] JSON parse error: %s", self.source_name, e)
                break

            collection = data.get("collection", [])
            if not collection:
                break

            for item in collection:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)

            # Cursor pagination
            messages = data.get("messages", [])
            cursor = messages[0].get("cursor", 0) if messages else 0
            count = messages[0].get("count", 0) if messages else 0

            logger.debug(
                "[%s] Page cursor=%d, got %d papers (total: %d)",
                self.source_name, cursor, count, len(papers),
            )

            if cursor == 0 or count == 0:
                break

            time.sleep(0.5)  # Rate limiting

        return papers

    def _parse_item(self, item: dict) -> Optional[PaperMetadata]:
        """Parse a bioRxiv API item into PaperMetadata."""
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            doi = item.get("doi", "")
            abstract = item.get("abstract", "").strip()
            authors_str = item.get("authors", "")
            authors = [a.strip() for a in authors_str.split(";") if a.strip()] if authors_str else []

            # bioRxiv API provides author list but not affiliations in the detail view
            affiliations: list[str] = []

            # Author affiliations are sometimes embedded in the author string
            # e.g., "Smith J (Harvard University)"
            author_corresponding = item.get("author_corresponding", "")
            institution = item.get("author_corresponding_institution", "")
            if institution:
                affiliations.append(institution.strip())

            # Date parsing
            date_str = item.get("date", "") or item.get("server_date", "")
            pub_date = self._parse_date(date_str) if date_str else None

            # Category
            category = item.get("category", "")

            # URL
            url = f"https://doi.org/{doi}" if doi else ""
            if not url and doi:
                url = f"https://www.biorxiv.org/content/{doi}"

            return PaperMetadata(
                title=title,
                source=self.source_name,
                authors=authors,
                affiliations=affiliations,
                abstract=abstract,
                doi=doi,
                url=url,
                published_date=pub_date,
                keywords=[category] if category else [],
                category=category,
                pdf_url=f"https://www.biorxiv.org/content/{doi}.pdf" if doi else "",
            )
        except Exception as e:
            logger.warning("[%s] Failed to parse item: %s", self.source_name, e)
            return None

    def search_by_abstract(
        self, keywords: list[str], lookback_days: int = 7
    ) -> list[PaperMetadata]:
        """
        Alternative search using bioRxiv's search endpoint.
        Searches the abstract/title fields for specific terms.
        """
        papers = []
        today = date.today()
        start_date = today - timedelta(days=lookback_days)

        # Use the content API with date range, then filter
        all_papers = self._fetch_date_range(start_date, today)
        return self._filter_by_keywords(all_papers, keywords)
