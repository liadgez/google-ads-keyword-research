"""
Shared utilities for Google Sheets operations
Centralizes common formatting and creation logic
"""

import sys
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def create_spreadsheet(service, title, sheet_configs):
    """
    Create a new Google Spreadsheet with multiple sheets
    
    Args:
        service: Google Sheets API service instance
        title: Title for the spreadsheet
        sheet_configs: List of sheet configuration dicts with 'title' and optional 'frozen_rows'
    
    Returns:
        dict with 'sheet_id' and 'sheet_url', or None if failed
    """
    try:
        sheets = []
        for config in sheet_configs:
            sheet_props = {
                'properties': {
                    'title': config['title'],
                    'gridProperties': {
                        'frozenRowCount': config.get('frozen_rows', 1)
                    }
                }
            }
            if 'tab_color' in config:
                sheet_props['properties']['tabColor'] = config['tab_color']
            sheets.append(sheet_props)
        
        spreadsheet = {
            'properties': {'title': title},
            'sheets': sheets
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


def get_sheet_id_by_name(service, spreadsheet_id, sheet_name):
    """Get the internal sheet ID for a named sheet tab"""
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        return None
    except Exception as e:
        print(f"Error getting sheet ID: {e}", file=sys.stderr)
        return None


def format_header_row(sheet_id, bg_color=None):
    """
    Create request to format header row (row 0)
    
    Args:
        sheet_id: Internal sheet ID
        bg_color: Dict with 'red', 'green', 'blue' values (0-1), defaults to blue
    
    Returns:
        Request dict for batchUpdate
    """
    if bg_color is None:
        bg_color = {'red': 0.2, 'green': 0.6, 'blue': 0.9}
    
    return {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': bg_color,
                    'textFormat': {
                        'bold': True,
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                    }
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    }


def format_number_column(sheet_id, col_index, num_rows, pattern='#,##0'):
    """Create request to format a column as number"""
    return {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'endRowIndex': num_rows + 1,
                'startColumnIndex': col_index,
                'endColumnIndex': col_index + 1
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'NUMBER',
                        'pattern': pattern
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }


def format_currency_column(sheet_id, col_index, num_rows, pattern='$#,##0.00'):
    """Create request to format a column as currency"""
    return {
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'endRowIndex': num_rows + 1,
                'startColumnIndex': col_index,
                'endColumnIndex': col_index + 1
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': pattern
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }


def auto_resize_columns(sheet_id, start_col=0, end_col=10):
    """Create request to auto-resize columns"""
    return {
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': start_col,
                'endIndex': end_col
            }
        }
    }


def apply_formatting(service, spreadsheet_id, sheet_name, requests):
    """
    Apply a list of formatting requests to a sheet
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: Spreadsheet ID
        sheet_name: Name of sheet tab
        requests: List of request dicts
    
    Returns:
        True if successful
    """
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        print(f"Applied formatting to '{sheet_name}'", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Warning: Failed to format sheet: {e}", file=sys.stderr)
        return False


def set_public_permission(credentials, file_id):
    """Make the file accessible to anyone with the link"""
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        permission = {
            'type': 'anyone',
            'role': 'writer',
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


def write_data_to_sheet(service, spreadsheet_id, sheet_name, data_rows):
    """
    Write data to a sheet
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: Spreadsheet ID
        sheet_name: Name of sheet tab
        data_rows: List of lists (rows of data, including header)
    
    Returns:
        True if successful
    """
    try:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body={'values': data_rows}
        ).execute()
        return True
    except Exception as e:
        print(f"Error writing data: {e}", file=sys.stderr)
        return False


def generate_sheet_title(base_name, url=None):
    """Generate a standardized sheet title with date"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    if url:
        clean_url = url.replace('https://', '').replace('http://', '').split('/')[0]
        if len(clean_url) > 30:
            clean_url = clean_url[:30] + '...'
        return f"{base_name}: {clean_url} - {date_str}"
    return f"{base_name} - {date_str}"
