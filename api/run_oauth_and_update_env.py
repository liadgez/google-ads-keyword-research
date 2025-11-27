# run_oauth_and_update_env.py
"""Helper script to obtain a new Google OAuth refresh token with both
Google Ads and Google Sheets scopes, and automatically update the project's
`.env` file.

Usage:
    source venv/bin/activate   # ensure virtualenv is active
    python api/run_oauth_and_update_env.py

The script will:
1. Build an OAuth flow using the client ID/secret from your existing `.env`.
2. Request the combined scopes:
   - https://www.googleapis.com/auth/adwords
   - https://www.googleapis.com/auth/spreadsheets
3. Open a browser window automatically for you to grant permissions.
4. Exchange the authorization code for credentials, extract the **refresh token**, 
   and write it back to `.env` (replacing any existing `GOOGLE_ADS_REFRESH_TOKEN`).
5. Print the new token and the path to the updated `.env`.

The script does **not** restart your server; after the token is updated, simply
restart `npm start` to pick up the new credentials.
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "Client ID or Client Secret not found in .env. Please ensure "
        "GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET are set."
    )

# Scopes we need – Ads + Sheets
SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    # Build the OAuth flow using the client config directly (no client_secret.json file needed)
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                # Use explicit localhost redirect URI to avoid "Missing required parameter: redirect_uri" error
                "redirect_uris": ["http://localhost:8080/"],
            }
        },
        scopes=SCOPES,
    )

    # Run a temporary local web server to handle the OAuth redirect automatically
    print("\n=== GOOGLE AUTHORIZATION REQUIRED ===")
    print("A browser window will open – please sign in and grant access.")
    creds = flow.run_local_server(port=8080, prompt="consent")
    refresh_token = creds.refresh_token
    if not refresh_token:
        raise RuntimeError("Failed to obtain a refresh token. Did you grant the requested scopes?")

    # Path to .env (project root)
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        raise FileNotFoundError(f"Could not locate .env at {env_path}")

    # Read current .env content
    with env_path.open("r") as f:
        lines = f.readlines()

    # Replace existing GOOGLE_ADS_REFRESH_TOKEN line if present, otherwise append
    token_line = f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}\n"
    token_replaced = False
    new_lines = []
    for line in lines:
        if line.startswith("GOOGLE_ADS_REFRESH_TOKEN="):
            new_lines.append(token_line)
            token_replaced = True
        else:
            new_lines.append(line)
    if not token_replaced:
        # Ensure file ends with a newline before appending
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(token_line)

    # Write back to .env
    with env_path.open("w") as f:
        f.writelines(new_lines)

    print("\n✅ Refresh token updated successfully!")
    print(f"New token stored in {env_path}")
    print(f"Token value (truncated): {refresh_token[:30]}...")
    print("\nRemember to restart your server (npm start) to use the new token.")

if __name__ == "__main__":
    main()

