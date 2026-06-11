"""
Paper Digest - Fetchers Package

Each fetcher searches a specific journal/source and returns a standardized
list of paper metadata dicts.
"""

from .base import BaseFetcher, PaperMetadata
from .biorxiv import BioRxivFetcher
from .pubmed import PubMedFetcher
from .nature import NatureFetcher
from .cell import CellFetcher
from .wiley import WileyFetcher

# Registry mapping fetcher name → class
FETCHER_REGISTRY = {
    "BioRxivFetcher": BioRxivFetcher,
    "PubMedFetcher": PubMedFetcher,
    "NatureFetcher": NatureFetcher,
    "CellFetcher": CellFetcher,
    "WileyFetcher": WileyFetcher,
}


def get_fetcher(name: str, **kwargs) -> BaseFetcher:
    """Get a fetcher instance by name."""
    cls = FETCHER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown fetcher: {name}. Available: {list(FETCHER_REGISTRY.keys())}")
    return cls(**kwargs)


__all__ = [
    "BaseFetcher", "PaperMetadata",
    "BioRxivFetcher", "PubMedFetcher", "NatureFetcher",
    "CellFetcher", "WileyFetcher",
    "FETCHER_REGISTRY", "get_fetcher",
]
