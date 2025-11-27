"""
Google Ads Keyword Planner - Python Implementation
This script generates keyword ideas from a URL using the Google Ads API.
"""

import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from utils import load_env_vars
from sheets_exporter import create_and_export

# Language code to Google Ads language constant ID mapping
LANGUAGE_MAP = {
    'en': '1000',  # English
    'es': '1003',  # Spanish
    'fr': '1002',  # French
}

# Global cache for the client
_google_ads_client = None

def get_google_ads_client():
    """Get or create cached Google Ads client"""
    global _google_ads_client
    if _google_ads_client:
        return _google_ads_client
        
    creds = load_env_vars()
    
    # Validate credentials
    required = ['developer_token', 'client_id', 'client_secret', 'refresh_token', 'login_customer_id']
    missing = [k for k in required if not creds.get(k)]
    if missing:
        raise ValueError(f"Missing credentials: {', '.join(missing)}")
        
    credentials = {
        'developer_token': creds['developer_token'],
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'login_customer_id': creds['login_customer_id'],
        'use_proto_plus': True
    }
    
    _google_ads_client = GoogleAdsClient.load_from_dict(credentials)
    return _google_ads_client

def generate_keyword_ideas(url, keywords=None, language_code='en', location_ids=None):
    """
    Generate keyword ideas from a URL using Google Ads API
    
    Args:
        url: Website URL to analyze
        keywords: Optional list of seed keywords
        language_code: Language code (e.g., 'en', 'es')
        location_ids: List of location IDs (e.g., ['2840'] for USA)
    
    Returns:
        dict with success status and keyword ideas
    """
    try:
        # Get cached client
        try:
            client = get_google_ads_client()
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
            
        # Get customer ID from cached client config or env
        # We can just get it from load_env_vars() since it's cached now
        creds = load_env_vars()
        
        # Use customer ID from environment
        customer_id = creds['login_customer_id']
        print(f"Using customer ID: {customer_id}", file=sys.stderr)
        
        # Get the KeywordPlanIdeaService
        keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
        
        # Build the request
        request = client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = customer_id
        
        # Set URL seed
        request.url_seed.url = url
        
        # Set keyword plan network (Google Search)
        request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        
        # Optional: Add language
        if language_code:
            language_id = LANGUAGE_MAP.get(language_code, '1000')
            request.language = f"languageConstants/{language_id}"
        
        # Optional: Add location targeting
        if location_ids:
            for location_id in location_ids:
                request.geo_target_constants.append(f"geoTargetConstants/{location_id}")
        
        # Optional: Add keyword seeds
        if keywords:
            request.keyword_seed.keywords.extend(keywords)
        
        print(f"Calling Google Ads API for customer {customer_id}...", file=sys.stderr)
        
        # Make the API call
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
        
        # Parse results using list comprehension for better performance
        keyword_ideas = [
            {
                'keyword': idea.text,
                'avgMonthlySearches': idea.keyword_idea_metrics.avg_monthly_searches or 0,
                'competition': idea.keyword_idea_metrics.competition.name if idea.keyword_idea_metrics.competition else 'UNSPECIFIED',
                'competitionIndex': idea.keyword_idea_metrics.competition_index or 0,
                'lowTopOfPageBidMicros': idea.keyword_idea_metrics.low_top_of_page_bid_micros or 0,
                'highTopOfPageBidMicros': idea.keyword_idea_metrics.high_top_of_page_bid_micros or 0,
                'lowTopOfPageBid': (idea.keyword_idea_metrics.low_top_of_page_bid_micros or 0) / 1000000,
                'highTopOfPageBid': (idea.keyword_idea_metrics.high_top_of_page_bid_micros or 0) / 1000000,
            }
            for idea in response
        ]
        
        print(f"Successfully generated {len(keyword_ideas)} keyword ideas", file=sys.stderr)
        
        # Try to export to Google Sheets
        sheet_url = None
        try:
            print("Attempting to create Google Sheet...", file=sys.stderr)
            sheet_url = create_and_export(keyword_ideas, url)
            if sheet_url:
                print(f"Sheet created successfully: {sheet_url}", file=sys.stderr)
            else:
                print("Failed to create sheet (continuing without it)", file=sys.stderr)
        except Exception as sheet_error:
            print(f"Warning: Could not create sheet: {sheet_error}", file=sys.stderr)
            # Continue without sheet - don't fail the whole request
        
        result = {
            'success': True,
            'url': url,
            'totalResults': len(keyword_ideas),
            'keywords': keyword_ideas
        }
        
        # Add sheet URL if available
        if sheet_url:
            result['sheetUrl'] = sheet_url
        
        return result
        
    except GoogleAdsException as ex:
        error_msg = f"Google Ads API error: {ex.error.code().name}"
        for error in ex.failure.errors:
            error_msg += f"\n  - {error.message}"
        
        print(f"Error: {error_msg}", file=sys.stderr)
        return {
            'success': False,
            'error': error_msg,
            'url': url
        }
    
    except Exception as ex:
        error_msg = str(ex)
        print(f"Error: {error_msg}", file=sys.stderr)
        return {
            'success': False,
            'error': error_msg,
            'url': url
        }


