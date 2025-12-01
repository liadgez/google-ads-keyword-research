"""
Google Sheets Exporter
Exports keyword research results to a new Google Sheet
"""

import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from api.utils import get_credentials
from api.sheets_utils import (
    create_spreadsheet,
    get_sheet_id_by_name,
    format_header_row,
    format_number_column,
    format_currency_column,
    auto_resize_columns,
    apply_formatting,
    set_public_permission,
    write_data_to_sheet,
    generate_sheet_title
)


def create_and_export(keywords, url):
    """
    Create a new sheet and export keywords to it
    
    Args:
        keywords: List of keyword dictionaries
        url: URL that was analyzed
    
    Returns:
        Sheet URL if successful, None if failed
    """
    try:
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Create sheet title
        title = generate_sheet_title("Keywords", url)
        
        # Define sheet structure
        sheet_configs = [
            {'title': 'Keyword Research', 'frozen_rows': 1}
        ]
        
        # Create spreadsheet
        sheet_info = create_spreadsheet(service, title, sheet_configs)
        if not sheet_info:
            return None
        
        sheet_id = sheet_info['sheet_id']
        
        # Make it public
        set_public_permission(credentials, sheet_id)
        
        # Export keywords
        success = export_keywords(service, sheet_id, keywords)
        if not success:
            return None
        
        return sheet_info['sheet_url']
        
    except Exception as e:
        print(f"Error initializing Sheets service: {e}", file=sys.stderr)
        return None


def export_keywords(service, sheet_id, keywords):
    """
    Export keyword data to the Google Sheet
    
    Args:
        service: Google Sheets API service instance
        sheet_id: ID of the sheet to write to
        keywords: List of keyword dictionaries
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare data
        headers = [
            'Keyword',
            'Avg Monthly Searches',
            'Competition',
            'Competition Index',
            'Low Bid ($)',
            'High Bid ($)'
        ]
        
        rows = [headers]
        for kw in keywords:
            rows.append([
                kw.get('keyword', ''),
                kw.get('avgMonthlySearches', 0),
                kw.get('competition', ''),
                kw.get('competitionIndex', 0),
                kw.get('lowTopOfPageBid', 0),
                kw.get('highTopOfPageBid', 0)
            ])
        
        # Write data
        write_data_to_sheet(service, sheet_id, 'Keyword Research', rows)
        
        # Apply formatting
        internal_sheet_id = get_sheet_id_by_name(service, sheet_id, 'Keyword Research')
        if internal_sheet_id is not None:
            num_keywords = len(keywords)
            requests = [
                format_header_row(internal_sheet_id),
                format_number_column(internal_sheet_id, 1, num_keywords),  # Avg Monthly Searches
                format_currency_column(internal_sheet_id, 4, num_keywords),  # Low Bid
                format_currency_column(internal_sheet_id, 5, num_keywords),  # High Bid
                auto_resize_columns(internal_sheet_id, 0, 6)
            ]
            apply_formatting(service, sheet_id, 'Keyword Research', requests)
        
        print(f"Exported {len(keywords)} keywords to sheet", file=sys.stderr)
        return True
        
    except HttpError as error:
        print(f"Failed to export keywords: {error}", file=sys.stderr)
        return False
    except Exception as error:
        print(f"Unexpected error exporting keywords: {error}", file=sys.stderr)
        return False


# Legacy function for backward compatibility
def format_sheet(service, sheet_id, sheet_name, num_keywords):
    """
    Legacy format_sheet function for backward compatibility
    Redirects to new utilities
    """
    internal_sheet_id = get_sheet_id_by_name(service, sheet_id, sheet_name)
    if internal_sheet_id is not None:
        requests = [
            format_header_row(internal_sheet_id),
            auto_resize_columns(internal_sheet_id, 0, 6)
        ]
        apply_formatting(service, sheet_id, sheet_name, requests)
