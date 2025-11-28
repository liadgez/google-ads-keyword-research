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
        
        # Prepare sheets structure
        sheets_to_create = []
        
        # 1. Overview tab
        sheets_to_create.append({
            'properties': {
                'title': 'Overview',
                'gridProperties': {'frozenRowCount': 1}
            }
        })
        
        # 2. Negatives tab (if any negatives exist)
        all_negatives = []
        for cluster in clusters:
            all_negatives.extend(cluster.negative_candidates)
        
        if all_negatives:
            sheets_to_create.append({
                'properties': {
                    'title': 'Negative Keywords',
                    'gridProperties': {'frozenRowCount': 1},
                    'tabColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}
                }
            })
        
        # 3. Top ad group tabs (limit to 15 to avoid too many tabs)
        top_clusters = clusters[:15]
        for cluster in top_clusters:
            # Sanitize sheet name (max 100 chars, no special chars)
            sheet_name = cluster.name[:50]
            sheets_to_create.append({
                'properties': {
                    'title': sheet_name,
                    'gridProperties': {'frozenRowCount': 1}
                }
            })
        
        # 4. "Other Keywords" tab if there are more clusters
        if len(clusters) > 15:
            sheets_to_create.append({
                'properties': {
                    'title': 'Other Keywords',
                    'gridProperties': {'frozenRowCount': 1}
                }
            })
        
        # Create spreadsheet with all tabs
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
        
        # Export data to each tab
        _export_overview_tab(service, sheet_id, clusters)
        
        if all_negatives:
            _export_negatives_tab(service, sheet_id, list(set(all_negatives)))
        
        for i, cluster in enumerate(top_clusters):
            sheet_name = cluster.name[:50]
            _export_cluster_tab(service, sheet_id, sheet_name, cluster.keywords)
        
        # Export remaining keywords to "Other Keywords" tab
        if len(clusters) > 15:
            other_keywords = []
            for cluster in clusters[15:]:
                other_keywords.extend(cluster.keywords)
            _export_cluster_tab(service, sheet_id, 'Other Keywords', other_keywords)
        
        print(f"Exported {len(clusters)} ad groups to sheet", file=sys.stderr)
        
        return sheet_url
        
    except Exception as e:
        print(f"Error creating clustered sheet: {e}", file=sys.stderr)
        return None


def _export_overview_tab(service, sheet_id, clusters):
    """Export overview/summary of all clusters"""
    try:
        headers = ['Ad Group Name', 'Keywords Count', 'Total Monthly Searches', 'Avg Competition']
        rows = [headers]
        
        for cluster in clusters:
            total_volume = sum(kw.get('avgMonthlySearches', 0) for kw in cluster.keywords)
            avg_comp = sum(kw.get('competitionIndex', 0) for kw in cluster.keywords) / len(cluster.keywords) if cluster.keywords else 0
            
            rows.append([
                cluster.name,
                len(cluster.keywords),
                total_volume,
                round(avg_comp, 1)
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


def _export_negatives_tab(service, sheet_id, negatives):
    """Export negative keywords with red highlighting"""
    try:
        headers = ['Negative Keyword', 'Reason']
        rows = [headers]
        
        for neg in negatives:
            rows.append([neg, 'Contains flagged term'])
        
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


def _export_cluster_tab(service, sheet_id, sheet_name, keywords):
    """Export keywords for a single cluster/ad group"""
    try:
        headers = ['Keyword', 'Avg Monthly Searches', 'Competition', 'Competition Index', 'Low Bid ($)', 'High Bid ($)']
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
        
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        format_sheet(service, sheet_id, sheet_name, len(keywords))
        
    except Exception as e:
        print(f"Warning: Failed to export cluster '{sheet_name}': {e}", file=sys.stderr)
