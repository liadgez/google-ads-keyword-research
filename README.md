# Google Ads Keyword Research Tool (Hagakure Edition)

A powerful CLI tool for generating, clustering, and analyzing keywords for Google Ads campaigns, now with AI-powered Competitor Research.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-%3E%3D3.13-blue)](https://www.python.org/)

## ✨ Features

### 🔍 Keyword Research
- **Google Ads API Integration**: Fetches real keyword data (volume, CPC, competition).
- **Semantic Clustering**: Uses Sentence Transformers to group keywords by intent.
- **Hagakure Structure**: Automatically organizes keywords into Hagakure-style ad groups.
- **Negative Keyword Detection**: Identifies potential negative keywords automatically.
- **Google Sheets Export**: Exports clustered data directly to Google Sheets with pivot tables.

### 🕵️ Competitor Research (NEW!)
- **AI-Powered Analysis**: Uses Gemini 2.0 Flash to analyze competitor websites.
- **Competitor Discovery**: Finds direct competitors and market insights.
- **Multi-Format Export**: Exports results to JSON, CSV, Markdown, and Google Sheets.
- **Robust Fallbacks**: Handles timeouts and invalid URLs gracefully.

## 🚀 Quick Start

### Prerequisites
- **Python** 3.13+ ([Download](https://www.python.org/))
- **Google Cloud Project** with:
  - Google Ads API enabled
  - Google Sheets API enabled
  - OAuth 2.0 Desktop client credentials
- **Google Ads Account** (MCC or regular)
- **Gemini API Key** (for Competitor Research)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd google-ads-scripts
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   cp .env.example .env
   ```

   **Required for Competitor Research:**
   - `GEMINI_API_KEY`: Get it from [Google AI Studio](https://aistudio.google.com/apikey)

## 📖 Usage

### Keyword Research
Generate keyword ideas and cluster them into ad groups.

```bash
# Interactive Mode
python cli.py

# Non-Interactive (One-liner)
python cli.py --url https://example.com --method 3 --export y
```

### Competitor Research
Analyze a competitor's website to find their competitors and market insights.

```bash
# Interactive Mode
python cli.py --mode competitor

# Non-Interactive (One-liner)
python cli.py --mode competitor --url https://example.com --method 1 --export y
```

### Options
- `--mode`: `keyword` (default) or `competitor`
- `--url`: Target website URL
- `--method`: 
  - Keyword: `1` (Rule-based), `2` (Semantic), `3` (Hybrid)
  - Competitor: `gemini` (AI), `google` (Search API), `hybrid`
- `--export`: `y` or `n` to export results
- `--format`: `json`, `csv`, or `markdown` (for competitor mode)

## 📊 Google Sheets Export

The tool automatically creates comprehensive Google Sheets:

**Keyword Research Sheet:**
- **All Keywords:** Full list with metrics and assigned Ad Groups.
- **Overview:** Pivot table summary of clusters.
- **Negative Keywords:** List of excluded terms.

**Competitor Research Sheet:**
- **Competitors:** List of competitors with confidence scores and descriptions.
- **Market Insight:** AI-generated analysis of the market landscape.

## 🔐 Security
- `.env` is git-ignored (never commit credentials).
- OAuth tokens are stored securely.
- No hardcoded secrets in code.

## 📝 License
MIT License - feel free to use this for any purpose.
