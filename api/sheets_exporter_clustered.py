"""
Clustered Google Sheets Export
Exports keyword clusters to multiple tabs with overview and negatives
"""

import sys
from googleapiclient.discovery import build
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
        title = generate_sheet_title("Ad Groups", url)
        
        # Collect all negatives
        all_negatives = []
        seen_negatives = set()
        
        for cluster in clusters:
            for neg in cluster.negative_candidates:
                if neg['keyword'] not in seen_negatives:
                    all_negatives.append(neg)
                    seen_negatives.add(neg['keyword'])
        
        # Define sheet structure
        sheet_configs = [
            {'title': 'All Keywords', 'frozen_rows': 1}
        ]
        
        if all_negatives:
            sheet_configs.append({
                'title': 'Negative Keywords',
                'frozen_rows': 1,
                'tab_color': {'red': 1.0, 'green': 0.0, 'blue': 0.0}
            })
        
        sheet_configs.append({'title': 'Overview', 'frozen_rows': 1})
        
        # Create spreadsheet
        sheet_info = create_spreadsheet(service, title, sheet_configs)
        if not sheet_info:
            return None
        
        sheet_id = sheet_info['sheet_id']
        
        # Make it public
        set_public_permission(credentials, sheet_id)
        
        # Export data
        _export_all_keywords_tab(service, sheet_id, clusters)
        _export_overview_tab(service, sheet_id, clusters)
        
        if all_negatives:
            _export_negatives_tab(service, sheet_id, all_negatives)
        
        print(f"Exported {len(clusters)} ad groups to sheet", file=sys.stderr)
        
        return sheet_info['sheet_url']
        
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
        
        # Write data
        write_data_to_sheet(service, sheet_id, 'All Keywords', rows)
        
        # Format the sheet
        internal_sheet_id = get_sheet_id_by_name(service, sheet_id, 'All Keywords')
        if internal_sheet_id is not None:
            num_keywords = len(rows) - 1
            requests = [
                format_header_row(internal_sheet_id),
                format_number_column(internal_sheet_id, 2, num_keywords),  # Avg Monthly Searches
                format_currency_column(internal_sheet_id, 5, num_keywords),  # Low Bid
                format_currency_column(internal_sheet_id, 6, num_keywords),  # High Bid
                auto_resize_columns(internal_sheet_id, 0, 7)
            ]
            apply_formatting(service, sheet_id, 'All Keywords', requests)
        
        print(f"Exported {len(rows)-1} keywords to 'All Keywords' tab", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to export keywords: {e}", file=sys.stderr)


def _export_overview_tab(service, sheet_id, clusters):
    """Export dynamic Pivot Table overview"""
    try:
        # Get Sheet IDs
        source_sheet_id = get_sheet_id_by_name(service, sheet_id, 'All Keywords')
        target_sheet_id = get_sheet_id_by_name(service, sheet_id, 'Overview')
        
        if source_sheet_id is None or target_sheet_id is None:
            print("Error: Could not find required sheets for Pivot Table", file=sys.stderr)
            return

        # Define Pivot Table
        requests = [{
            'updateCells': {
                'rows': [{
                    'values': [{
                        'pivotTable': {
                            'source': {
                                'sheetId': source_sheet_id,
                                'startRowIndex': 0,
                                'startColumnIndex': 0,
                                'endColumnIndex': 7  # Columns A-G
                            },
                            'rows': [{
                                'sourceColumnOffset': 0,  # Col A: Ad Group
                                'showTotals': True,
                                'sortOrder': 'ASCENDING'
                            }],
                            'values': [
                                {
                                    'summarizeFunction': 'COUNTA',
                                    'sourceColumnOffset': 1,  # Col B: Keyword
                                    'name': 'Keywords Count'
                                },
                                {
                                    'summarizeFunction': 'SUM',
                                    'sourceColumnOffset': 2,  # Col C: Volume
                                    'name': 'Total Volume'
                                },
                                {
                                    'summarizeFunction': 'AVERAGE',
                                    'sourceColumnOffset': 4,  # Col E: Comp Index
                                    'name': 'Avg Competition'
                                },
                                {
                                    'summarizeFunction': 'AVERAGE',
                                    'sourceColumnOffset': 5,  # Col F: Low Bid
                                    'name': 'Avg CPC (Low)'
                                },
                                {
                                    'summarizeFunction': 'AVERAGE',
                                    'sourceColumnOffset': 6,  # Col G: High Bid
                                    'name': 'Avg CPC (High)'
                                }
                            ]
                        }
                    }]
                }],
                'start': {
                    'sheetId': target_sheet_id,
                    'rowIndex': 0,
                    'columnIndex': 0
                },
                'fields': 'pivotTable'
            }
        }]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"Created Pivot Table in 'Overview' tab", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to export pivot table: {e}", file=sys.stderr)


def _export_negatives_tab(service, sheet_id, negatives):
    """Export negative keywords with categories and red highlighting"""
    try:
        headers = ['Negative Keyword', 'Category', 'Reason']
        rows = [headers]
        
        for neg in negatives:
            rows.append([
                neg['keyword'], 
                neg['category'],
                f"Matches '{neg['category']}' list"
            ])
        
        # Write data
        write_data_to_sheet(service, sheet_id, 'Negative Keywords', rows)
        
        # Format with red background
        internal_sheet_id = get_sheet_id_by_name(service, sheet_id, 'Negative Keywords')
        if internal_sheet_id is not None:
            requests = [
                format_header_row(internal_sheet_id),
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': internal_sheet_id,
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
                },
                auto_resize_columns(internal_sheet_id, 0, 3)
            ]
            apply_formatting(service, sheet_id, 'Negative Keywords', requests)
        
    except Exception as e:
        print(f"Warning: Failed to export negatives: {e}", file=sys.stderr)
