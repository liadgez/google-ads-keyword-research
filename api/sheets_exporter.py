"""
Google Sheets Exporter
Exports keyword research results to a new Google Sheet
"""

import sys
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import get_credentials

def create_sheet(service, title):
    """
    Create a new Google Sheet
    
    Args:
        service: Google Sheets API service instance
        title: Title for the sheet
    
    Returns:
        dict with sheet_id and sheet_url, or None if failed
    """
    try:
        # Create the spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            },
            'sheets': [{
                'properties': {
                    'title': 'Keyword Research',
                    'gridProperties': {
                        'frozenRowCount': 1  # Freeze header row
                    }
                }
            }]
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        
        sheet_id = result['spreadsheetId']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        
        print(f"Created sheet: {sheet_url}", file=sys.stderr)
        
        return {
            'sheet_id': sheet_id,
            'sheet_url': sheet_url
        }
        
    except HttpError as error:
        print(f"Failed to create sheet: {error}", file=sys.stderr)
        return None
    except Exception as error:
        print(f"Unexpected error creating sheet: {error}", file=sys.stderr)
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
        # Prepare header row
        headers = [
            'Keyword',
            'Avg Monthly Searches',
            'Competition',
            'Competition Index',
            'Low Bid ($)',
            'High Bid ($)'
        ]
        
        # Prepare data rows
        rows = [headers]
        for kw in keywords:
            row = [
                kw.get('keyword', ''),
                kw.get('avgMonthlySearches', 0),
                kw.get('competition', ''),
                kw.get('competitionIndex', 0),
                kw.get('lowTopOfPageBid', 0),
                kw.get('highTopOfPageBid', 0)
            ]
            rows.append(row)
        
        # Write data to sheet
        body = {
            'values': rows
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Keyword Research!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Exported {len(keywords)} keywords to sheet", file=sys.stderr)
        
        # Apply formatting
        format_sheet(service, sheet_id, len(keywords))
        
        return True
        
    except HttpError as error:
        print(f"Failed to export keywords: {error}", file=sys.stderr)
        return False
    except Exception as error:
        print(f"Unexpected error exporting keywords: {error}", file=sys.stderr)
        return False

def format_sheet(service, sheet_id, num_keywords):
    """
    Apply formatting to the sheet
    
    Args:
        service: Google Sheets API service
        sheet_id: ID of the sheet
        num_keywords: Number of keyword rows (for range)
    """
    try:
        requests = []
        
        # Format header row (bold, background color)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.6,
                            'blue': 0.9
                        },
                        'textFormat': {
                            'bold': True,
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            }
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Format number columns (B and D) - add thousand separators
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 1,
                    'endRowIndex': num_keywords + 1,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'NUMBER',
                            'pattern': '#,##0'
                        }
                    }
                },
                'fields': 'userEnteredFormat.numberFormat'
            }
        })
        
        # Format currency columns (E and F)
        for col in [4, 5]:  # Columns E and F
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': num_keywords + 1,
                        'startColumnIndex': col,
                        'endColumnIndex': col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': {
                                'type': 'CURRENCY',
                                'pattern': '$#,##0.00'
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat'
                }
            })
        
        # Auto-resize all columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6
                }
            }
        })
        
        # Execute all formatting requests
        body = {
            'requests': requests
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        
        print("Applied formatting to sheet", file=sys.stderr)
        
    except Exception as error:
        print(f"Warning: Failed to format sheet: {error}", file=sys.stderr)
        # Don't fail if formatting fails - data is already there

def set_public_permission(credentials, file_id):
    """
    Make the file accessible to anyone with the link
    """
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id',
        ).execute()
        
        print("✅ Sheet made public (anyone with link can view)", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Warning: Failed to set public permissions: {e}", file=sys.stderr)
        return False

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
        # Initialize service once
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Create sheet title with URL and date
        date_str = datetime.now().strftime('%Y-%m-%d')
        # Clean URL for title (remove protocol, limit length)
        clean_url = url.replace('https://', '').replace('http://', '').split('/')[0]
        if len(clean_url) > 30:
            clean_url = clean_url[:30] + '...'
        
        title = f"Keywords for {clean_url} - {date_str}"
        
        # Create the sheet
        sheet_info = create_sheet(service, title)
        if not sheet_info:
            return None
            
        # Make it public
        set_public_permission(credentials, sheet_info['sheet_id'])
        
        # Export keywords
        success = export_keywords(service, sheet_info['sheet_id'], keywords)
        if not success:
            return None
        
        return sheet_info['sheet_url']
        
    except Exception as e:
        print(f"Error initializing Sheets service: {e}", file=sys.stderr)
        return None

