# Google Ads Keyword Research Tool (Hagakure Edition)

A powerful CLI tool for generating, clustering, and analyzing keywords for Google Ads campaigns, now with AI-powered Competitor Research.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-%3E%3D3.13-blue)](https://www.python.org/)

## ✨ Features

### 🔍 Keyword Research
- **Google Ads API Integration**: Fetches real keyword data (volume, CPC, competition)
- **Semantic Clustering**: Uses Sentence Transformers to group keywords by intent
- **Hagakure Structure**: Automatically organizes keywords into Hagakure-style ad groups
- **Negative Keyword Detection**: Identifies potential negative keywords automatically
- **Google Sheets Export**: Exports clustered data directly to Google Sheets with pivot tables

### 🕵️ Competitor Research (NEW!)
- **AI-Powered Analysis**: Uses Gemini 2.0 Flash to analyze competitor websites
- **Competitor Discovery**: Finds direct competitors and market insights
- **Multi-Format Export**: Exports results to JSON, CSV, Markdown, and Google Sheets
- **Robust Fallbacks**: Handles timeouts and invalid URLs gracefully

### 💬 WhatsApp Bot Integration (NEW!)
- **Conversational Interface**: Interact with the tool via WhatsApp messages
- **Real-time Results**: Get keyword research and competitor analysis on your phone
- **Automatic Exports**: Receive Google Sheets links directly in WhatsApp
- **Easy Commands**: Simple text commands like "research [URL]" or "competitors [URL]"
- **Rich Formatting**: Beautiful messages with emojis, formatting, and interactive buttons

## 🚀 Quick Start

### Prerequisites
- **Python** 3.13+ ([Download](https://www.python.org/))
- **Google Cloud Project** with:
  - Google Ads API enabled
  - Google Sheets API enabled
  - OAuth 2.0 Desktop client credentials
- **Google Ads Account** (MCC or regular)
- **Gemini API Key** (for Competitor Research - [Get it here](https://aistudio.google.com/apikey))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/liadgez/google-ads-keyword-research.git
   cd google-ads-keyword-research
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

   **Required Variables:**
   - `GOOGLE_ADS_DEVELOPER_TOKEN`: Your Google Ads developer token
   - `GOOGLE_ADS_CLIENT_ID`: OAuth client ID
   - `GOOGLE_ADS_CLIENT_SECRET`: OAuth client secret
   - `GOOGLE_ADS_REFRESH_TOKEN`: OAuth refresh token (run `python api/run_oauth_and_update_env.py`)
   - `GOOGLE_ADS_LOGIN_CUSTOMER_ID`: Your Google Ads customer ID
   - `GEMINI_API_KEY`: Your Gemini API key (for competitor research)

## 📖 Usage

### Keyword Research
Generate keyword ideas and cluster them into ad groups.

```bash
# Interactive Mode
python cli.py

# Non-Interactive (Recommended for automation)
python cli.py --url https://example.com --method 3 --export y
```

**Example Output:**
```
✅ Found 1,340 keywords
✅ Created 694 ad groups
✅ Identified 9 negative keywords
📊 Google Sheet: https://docs.google.com/spreadsheets/d/...
```

### Competitor Research
Analyze a competitor's website to find their competitors and market insights.

```bash
# Interactive Mode
python cli.py --mode competitor

# Non-Interactive (Recommended)
python cli.py --mode competitor --url https://example.com --method 1 --export y
```

**Example Output:**
```
✅ Analysis Complete
Brand: Example Company
Keyword: example services
Competitors Found: 8

Market Insight:
The market is highly competitive with established players...

📊 Google Sheet: https://docs.google.com/spreadsheets/d/...
```

### WhatsApp Bot
Interact with the tool directly from WhatsApp!

**Quick Start:**
```bash
# 1. Configure WhatsApp credentials in .env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_VERIFY_TOKEN=myverifycode123

# 2. Start the server and ngrok
./start_whatsapp_bot.sh

# 3. Send WhatsApp messages to your bot:
"help"                              # Show available commands
"research https://netflix.com"      # Keyword research
"competitors https://netflix.com"   # Competitor analysis
```

**📖 Full Setup Guide:** See [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md) for detailed instructions.

**Example WhatsApp Conversation:**
```
You: research https://shopify.com

Bot: 🔍 Keyword Research Started
     Analyzing: https://shopify.com
     ⏳ This may take 30-60 seconds...

Bot: ✅ Keyword Research Complete!
     📊 Results Summary:
     • Keywords Found: 1,247
     • Ad Groups Created: 89
     
     📈 View Full Report:
     https://docs.google.com/spreadsheets/d/...
```

### CLI Options

| Option | Values | Description |
|--------|--------|-------------|
| `--mode` | `keyword`, `competitor` | Mode of operation (default: `keyword`) |
| `--url` | URL string | Target website URL (required) |
| `--method` | Keyword: `1`, `2`, `3`<br>Competitor: `gemini`, `google`, `hybrid` | Clustering/analysis method |
| `--export` | `y`, `n` | Export results (default: prompt) |
| `--format` | `json`, `csv`, `markdown` | Export format for competitor mode |

**Clustering Methods:**
- `1` - **Rule-based**: Fast, pattern matching
- `2` - **Semantic (ML)**: AI-powered, intent-based
- `3` - **Hybrid**: Best of both (recommended)

## 🧪 Testing

### Test Clustering Engine
```bash
python test_clustering.py
```

**Expected Output:**
```
Testing Rule-Based Clustering...
Cluster: Netflix Login (3 kws)
  - netflix login
  - netflix sign in
  - netflix log in

Testing Negatives...
Negatives found: [{'keyword': 'hiring', 'category': 'job'}]
✅ Tests Passed
```

### Test Competitor Research
```bash
python cli.py --mode competitor --url https://www.example.com --method 1 --export y
```

**Success Criteria:**
- ✅ Competitors found (typically 5-8)
- ✅ Market insight generated
- ✅ JSON file created in `output/`
- ✅ Google Sheet created and accessible

### Test Keyword Research
```bash
python cli.py --url https://www.netflix.com --method 3 --export y
```

**Success Criteria:**
- ✅ Keywords found (typically 500-2000)
- ✅ Ad groups created
- ✅ Negative keywords identified
- ✅ Google Sheet with pivot table created

## 📊 Google Sheets Export

The tool automatically creates comprehensive Google Sheets:

### Keyword Research Sheet
- **All Keywords**: Full list with metrics and assigned Ad Groups
- **Overview**: Pivot table summary showing:
  - Keywords count per ad group
  - Total search volume
  - Average competition
  - Average CPC (low/high)
- **Negative Keywords**: Excluded terms with categories (job, academic, piracy)

### Competitor Research Sheet
- **Competitors**: List with confidence scores, services, and descriptions
- **Market Insight**: AI-generated market analysis

All sheets are automatically made **public** (view-only) for easy sharing.

## 📁 Project Structure

```
google-ads-keyword-research/
├── api/
│   ├── clustering.py              # Clustering algorithms
│   ├── competitor_research.py     # AI competitor analysis
│   ├── keyword_planner.py         # Google Ads API integration
│   ├── sheets_exporter.py         # Base sheets exporter
│   ├── sheets_exporter_clustered.py  # Clustered export
│   ├── sheets_exporter_competitor.py # Competitor export
│   ├── sheets_utils.py            # Shared formatting utilities
│   ├── utils.py                   # General utilities
│   └── run_oauth_and_update_env.py   # OAuth helper
├── cli.py                         # Main CLI interface
├── main.py                        # FastAPI server
├── test_clustering.py             # Clustering tests
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🔐 Security Best Practices

- ✅ `.env` is git-ignored (never commit credentials)
- ✅ OAuth tokens are stored securely
- ✅ No hardcoded secrets in code
- ✅ API keys are loaded from environment variables
- ⚠️ **Never share your `.env` file or commit it to version control**

## 🐛 Troubleshooting

### "Missing GEMINI_API_KEY" Error
**Solution:** Add your Gemini API key to `.env`:
```bash
GEMINI_API_KEY=your_key_here
```
Get a key from: https://aistudio.google.com/apikey

### "Failed to fetch HTML" Warning
**Solution:** This is normal for sites that block scrapers. The tool automatically falls back to URL-only analysis, which still works well.

### "Sheet not created" Error
**Solution:** Ensure your OAuth refresh token has Google Sheets scope:
```bash
python api/run_oauth_and_update_env.py
```
Grant both scopes when prompted.

### Rate Limit Errors
**Solution:** Wait 1-2 seconds between requests. The Google Ads API has rate limits.

## 🚀 Advanced Usage

### Batch Processing (Future)
```bash
# Process multiple URLs
python cli.py --batch urls.txt --method 3 --export y
```

### API Server
```bash
# Start FastAPI server
python main.py

# Access at http://localhost:3002
```

## 📝 License

MIT License - feel free to use this for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/liadgez/google-ads-keyword-research/issues)
- **Documentation**: This README
- **Google Ads API**: [Official Docs](https://developers.google.com/google-ads/api)

---

**Built with ❤️ using Google Ads API, Gemini AI, and Google Sheets API**
