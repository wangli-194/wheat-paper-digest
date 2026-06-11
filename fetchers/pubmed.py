"""
PubMed / NCBI Entrez paper fetcher.

Uses the NCBI E-utilities API:
- esearch: Search for paper IDs
- efetch: Fetch detailed paper metadata

Reference: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import logging
import time
from datetime import date, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

import requests

from .base import BaseFetcher, PaperMetadata

logger = logging.getLogger(__name__)

# Plant-related MeSH terms and journal filters for PubMed
PLANT_SEARCH_FILTER = (
    '("plants"[MeSH Terms] OR "botany"[MeSH Terms] OR '
    '"plant proteins"[MeSH Terms] OR "plant roots"[MeSH Terms] OR '
    '"plant leaves"[MeSH Terms] OR "plant diseases"[MeSH Terms] OR '
    '"plant development"[MeSH Terms] OR "plant physiology"[MeSH Terms] OR '
    '"arabidopsis"[MeSH Terms] OR "oryza"[MeSH Terms] OR '
    '"zea mays"[MeSH Terms] OR "triticum"[MeSH Terms])'
)

# High-impact plant journals
PLANT_JOURNALS = [
    "Nature plants",
    "The Plant cell",
    "Plant physiology",
    "The Plant journal",
    "New phytologist",
    "Journal of experimental botany",
    "Plant, cell & environment",
    "Molecular plant",
    "Nature communications",
    "Science",
    "Nature",
    "Cell",
    "PNAS",
    "Current biology",
    "eLife",
    "Plant biotechnology journal",
    "Frontiers in plant science",
    "BMC plant biology",
]


class PubMedFetcher(BaseFetcher):
    """Fetcher for PubMed / NCBI Entrez."""

    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(
        self,
        source_name: str = "PubMed",
        max_results: int = 100,
        api_key: str = "",
        email: str = "",
        **kwargs,
    ):
        super().__init__(source_name=source_name, max_results=max_results)
        self.api_key = api_key
        self.email = email
        self.session = requests.Session()

    def _base_params(self) -> dict:
        params = {"tool": "PaperDigest", "email": self.email}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def fetch(
        self, keywords: list[str], lookback_days: int = 1
    ) -> list[PaperMetadata]:
        """
        Search PubMed for recent papers using keyword OR query.
        No MeSH restriction to avoid missing relevant papers.
        """
        today = date.today()
        start_date = today - timedelta(days=max(lookback_days, 1))

        # 关键词 OR 查询，覆盖所有关键词
        if keywords:
            kw_query = " OR ".join(
                f'"{kw}"[Title/Abstract]' for kw in keywords
            )
        else:
            kw_query = PLANT_SEARCH_FILTER

        # 日期范围（PubMed 支持 YYYY/MM/DD 格式）
        date_term = (
            f'("{start_date.strftime("%Y/%m/%d")}"[Date - Publication] : '
            f'"{today.strftime("%Y/%m/%d")}"[Date - Publication])'
        )

        query = f"({kw_query}) AND {date_term}"

        logger.info(
            "[%s] Searching: date=%s to %s, query_length=%d",
            self.source_name, start_date, today, len(query),
        )

        # Step 1: Search for PMIDs
        pmids = self._esearch(query)
        logger.info("[%s] Found %d PMIDs", self.source_name, len(pmids))

        if not pmids:
            return []

        # Step 2: Fetch detailed metadata
        papers = self._efetch(pmids[:self.max_results])
        logger.info("[%s] Fetched details for %d papers", self.source_name, len(papers))

        return papers

    def _esearch(self, query: str) -> list[str]:
        """Search PubMed and return list of PMIDs."""
        params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmax": min(self.max_results * 2, 200),
            "retmode": "json",
            "sort": "date",
            "datetype": "pdat",
        }

        try:
            resp = self.session.get(
                self.ESEARCH_URL, params=params, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except requests.RequestException as e:
            logger.error("[%s] ESearch failed: %s", self.source_name, e)
            return []
        except ValueError as e:
            logger.error("[%s] JSON parse error: %s", self.source_name, e)
            return []

    def _efetch(self, pmids: list[str]) -> list[PaperMetadata]:
        """Fetch detailed metadata for a list of PMIDs."""
        if not pmids:
            return []

        papers = []

        # Process in batches of 50 to avoid large responses
        batch_size = 50
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            batch_papers = self._efetch_batch(batch)
            papers.extend(batch_papers)
            if i + batch_size < len(pmids):
                time.sleep(0.35)  # NCBI rate limit: 3 requests/sec without API key

        return papers

    def _efetch_batch(self, pmids: list[str]) -> list[PaperMetadata]:
        """Fetch a single batch of PMIDs."""
        params = {
            **self._base_params(),
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        try:
            resp = self.session.get(
                self.EFETCH_URL, params=params, timeout=60
            )
            resp.raise_for_status()
            return self._parse_xml(resp.text)
        except requests.RequestException as e:
            logger.error("[%s] EFetch failed: %s", self.source_name, e)
            return []
        except ET.ParseError as e:
            logger.error("[%s] XML parse error: %s", self.source_name, e)
            return []

    def _parse_xml(self, xml_text: str) -> list[PaperMetadata]:
        """Parse PubMed EFetch XML response."""
        papers = []
        root = ET.fromstring(xml_text)

        for article_elem in root.findall(".//PubmedArticle"):
            try:
                paper = self._parse_article(article_elem)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning("[%s] Failed to parse article: %s", self.source_name, e)

        return papers

    def _parse_article(self, elem: ET.Element) -> Optional[PaperMetadata]:
        """Parse a single PubmedArticle element."""
        # Title
        title_elem = elem.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""
        if not title.strip():
            return None

        # Abstract
        abstract_parts = []
        for abs_elem in elem.findall(".//AbstractText"):
            label = abs_elem.get("Label", "")
            text = "".join(abs_elem.itertext()).strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = "\n".join(abstract_parts)

        # Authors
        authors = []
        affiliations_list = []
        for author_elem in elem.findall(".//Author"):
            last = author_elem.findtext("LastName", "")
            fore = author_elem.findtext("ForeName", "")
            if last:
                name = f"{last} {fore}".strip()
                authors.append(name)

            # Affiliations from author
            for aff_elem in author_elem.findall(".//AffiliationInfo/Affiliation"):
                aff_text = aff_elem.text or ""
                if aff_text and aff_text not in affiliations_list:
                    affiliations_list.append(aff_text)

        # DOI
        doi = ""
        for eid in elem.findall(".//ELocationID"):
            if eid.get("EIdType") == "doi":
                doi = (eid.text or "").strip()

        # PMID
        pmid_elem = elem.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        # URL
        url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        # Publication date
        pub_date = self._extract_pub_date(elem)

        # Journal name
        journal_elem = elem.find(".//Journal/Title")
        journal_name = journal_elem.text if journal_elem is not None else ""

        # Keywords (MeSH terms)
        keywords = []
        for kw_elem in elem.findall(".//Keyword"):
            text = kw_elem.text or ""
            if text:
                keywords.append(text)

        # Mesh headings
        for mesh_elem in elem.findall(".//MeshHeading"):
            descriptor = mesh_elem.findtext("DescriptorName", "")
            if descriptor:
                keywords.append(descriptor)

        # Build source display name
        source = journal_name or "PubMed"

        return PaperMetadata(
            title=title.strip(),
            source=source,
            authors=authors,
            affiliations=affiliations_list[:5],  # Limit affiliations
            abstract=abstract.strip(),
            doi=doi,
            url=url,
            published_date=pub_date,
            keywords=keywords,
            category="",
        )

    def _extract_pub_date(self, elem: ET.Element) -> Optional[date]:
        """Extract publication date from PubMed article element."""
        pub_date_elem = elem.find(".//PubDate")

        if pub_date_elem is None:
            return None

        year = pub_date_elem.findtext("Year")
        month = pub_date_elem.findtext("Month", "1")
        day = pub_date_elem.findtext("Day", "1")

        if not year:
            # Try MedlineDate format
            medline_date = pub_date_elem.findtext("MedlineDate", "")
            return self._parse_date(medline_date.split()[0] if medline_date else "")

        # Month might be 3-letter abbreviation
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        try:
            month_num = int(month)
        except ValueError:
            month_num = month_map.get(month.lower()[:3], 1)

        try:
            return date(int(year), month_num, int(day))
        except (ValueError, TypeError):
            try:
                return date(int(year), month_num, 1)
            except (ValueError, TypeError):
                return None
