"""
Competitor Research Google Sheets Export
Exports competitor analysis results to a new Google Sheet
"""

import sys
from datetime import datetime
from googleapiclient.discovery import build
from api.utils import get_credentials
from api.sheets_exporter import set_public_permission

def create_and_export_competitor_analysis(result):
    """
    Create a new sheet with competitor analysis results
    
    Args:
        result: AnalysisResult object from CompetitorResearcher
    
    Returns:
        Sheet URL if successful, None if failed
    """
    try:
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Create sheet title
        date_str = datetime.now().strftime('%Y-%m-%d')
        brand_name = result.brand_info.brandName
        title = f"Competitor Analysis: {brand_name} - {date_str}"
        
        # Prepare sheets structure
        sheets_to_create = [
            {
                'properties': {
                    'title': 'Competitors',
                    'gridProperties': {'frozenRowCount': 1}
                }
            },
            {
                'properties': {
                    'title': 'Market Insight',
                    'gridProperties': {'frozenRowCount': 1}
                }
            }
        ]
        
        # Create spreadsheet
        spreadsheet = {
            'properties': {'title': title},
            'sheets': sheets_to_create
        }
        
        result_sheet = service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = result_sheet['spreadsheetId']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        
        print(f"Created sheet: {sheet_url}", file=sys.stderr)
        
        # Make it public
        set_public_permission(credentials, sheet_id)
        
        # Export Data
        _export_competitors_tab(service, sheet_id, result.competitors)
        _export_insight_tab(service, sheet_id, result)
        
        print(f"Exported {len(result.competitors)} competitors to sheet", file=sys.stderr)
        
        return sheet_url
        
    except Exception as e:
        print(f"Error creating competitor sheet: {e}", file=sys.stderr)
        return None


def _export_competitors_tab(service, sheet_id, competitors):
    """Export competitors list"""
    try:
        headers = ['Name', 'Domain', 'Confidence', 'Services', 'Description', 'URL']
        rows = [headers]
        
        for comp in competitors:
            rows.append([
                comp.name,
                comp.domain,
                f"{comp.confidence}%",
                comp.services,
                comp.description,
                comp.url
            ])
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Competitors!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format the sheet
        _format_competitors_sheet(service, sheet_id, 'Competitors', len(rows) - 1)
        
    except Exception as e:
        print(f"Warning: Failed to export competitors: {e}", file=sys.stderr)


def _export_insight_tab(service, sheet_id, result):
    """Export market insight and brand info"""
    try:
        rows = [
            ['Brand Analysis', ''],
            ['Brand Name', result.brand_info.brandName],
            ['Domain', result.brand_info.domain],
            ['Target Keyword', result.selected_keyword],
            ['', ''],
            ['Market Insight', ''],
            [result.market_insight, '']
        ]
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Market Insight!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format Insight Sheet
        _format_insight_sheet(service, sheet_id, 'Market Insight')
        
    except Exception as e:
        print(f"Warning: Failed to export insight: {e}", file=sys.stderr)


def _format_competitors_sheet(service, sheet_id, sheet_name, num_rows):
    """Format the Competitors sheet"""
    try:
        # Get sheet ID
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        target_sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                target_sheet_id = sheet['properties']['sheetId']
                break
        
        if target_sheet_id is None: return
        
        requests = []
        
        # Header formatting
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': target_sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                        'textFormat': {
                            'bold': True,
                            'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': target_sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6
                }
            }
        })
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()
        
    except Exception as e:
        print(f"Warning: Failed to format competitors sheet: {e}", file=sys.stderr)


def _format_insight_sheet(service, sheet_id, sheet_name):
    """Format the Insight sheet"""
    try:
        # Get sheet ID
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        target_sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                target_sheet_id = sheet['properties']['sheetId']
                break
        
        if target_sheet_id is None: return
        
        requests = []
        
        # Bold headers (Rows 1, 6)
        for row_idx in [0, 5]:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True, 'fontSize': 12}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat)'
                }
            })
            
        # Wrap text for insight
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': target_sheet_id,
                    'startRowIndex': 6,
                    'endRowIndex': 7,
                    'startColumnIndex': 0,
                    'endColumnIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'wrapStrategy': 'WRAP'
                    }
                },
                'fields': 'userEnteredFormat.wrapStrategy'
            }
        })
        
        # Resize column A to be wide
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': target_sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 1
                },
                'properties': {
                    'pixelSize': 600
                },
                'fields': 'pixelSize'
            }
        })
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()
        
    except Exception as e:
        print(f"Warning: Failed to format insight sheet: {e}", file=sys.stderr)
