# 🌾 Wheat Disease Resistance · Plant Immunity — Daily Paper Digest

An automated tool that retrieves the latest research papers on **wheat disease resistance** and **plant immunity** from PubMed, OpenAlex, Semantic Scholar, bioRxiv, and major journals. Papers are filtered and analyzed by DeepSeek AI, generating a clean card-style HTML digest every morning.

## Preview

Each paper is displayed as a card with:
- ★ Relevance score (wheat-specific vs. plant immunity)
- 🏛 Research institution
- 🔬 Background & scientific question
- 🧪 Methods
- 📊 Key results
- 💬 Discussion & breeding value
- ⭐ Innovation highlights
- 🌾 Relevance to wheat disease resistance breeding

## Data Sources

| Source | Description |
|--------|-------------|
| **OpenAlex** | 250M+ papers, best coverage, stable API |
| **Semantic Scholar** | AI-powered search, 200M+ papers |
| **PubMed** | Authoritative biomedical database |
| **bioRxiv** | Latest preprints |
| Nature Plants | Top plant science journal |
| Molecular Plant | Leading plant molecular biology journal |
| The Plant Cell | Authoritative plant cell biology |
| New Phytologist | Plant ecology & physiology |
| Molecular Plant Pathology | Plant pathology specialist |
| Plant Disease | APS flagship journal |
| Frontiers in Plant Science | High-volume open access |
| PLOS Pathogens | Pathogen-host interactions |

## Key Features

- **Two-stage AI filtering**: Quick relevance scoring (0-10) then deep structured analysis
- **Focus on wheat**: Prioritizes stripe rust, powdery mildew, Fusarium head blight, R genes, NLR proteins, QTL mapping
- **Deduplication**: DOI-based deduplication across all sources
- **Daily automation**: Windows Task Scheduler support, auto-retry on network failure
- **Clean HTML output**: Card-style layout, opens directly in any browser

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/wangli-194/wheat-paper-digest.git
cd wheat-paper-digest
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Copy the example file and fill in your keys:

```bash
copy .env.example .env
```

Open `.env` and add:

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
PUBMED_EMAIL=your_email@example.com
```

Get your DeepSeek API key at [platform.deepseek.com](https://platform.deepseek.com). Cost is extremely low (~¥1 per 500 papers analyzed).

> OpenAlex and Semantic Scholar require **no API key**.

## Usage

### Run once

```bash
python main.py
```

The HTML digest is saved to `output/`. Open it in any browser.

### Schedule daily at 8:00 AM (Windows)

Set up Windows Task Scheduler:
1. Program: full path to `python.exe`
2. Arguments: `main.py`
3. Start in: path to this project folder
4. Trigger: Daily at 08:00
5. Settings: Retry on failure every 30 minutes, up to 3 times

### Common options

```bash
python main.py --lookback 7    # Search last 7 days (default)
python main.py --lookback 3    # Search last 3 days
```

## How It Works

```
Fetch papers from all sources
        ↓
Deduplicate by DOI
        ↓
Stage 1: AI relevance scoring (0-10) for each paper
        ↓
Filter: keep papers scoring >= 5
        ↓
Stage 2: Deep structured analysis for top papers
        ↓
Generate HTML digest (top 8 most relevant)
```

**Relevance scoring:**
- **9-10**: Directly studies wheat disease resistance (rust, powdery mildew, FHB, R genes, NLR, QTL)
- **7-8**: Plant disease resistance mechanisms with direct reference value for wheat
- **5-6**: Plant immunity / defense signaling (SA, JA, ETI, PTI), indirect relevance
- **< 5**: Filtered out

## Configuration

Edit `config.py` to adjust:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LOOKBACK_DAYS` | 7 | Days to look back for new papers |
| `TARGET_PAPERS` | 8 | Target number of papers per digest |
| `RELEVANCE_THRESHOLD` | 5 | Minimum AI relevance score (0-10) |
| `MAX_PAPERS_TO_ANALYZE` | 30 | Max papers sent to AI for deep analysis |

## Project Structure

```
wheat-paper-digest/
├── main.py                  # Entry point
├── config.py                # Keywords, sources, parameters
├── analyzer.py              # DeepSeek AI analysis module
├── html_generator.py        # HTML digest generator
├── notifier.py              # Email notification module
├── fetchers/
│   ├── base.py              # Base fetcher & PaperMetadata
│   ├── openalex.py          # OpenAlex fetcher
│   ├── semantic_scholar.py  # Semantic Scholar fetcher
│   ├── pubmed.py            # PubMed / NCBI fetcher
│   ├── biorxiv.py           # bioRxiv fetcher
│   ├── nature.py            # Nature journals RSS fetcher
│   ├── cell.py              # Cell / Molecular Plant RSS fetcher
│   └── wiley.py             # Wiley journals RSS fetcher
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
└── output/                  # Generated digests (git-ignored)
```

## Contributing

Contributions are welcome! Areas where help is appreciated:

- **More data sources**: Europe PMC, CNKI (Chinese papers), CrossRef
- **Better relevance scoring**: Fine-tuning prompts for specific wheat diseases
- **Email delivery**: Improving the email notification module
- **Full-text retrieval**: Fetching abstracts from DOI when RSS provides none
- **Multi-language support**: Chinese wheat research community is very active

Please open an issue or submit a pull request.

## Background

Developed by a researcher in **wheat genetics and disease resistance breeding**. The goal is to automatically track the latest publications on wheat rust (stripe rust, leaf rust, stem rust), powdery mildew, Fusarium head blight, and plant immunity mechanisms — saving hours of manual literature searching each week.

If you work in plant pathology, crop breeding, or plant immunity, this tool is for you.

## License

MIT License — free to use, modify, and distribute.

---

*Generated digests are for reference only. Please consult the original papers for details.*
