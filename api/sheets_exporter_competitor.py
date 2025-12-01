"""
Competitor Research Google Sheets Export
Exports competitor analysis results to a new Google Sheet
"""

import sys
from googleapiclient.discovery import build
from api.utils import get_credentials
from api.sheets_utils import (
    create_spreadsheet,
    get_sheet_id_by_name,
    format_header_row,
    auto_resize_columns,
    apply_formatting,
    set_public_permission,
    write_data_to_sheet,
    generate_sheet_title
)


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
        title = generate_sheet_title("Competitor Analysis", result.brand_info.brandName)
        
        # Define sheet structure
        sheet_configs = [
            {'title': 'Competitors', 'frozen_rows': 1},
            {'title': 'Market Insight', 'frozen_rows': 1}
        ]
        
        # Create spreadsheet
        sheet_info = create_spreadsheet(service, title, sheet_configs)
        if not sheet_info:
            return None
        
        sheet_id = sheet_info['sheet_id']
        
        # Make it public
        set_public_permission(credentials, sheet_id)
        
        # Export data
        _export_competitors_tab(service, sheet_id, result.competitors)
        _export_insight_tab(service, sheet_id, result)
        
        print(f"Exported {len(result.competitors)} competitors to sheet", file=sys.stderr)
        
        return sheet_info['sheet_url']
        
    except Exception as e:
        print(f"Error creating competitor sheet: {e}", file=sys.stderr)
        return None


def _export_competitors_tab(service, sheet_id, competitors):
    """Export competitors list"""
    try:
        # Prepare data
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
        
        # Write data
        write_data_to_sheet(service, sheet_id, 'Competitors', rows)
        
        # Format
        internal_sheet_id = get_sheet_id_by_name(service, sheet_id, 'Competitors')
        if internal_sheet_id is not None:
            requests = [
                format_header_row(internal_sheet_id),
                auto_resize_columns(internal_sheet_id, 0, 6)
            ]
            apply_formatting(service, sheet_id, 'Competitors', requests)
        
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
        
        # Write data
        write_data_to_sheet(service, sheet_id, 'Market Insight', rows)
        
        # Format
        internal_sheet_id = get_sheet_id_by_name(service, sheet_id, 'Market Insight')
        if internal_sheet_id is not None:
            requests = [
                # Bold headers
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': internal_sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
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
                },
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': internal_sheet_id,
                            'startRowIndex': 5,
                            'endRowIndex': 6,
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
                },
                # Wrap text for insight
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': internal_sheet_id,
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
                },
                # Resize column A
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': internal_sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 1
                        },
                        'properties': {
                            'pixelSize': 600
                        },
                        'fields': 'pixelSize'
                    }
                }
            ]
            apply_formatting(service, sheet_id, 'Market Insight', requests)
        
    except Exception as e:
        print(f"Warning: Failed to export insight: {e}", file=sys.stderr)
