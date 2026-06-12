"""Fetchers package"""

from .base import BaseFetcher, PaperMetadata
from .pubmed import PubMedFetcher
from .biorxiv import BioRxivFetcher
from .nature import NatureFetcher
from .cell import CellFetcher
from .wiley import WileyFetcher
from .openalex import OpenAlexFetcher
from .semantic_scholar import SemanticScholarFetcher


_REGISTRY = {
    "PubMedFetcher":          PubMedFetcher,
    "BioRxivFetcher":         BioRxivFetcher,
    "NatureFetcher":          NatureFetcher,
    "CellFetcher":            CellFetcher,
    "WileyFetcher":           WileyFetcher,
    "OpenAlexFetcher":        OpenAlexFetcher,
    "SemanticScholarFetcher": SemanticScholarFetcher,
}


def get_fetcher(name: str, **kwargs) -> BaseFetcher:
    cls = _REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown fetcher: {name}")
    return cls(**kwargs)
