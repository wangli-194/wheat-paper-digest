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
# 覆盖植物/作物/抗病领域主流期刊，按 fetcher 类型分组
JOURNAL_SOURCES = [

    # ── PubMed（最重要，直接用关键词搜索，覆盖所有 MEDLINE 期刊）──────────
    {
        "name": "PubMed",
        "fetcher": "PubMedFetcher",
        "max_results": 100,
    },

    # ── bioRxiv 预印本 ────────────────────────────────────────────────────
    {
        "name": "bioRxiv",
        "fetcher": "BioRxivFetcher",
        "server": "biorxiv",
        "max_results": 80,
    },

    # ── Nature 系列 ───────────────────────────────────────────────────────
    {
        "name": "Nature Plants",
        "fetcher": "NatureFetcher",
        "journal_name": "Nature Plants",
        "rss_url": "https://www.nature.com/nplants.rss",
        "max_results": 30,
    },
    {
        "name": "Nature Communications",
        "fetcher": "NatureFetcher",
        "journal_name": "Nature Communications",
        "rss_url": "https://www.nature.com/ncomms.rss",
        "max_results": 20,
    },
    {
        "name": "Nature",
        "fetcher": "NatureFetcher",
        "journal_name": "Nature",
        "rss_url": "https://www.nature.com/nature.rss",
        "max_results": 15,
    },

    # ── Cell 系列 ─────────────────────────────────────────────────────────
    {
        "name": "Cell",
        "fetcher": "CellFetcher",
        "journal_name": "Cell",
        "rss_url": "https://www.cell.com/cell/inpress.rss",
        "max_results": 15,
    },
    {
        "name": "Cell Host & Microbe",
        "fetcher": "CellFetcher",
        "journal_name": "Cell Host & Microbe",
        "rss_url": "https://www.cell.com/cell-host-microbe/inpress.rss",
        "max_results": 20,
    },
    {
        "name": "Current Biology",
        "fetcher": "CellFetcher",
        "journal_name": "Current Biology",
        "rss_url": "https://www.cell.com/current-biology/inpress.rss",
        "max_results": 15,
    },
    {
        "name": "Molecular Plant",
        "fetcher": "CellFetcher",
        "journal_name": "Molecular Plant",
        "rss_url": "https://www.cell.com/molecular-plant/inpress.rss",
        "max_results": 30,
    },
    {
        "name": "Molecular Plant-Microbe Interactions",
        "fetcher": "CellFetcher",
        "journal_name": "Molecular Plant-Microbe Interactions",
        "rss_url": "https://apsjournals.apsnet.org/action/showFeed?type=etoc&feed=rss&jc=mpmi",
        "max_results": 25,
    },

    # ── OUP（牛津大学出版社）─────────────────────────────────────────────
    {
        "name": "Plant Cell",
        "fetcher": "CellFetcher",
        "journal_name": "The Plant Cell",
        "rss_url": "https://academic.oup.com/rss/site_5507/3361.xml",
        "max_results": 25,
    },
    {
        "name": "Plant Physiology",
        "fetcher": "CellFetcher",
        "journal_name": "Plant Physiology",
        "rss_url": "https://academic.oup.com/rss/site_5507/3362.xml",
        "max_results": 25,
    },
    {
        "name": "Journal of Experimental Botany",
        "fetcher": "CellFetcher",
        "journal_name": "Journal of Experimental Botany",
        "rss_url": "https://academic.oup.com/rss/site_5324/3097.xml",
        "max_results": 25,
    },

    # ── Wiley 系列 ────────────────────────────────────────────────────────
    {
        "name": "New Phytologist",
        "fetcher": "WileyFetcher",
        "journal_name": "New Phytologist",
        "rss_url": "https://nph.onlinelibrary.wiley.com/feed/14698137/most-recent",
        "max_results": 20,
    },
    {
        "name": "Plant Journal",
        "fetcher": "WileyFetcher",
        "journal_name": "The Plant Journal",
        "rss_url": "https://onlinelibrary.wiley.com/feed/1365313x/most-recent",
        "max_results": 20,
    },
    {
        "name": "Molecular Plant Pathology",
        "fetcher": "WileyFetcher",
        "journal_name": "Molecular Plant Pathology",
        "rss_url": "https://bsppjournals.onlinelibrary.wiley.com/feed/13643703/most-recent",
        "max_results": 25,
    },
    {
        "name": "Plant Cell & Environment",
        "fetcher": "WileyFetcher",
        "journal_name": "Plant Cell & Environment",
        "rss_url": "https://onlinelibrary.wiley.com/feed/13653040/most-recent",
        "max_results": 15,
    },
    {
        "name": "Plant Pathology",
        "fetcher": "WileyFetcher",
        "journal_name": "Plant Pathology",
        "rss_url": "https://bsppjournals.onlinelibrary.wiley.com/feed/13653059/most-recent",
        "max_results": 25,
    },
    {
        "name": "Theoretical and Applied Genetics",
        "fetcher": "WileyFetcher",
        "journal_name": "Theoretical and Applied Genetics",
        "rss_url": "https://link.springer.com/search.rss?facet-journal-id=122&query=",
        "max_results": 20,
    },

    # ── APS（美国植物病理学会）────────────────────────────────────────────
    {
        "name": "Phytopathology",
        "fetcher": "NatureFetcher",   # RSS 格式兼容
        "journal_name": "Phytopathology",
        "rss_url": "https://apsjournals.apsnet.org/action/showFeed?type=etoc&feed=rss&jc=phyto",
        "max_results": 25,
    },
    {
        "name": "Plant Disease",
        "fetcher": "NatureFetcher",
        "journal_name": "Plant Disease",
        "rss_url": "https://apsjournals.apsnet.org/action/showFeed?type=etoc&feed=rss&jc=pdis",
        "max_results": 25,
    },

    # ── Frontiers ─────────────────────────────────────────────────────────
    {
        "name": "Frontiers in Plant Science",
        "fetcher": "NatureFetcher",
        "journal_name": "Frontiers in Plant Science",
        "rss_url": "https://www.frontiersin.org/journals/plant-science/rss",
        "max_results": 30,
    },

    # ── PLOS ─────────────────────────────────────────────────────────────
    {
        "name": "PLOS Pathogens",
        "fetcher": "NatureFetcher",
        "journal_name": "PLOS Pathogens",
        "rss_url": "https://journals.plos.org/plospathogens/feed/atom",
        "max_results": 20,
    },
    {
        "name": "PLOS Biology",
        "fetcher": "NatureFetcher",
        "journal_name": "PLOS Biology",
        "rss_url": "https://journals.plos.org/plosbiology/feed/atom",
        "max_results": 15,
    },
]

# ── Search Keywords ─────────────────────────────────────────────────────────
# 第一优先级：小麦抗病（核心）
WHEAT_DISEASE_KEYWORDS = [
    # 通用
    "wheat resistance", "wheat disease", "wheat immunity",
    "wheat pathogen", "wheat defense",
    # 锈病
    "wheat rust", "stripe rust", "yellow rust", "leaf rust", "stem rust",
    "Puccinia striiformis", "Puccinia triticina", "Puccinia graminis",
    # 白粉病
    "wheat powdery mildew", "Blumeria graminis",
    # 赤霉病
    "Fusarium head blight", "wheat scab", "Fusarium graminearum",
    # 其他病害
    "tan spot", "Septoria", "wheat blast", "Zymoseptoria tritici",
    "wheat spot blotch", "Bipolaris sorokiniana",
    # 抗病基因
    "wheat NLR", "wheat NBS-LRR", "wheat R gene",
    "TaLr", "TaSr", "TaYr", "TaPm", "TaMla",
    # 遗传育种
    "wheat QTL resistance", "wheat GWAS disease",
    "wheat breeding resistance", "wheat mapping resistance",
    # 物种名
    "Triticum aestivum resistance", "Triticum aestivum disease",
    "Triticum aestivum immunity", "Triticum dicoccoides resistance",
    "Aegilops resistance",
]

# 第二优先级：大麦/黑麦等近缘作物抗病
CEREAL_DISEASE_KEYWORDS = [
    "barley resistance", "barley powdery mildew", "barley rust",
    "barley Blumeria", "Hordeum vulgare resistance",
    "rye resistance", "triticale resistance",
    "cereal disease resistance", "cereal immunity",
    "Mla resistance", "RPG1", "HvRpg1",
]

# 第三优先级：植物抗病通用机制
PLANT_DISEASE_KEYWORDS = [
    "plant immunity", "plant resistance", "plant defense",
    "plant pathogen", "plant disease resistance",
    "NLR protein", "NBS-LRR", "resistance gene",
    "effector triggered immunity", "ETI", "PTI",
    "PAMP triggered immunity", "pattern recognition receptor",
    "PRR plant", "RLK immunity", "RLP immunity",
    "systemic acquired resistance", "SAR",
    "jasmonic acid defense", "salicylic acid defense",
    "plant innate immunity", "plant basal resistance",
    "rice blast", "Magnaporthe oryzae",
    "powdery mildew resistance", "downy mildew resistance",
    "Phytophthora resistance", "effector plant",
    "hypersensitive response", "HR plant",
    "plant immune signaling", "defense signaling",
]

PLANT_KEYWORDS = WHEAT_DISEASE_KEYWORDS + CEREAL_DISEASE_KEYWORDS + PLANT_DISEASE_KEYWORDS

# ── Run Configuration ───────────────────────────────────────────────────────
LOOKBACK_DAYS         =   7 # 回溯天数
TARGET_PAPERS          = 8    # 每日简报目标篇数（期刊多了适当放宽）
MAX_PAPERS_TO_ANALYZE  = 30   # 最多送 AI 分析的篇数
RELEVANCE_THRESHOLD    = 5    # 相关性阈值（期刊扩充后稍微放宽到5）

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
