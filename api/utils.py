"""Shared utilities for Google API authentication"""

import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials

from functools import lru_cache

# Load environment variables once
load_dotenv()

@lru_cache(maxsize=1)
def get_credentials():
    """Get Google OAuth credentials from environment variables
    
    Returns:
        Credentials object for Google APIs with both Ads and Sheets scopes
    """
    creds_info = {
        'client_id': os.getenv('GOOGLE_ADS_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_ADS_CLIENT_SECRET'),
        'refresh_token': os.getenv('GOOGLE_ADS_REFRESH_TOKEN'),
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
    
    return Credentials.from_authorized_user_info(
        creds_info,
        scopes=[
            'https://www.googleapis.com/auth/adwords',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )

@lru_cache(maxsize=1)
def load_env_vars():
    """Load Google Ads credentials from environment variables
    
    Returns:
        dict: Dictionary containing all required credentials
    """
    return {
        'developer_token': os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN'),
        'client_id': os.getenv('GOOGLE_ADS_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_ADS_CLIENT_SECRET'),
        'refresh_token': os.getenv('GOOGLE_ADS_REFRESH_TOKEN'),
        'login_customer_id': os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
    }
