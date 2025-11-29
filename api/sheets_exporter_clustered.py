"""
Clustered Google Sheets Export
Exports keyword clusters to multiple tabs with overview and negatives
"""

import sys
from datetime import datetime
from googleapiclient.discovery import build
from utils import get_credentials
from sheets_exporter import format_sheet, set_public_permission


def create_and_export_clustered(clusters, url):
    """
    Create a new sheet with clustered ad groups and export to multiple tabs
    
    Args:
        clusters: List of Cluster objects from clustering engine
        url: URL that was analyzed
    
    Returns:
        Sheet URL if successful, None if failed
    """
    try:
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        
        # Create sheet title
        date_str = datetime.now().strftime('%Y-%m-%d')
        clean_url = url.replace('https://', '').replace('http://', '').split('/')[0]
        if len(clean_url) > 30:
            clean_url = clean_url[:30] + '...'
        
        title = f"Ad Groups for {clean_url} - {date_str}"
        
        # Collect all negatives
        all_negatives = []
        seen_negatives = set()
        
        for cluster in clusters:
            for neg in cluster.negative_candidates:
                # neg is now a dict {'keyword': 'foo', 'category': 'bar'}
                if neg['keyword'] not in seen_negatives:
                    all_negatives.append(neg)
                    seen_negatives.add(neg['keyword'])
        
        # Prepare sheets structure - just 2-3 tabs
        sheets_to_create = [
            {
                'properties': {
                    'title': 'All Keywords',
                    'gridProperties': {'frozenRowCount': 1}
                }
            }
        ]
        
        # Add negatives tab if any exist
        if all_negatives:
            sheets_to_create.append({
                'properties': {
                    'title': 'Negative Keywords',
                    'gridProperties': {'frozenRowCount': 1},
                    'tabColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}
                }
            })
        
        # Add overview tab
        sheets_to_create.append({
            'properties': {
                'title': 'Overview',
                'gridProperties': {'frozenRowCount': 1}
            }
        })
        
        # Create spreadsheet
        spreadsheet = {
            'properties': {'title': title},
            'sheets': sheets_to_create
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = result['spreadsheetId']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        
        print(f"Created sheet: {sheet_url}", file=sys.stderr)
        
        # Make it public
        set_public_permission(credentials, sheet_id)
        
        _export_all_keywords_tab(service, sheet_id, clusters)
        _export_overview_tab(service, sheet_id, clusters)
        
        if all_negatives:
            _export_negatives_tab(service, sheet_id, all_negatives)
        
        print(f"Exported {len(clusters)} ad groups to sheet", file=sys.stderr)
        
        return sheet_url
        
    except Exception as e:
        print(f"Error creating clustered sheet: {e}", file=sys.stderr)
        return None


def _export_all_keywords_tab(service, sheet_id, clusters):
    """Export all keywords with Ad Group column"""
    try:
        headers = ['Ad Group', 'Keyword', 'Avg Monthly Searches', 'Competition', 'Competition Index', 'Low Bid ($)', 'High Bid ($)']
        rows = [headers]
        
        # Add all keywords with their ad group name
        for cluster in clusters:
            for kw in cluster.keywords:
                rows.append([
                    cluster.name,
                    kw.get('keyword', ''),
                    kw.get('avgMonthlySearches', 0),
                    kw.get('competition', ''),
                    kw.get('competitionIndex', 0),
                    kw.get('lowTopOfPageBid', 0),
                    kw.get('highTopOfPageBid', 0)
                ])
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='All Keywords!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format the sheet
        _format_keywords_sheet(service, sheet_id, 'All Keywords', len(rows) - 1)
        
        print(f"Exported {len(rows)-1} keywords to 'All Keywords' tab", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to export keywords: {e}", file=sys.stderr)


def _export_overview_tab(service, sheet_id, clusters):
    """Export overview/summary of all clusters"""
    try:
        headers = [
            'Ad Group Name', 
            'Keywords Count', 
            'Total Monthly Searches', 
            'Avg Competition',
            'Volume Tier',
            'Competition Tier',
            'N-gram Pattern'
        ]
        rows = [headers]
        
        for cluster in clusters:
            total_volume = sum(kw.get('avgMonthlySearches', 0) for kw in cluster.keywords)
            avg_comp = sum(kw.get('competitionIndex', 0) for kw in cluster.keywords) / len(cluster.keywords) if cluster.keywords else 0
            
            rows.append([
                cluster.name,
                len(cluster.keywords),
                total_volume,
                round(avg_comp, 1),
                cluster.volume_tier,
                cluster.competition_tier,
                cluster.ngram_group
            ])
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Overview!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        format_sheet(service, sheet_id, 'Overview', len(clusters))
        
    except Exception as e:
        print(f"Warning: Failed to export overview: {e}", file=sys.stderr)


def _format_keywords_sheet(service, sheet_id, sheet_name, num_keywords):
    """Format the All Keywords sheet with Ad Group column"""
    try:
        # Get the actual sheet ID
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        target_sheet_id = None
        
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                target_sheet_id = sheet['properties']['sheetId']
                break
        
        if target_sheet_id is None:
            return
        
        requests = []
        
        # Format header row
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
        
        # Format number columns (C - Avg Monthly Searches)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': target_sheet_id,
                    'startRowIndex': 1,
                    'endRowIndex': num_keywords + 1,
                    'startColumnIndex': 2,
                    'endColumnIndex': 3
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0'}
                    }
                },
                'fields': 'userEnteredFormat.numberFormat'
            }
        })
        
        # Format currency columns (F and G)
        for col in [5, 6]:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': num_keywords + 1,
                        'startColumnIndex': col,
                        'endColumnIndex': col + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'numberFormat': {'type': 'CURRENCY', 'pattern': '$#,##0.00'}
                        }
                    },
                    'fields': 'userEnteredFormat.numberFormat'
                }
            })
        
        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': target_sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 7
                }
            }
        })
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"Applied formatting to sheet '{sheet_name}'", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to format sheet: {e}", file=sys.stderr)


def _export_negatives_tab(service, sheet_id, negatives):
    """Export negative keywords with categories and red highlighting"""
    try:
        headers = ['Negative Keyword', 'Category', 'Reason']
        rows = [headers]
        
        for neg in negatives:
            # neg is dict {'keyword': 'foo', 'category': 'bar'}
            rows.append([
                neg['keyword'], 
                neg['category'],
                f"Matches '{neg['category']}' list"
            ])
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Negative Keywords!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Get sheet ID for formatting
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        neg_sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == 'Negative Keywords':
                neg_sheet_id = sheet['properties']['sheetId']
                break
        
        if neg_sheet_id is not None:
            # Format with red background
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': neg_sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': len(negatives) + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 1.0,
                                'green': 0.8,
                                'blue': 0.8
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            }]
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': requests}
            ).execute()
        
        format_sheet(service, sheet_id, 'Negative Keywords', len(negatives))
        
    except Exception as e:
        print(f"Warning: Failed to export negatives: {e}", file=sys.stderr)


