"""
Paper Digest - Configuration Module
"""

import os
from pathlib import Path
from datetime import date

# ── Project paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ── API Keys ────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEEPSEEK_API_KEY  = os.getenv("DEEPSEEK_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
PUBMED_API_KEY    = os.getenv("PUBMED_API_KEY", "")
PUBMED_EMAIL      = os.getenv("PUBMED_EMAIL", "paper-digest@example.com")

EMAIL_SENDER    = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
SMTP_SERVER     = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))

# ── Journal Sources ─────────────────────────────────────────────────────────
JOURNAL_SOURCES = [

    # ── 主力检索源（覆盖最全、摘要完整）─────────────────────────────────────
    {
        "name": "OpenAlex",
        "fetcher": "OpenAlexFetcher",
        "max_results": 60,
    },
    {
        "name": "Semantic Scholar",
        "fetcher": "SemanticScholarFetcher",
        "max_results": 50,
    },
    {
        "name": "PubMed",
        "fetcher": "PubMedFetcher",
        "max_results": 100,
    },
    {
        "name": "bioRxiv",
        "fetcher": "BioRxivFetcher",
        "server": "biorxiv",
        "max_results": 50,
    },

    # ── RSS 期刊源（补充）────────────────────────────────────────────────────
    {
        "name": "Nature Plants",
        "fetcher": "NatureFetcher",
        "journal_name": "Nature Plants",
        "rss_url": "https://www.nature.com/nplants.rss",
        "max_results": 20,
    },
    {
        "name": "Molecular Plant",
        "fetcher": "CellFetcher",
        "journal_name": "Molecular Plant",
        "rss_url": "https://www.cell.com/molecular-plant/inpress.rss",
        "max_results": 20,
    },
    {
        "name": "Plant Cell",
        "fetcher": "CellFetcher",
        "journal_name": "The Plant Cell",
        "rss_url": "https://academic.oup.com/rss/site_5507/3361.xml",
        "max_results": 20,
    },
    {
        "name": "New Phytologist",
        "fetcher": "WileyFetcher",
        "journal_name": "New Phytologist",
        "rss_url": "https://nph.onlinelibrary.wiley.com/feed/14698137/most-recent",
        "max_results": 20,
    },
    {
        "name": "Molecular Plant Pathology",
        "fetcher": "WileyFetcher",
        "journal_name": "Molecular Plant Pathology",
        "rss_url": "https://bsppjournals.onlinelibrary.wiley.com/feed/13643703/most-recent",
        "max_results": 20,
    },
    {
        "name": "Plant Disease",
        "fetcher": "NatureFetcher",
        "journal_name": "Plant Disease",
        "rss_url": "https://apsjournals.apsnet.org/action/showFeed?type=etoc&feed=rss&jc=pdis",
        "max_results": 20,
    },
    {
        "name": "Frontiers in Plant Science",
        "fetcher": "NatureFetcher",
        "journal_name": "Frontiers in Plant Science",
        "rss_url": "https://www.frontiersin.org/journals/plant-science/rss",
        "max_results": 25,
    },
    {
        "name": "PLOS Pathogens",
        "fetcher": "NatureFetcher",
        "journal_name": "PLOS Pathogens",
        "rss_url": "https://journals.plos.org/plospathogens/feed/atom",
        "max_results": 20,
    },
]

# ── Search Keywords ─────────────────────────────────────────────────────────
WHEAT_DISEASE_KEYWORDS = [
    "wheat resistance", "wheat disease", "wheat immunity",
    "wheat pathogen", "wheat defense",
    "wheat rust", "stripe rust", "yellow rust", "leaf rust", "stem rust",
    "Puccinia striiformis", "Puccinia triticina", "Puccinia graminis",
    "wheat powdery mildew", "Blumeria graminis",
    "Fusarium head blight", "wheat scab", "Fusarium graminearum",
    "tan spot", "Septoria", "wheat blast", "Zymoseptoria tritici",
    "wheat NLR", "wheat NBS-LRR", "wheat R gene",
    "TaLr", "TaSr", "TaYr", "TaPm",
    "wheat QTL resistance", "wheat GWAS disease",
    "Triticum aestivum resistance", "Triticum aestivum disease",
    "Triticum urartu resistance", "Aegilops resistance",
]

CEREAL_DISEASE_KEYWORDS = [
    "barley resistance", "barley powdery mildew", "barley rust",
    "Hordeum vulgare resistance", "cereal disease resistance",
    "cereal immunity", "Mla resistance",
]

PLANT_DISEASE_KEYWORDS = [
    "plant immunity", "plant resistance", "plant defense",
    "plant pathogen", "plant disease resistance",
    "NLR protein", "NBS-LRR", "resistance gene",
    "effector triggered immunity", "ETI", "PTI",
    "pattern recognition receptor", "systemic acquired resistance",
    "jasmonic acid defense", "salicylic acid defense",
    "plant innate immunity", "rice blast", "Magnaporthe oryzae",
    "powdery mildew resistance", "Phytophthora resistance",
    "hypersensitive response", "plant immune signaling",
]

PLANT_KEYWORDS = WHEAT_DISEASE_KEYWORDS + CEREAL_DISEASE_KEYWORDS + PLANT_DISEASE_KEYWORDS

# ── Run Configuration ───────────────────────────────────────────────────────
LOOKBACK_DAYS         = 7
TARGET_PAPERS         = 8
MAX_PAPERS_TO_ANALYZE = 30
RELEVANCE_THRESHOLD   = 5

# ── Analysis Configuration ──────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"

SUMMARY_SECTIONS = [
    ("publication_info", "📋 发表信息"),
    ("affiliation",      "🏛  研究单位"),
    ("background",       "🔬 研究背景"),
    ("methods",          "🧪 研究方法"),
    ("results",          "📊 实验结果"),
    ("discussion",       "💬 讨论"),
    ("innovations",      "⭐ 创新点"),
    ("relevance_note",   "🌾 与小麦抗病研究的关联"),
]

# ── Document Configuration ──────────────────────────────────────────────────
DOCUMENT_TITLE  = f"小麦抗病·植物免疫 论文日报 - {date.today().strftime('%Y年%m月%d日')}"
DOCUMENT_AUTHOR = "Paper Digest Bot"
DOCUMENT_FONT   = "Microsoft YaHei"
