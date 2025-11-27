# Google Ads Keyword Research Tool
gh repo - https://github.com/liadgez/google-ads-keyword-research

> Production-ready keyword research tool that generates keyword ideas from any URL using the Google Ads API and automatically exports results to beautifully formatted Google Sheets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.13-blue)](https://www.python.org/)

## ✨ Features

- 🔍 **URL-based keyword research** - Analyze any website to discover relevant keywords
- 📊 **Automatic Google Sheets export** - Results are automatically formatted and saved
- 📈 **Real Google Ads data** - Actual search volumes, competition levels, and bid estimates
- ⚡ **Fast & efficient** - Optimized hybrid architecture (Node.js + Python)
- 🎨 **Modern web UI** - Beautiful, responsive interface for easy testing
- 🔌 **Simple REST API** - Easy integration with other tools and workflows

## 📊 Data Provided

For each keyword discovered, you get:

| Field | Description |
|-------|-------------|
| **Keyword** | The actual keyword phrase |
| **Avg Monthly Searches** | Average monthly search volume |
| **Competition** | LOW / MEDIUM / HIGH |
| **Competition Index** | 0-100 score |
| **Low Bid** | Minimum suggested bid (USD) |
| **High Bid** | Maximum suggested bid (USD) |

## 🏗️ Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Client    │─────▶│   FastAPI    │─────▶│  Python Logic   │
│  (Browser)  │      │   (Python)   │      │  (Direct Call)  │
└─────────────┘      └──────────────┘      └─────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Google Ads API │
                                            │ Google Sheets   │
                                            └─────────────────┘
```

**Why this architecture?**
- **Pure Python**: Single language stack, easier maintenance
- **FastAPI**: Modern, high-performance web framework
- **Direct Execution**: No overhead from spawning subprocesses

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.13+ ([Download](https://www.python.org/))
- **Google Cloud Project** with:
  - Google Ads API enabled
  - Google Sheets API enabled
  - OAuth 2.0 Desktop client credentials
- **Google Ads Account** (MCC or regular)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd google-ads-scripts

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn google-ads-googleads python-dotenv \
            google-api-python-client google-auth-httplib2 \
            google-auth-oauthlib
```

### Configuration

Create a `.env` file in the project root:

```env
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

### Get OAuth Refresh Token

The refresh token must have **both** scopes:
- `https://www.googleapis.com/auth/adwords`
- `https://www.googleapis.com/auth/spreadsheets`

Run the automated helper:

```bash
source venv/bin/activate
python api/run_oauth_and_update_env.py
```

### ⚡ Instant Test

Want to see it in action immediately? Run this one-liner:

```bash
# Runs the CLI with default settings (Netflix, Hybrid Clustering, No Export)
source venv/bin/activate && python cli.py
```

Or for the full interactive experience:

```bash
source venv/bin/activate
python cli.py
```

### Start the API Server
If you prefer the web interface or REST API:

```bash
source venv/bin/activate
python main.py
```

Server runs on `http://localhost:3002` 🎉

## 📖 Usage

### Web UI

1. Open `http://localhost:3002` in your browser
2. Enter any website URL
3. Click "Generate Keywords"
4. Wait 10-30 seconds
5. View results and click the Google Sheet link

### API Endpoint

**POST** `/keyword-research`

**Request:**
```json
{
  "url": "https://example.com",
  "keywords": ["optional", "seed", "keywords"],
  "languageCode": "en",
  "locationIds": ["2840"]
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "totalResults": 1226,
  "sheetUrl": "https://docs.google.com/spreadsheets/d/...",
  "keywords": [
    {
      "keyword": "example keyword",
      "avgMonthlySearches": 14800,
      "competition": "LOW",
      "competitionIndex": 6,
      "lowTopOfPageBidMicros": 571426,
      "highTopOfPageBidMicros": 5620179,
      "lowTopOfPageBid": 0.571426,
      "highTopOfPageBid": 5.620179
    }
  ]
}
```

### cURL Example

```bash
curl -X POST http://localhost:3002/keyword-research \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

## 🧪 Testing

Run the integration test:

```bash
npm test
```

Or manually:

```bash
source venv/bin/activate
python api/test_keyword_planner.py
```

Expected output:
```
✅ Test passed – 1226 keywords generated
📄 Sheet URL: https://docs.google.com/spreadsheets/d/...
```

## 📁 Project Structure

google-ads-scripts/
├── main.py                        # FastAPI server (46 lines)
├── cli.py                         # Interactive CLI (120 lines)
├── api/
│   ├── keyword_planner.py         # Google Ads API integration (180 lines)
│   ├── sheets_exporter.py         # Google Sheets export (290 lines)
│   ├── clustering.py              # Advanced Clustering Engine (150 lines)
│   ├── run_oauth_and_update_env.py # OAuth helper (108 lines)
│   └── utils.py                   # Utilities (45 lines)
├── public/
│   └── index.html                 # Modern web UI (145 lines)
├── .env                           # Credentials (git-ignored)
└── README.md                      # This file

Total: ~1000 lines of clean, optimized Python code

## ⚙️ Advanced Configuration

### Language Codes

Supported languages (add more in `keyword_planner.py`):
- `en` - English (1000)
- `es` - Spanish (1003)
- `fr` - French (1002)

### Location IDs

Common location IDs:
- `2840` - United States
- `2826` - United Kingdom
- `2036` - Israel
- `2250` - France

[Full list of location IDs](https://developers.google.com/google-ads/api/data/geotargets)

## ⚠️ API Limitations & Best Practices

### Rate Limits

| Service | Limit |
|---------|-------|
| KeywordPlanIdeaService | 1 request/second |
| Daily quota | Check GCP Console |

### Best Practices

1. **Cache results** - Don't request the same URL repeatedly
2. **Respect rate limits** - Wait 1 second between requests
3. **Monitor quota** - Check usage in GCP Console regularly
4. **Handle errors gracefully** - Implement retry logic with exponential backoff
5. **Use specific URLs** - More specific URLs = better keyword suggestions

### Production Deployment

For production use, consider:

- ✅ Add authentication (API keys, OAuth, etc.)
- ✅ Enable HTTPS
- ✅ Implement rate limiting
- ✅ Add request logging
- ✅ Set up monitoring and alerts
- ✅ Use environment-specific configs
- ✅ Deploy to cloud (AWS, GCP, Azure)

## 🔐 Security

- ✅ `.env` is git-ignored (never commit credentials)
- ✅ OAuth tokens are stored securely
- ✅ No hardcoded secrets in code
- ✅ Desktop OAuth client (no web redirect vulnerabilities)
- ⚠️ **For production**: Add authentication layer

## 🐛 Troubleshooting

### "Missing credentials" error

**Cause**: Environment variables not set properly

**Solution**:
```bash
# Check .env file exists and has all required variables
cat .env

# Verify no extra spaces or quotes
```

### "Sheet not created" (no sheetUrl in response)

**Cause**: Refresh token missing Google Sheets scope

**Solution**:
```bash
# Re-run OAuth helper to get new token with both scopes
source venv/bin/activate
python api/run_oauth_and_update_env.py

# Make sure you grant BOTH scopes when authorizing
```

### "Invalid customer ID" error

**Cause**: Using MCC account ID instead of regular account

**Solution**:
```bash
# Check accounts.json exists
cat accounts.json

# Verify you're using a non-MCC account ID
# The tool automatically finds one from accounts.json
```

### Rate limit errors

**Cause**: Too many requests too quickly

**Solution**:
```bash
# Wait at least 1 second between requests
# Check your quota in GCP Console:
# https://console.cloud.google.com/apis/api/googleads.googleapis.com/quotas
```

### Server won't start

**Cause**: Port 3002 already in use

**Solution**:
```bash
# Kill process on port 3002
lsof -ti:3002 | xargs kill -9

# Or change port in server.js:
# const PORT = process.env.PORT || 3003;
```

## 📚 Resources

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [KeywordPlanIdeaService Reference](https://developers.google.com/google-ads/api/reference/rpc/v18/KeywordPlanIdeaService)

## 📝 License

MIT License - feel free to use this for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

- **Issues**: Open an issue on GitHub
- **Google Ads API**: [Official Support](https://developers.google.com/google-ads/api/docs/support)
- **Questions**: Check the troubleshooting section above

---

**Built with ❤️ using Google Ads API and Google Sheets API**

## 🤖 For AI Agents: How to Use the CLI

If a user asks you to run the keyword research for them, you can interact with the CLI programmatically using `send_command_input`.

**Step 1: Start the CLI**
```bash
python cli.py
```

**Step 2: Handle Prompts**
The CLI expects inputs in this order:
1. **URL**: Enter the target URL (e.g., `https://example.com`)
2. **Method**: Enter `1`, `2`, or `3`
   - `1`: Rule-Based (Fast)
   - `2`: ML-Based (Smart)
   - `3`: Hybrid (Recommended)
3. **Export**: Enter `y` or `n` to export to Google Sheets

**Example Workflow:**
1. Run `python cli.py` (Wait for "Enter Website URL")
2. Send Input: `https://www.netflix.com\n`
3. Wait for "Select Clustering Method"
4. Send Input: `3\n`
5. Wait for "Export to Google Sheets?"
6. Send Input: `y\n`

**Note:** Always wait for the prompt before sending input. Use `command_status` to check output.
