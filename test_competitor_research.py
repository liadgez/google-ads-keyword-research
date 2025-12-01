#!/usr/bin/env python3
"""
Test script for competitor research functionality.
"""

import asyncio
import sys
import os

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from competitor_research import CompetitorResearcher

async def test_competitor_research():
    """Test the competitor research module."""
    print("🧪 Testing Competitor Research Module\n")
    
    # Test URL
    test_url = "https://www.netflix.com"
    
    print(f"Testing with URL: {test_url}")
    print("Method: gemini\n")
    
    try:
        researcher = CompetitorResearcher()
        result = await researcher.analyze(test_url, method='gemini')
        
        print("✅ Analysis completed successfully!\n")
        print(f"Brand: {result.brand_info.brandName}")
        print(f"Domain: {result.brand_info.domain}")
        print(f"Selected Keyword: {result.selected_keyword}")
        print(f"Competitors Found: {len(result.competitors)}")
        print(f"Citations: {len(result.citations)}")
        
        if result.competitors:
            print("\nTop 3 Competitors:")
            for i, comp in enumerate(result.competitors[:3], 1):
                print(f"  {i}. {comp.name} ({comp.domain}) - Confidence: {comp.confidence}%")
        
        if result.market_insight:
            print(f"\nMarket Insight: {result.market_insight[:200]}...")
        
        # Test export
        print("\n📂 Testing export...")
        output_path = researcher.export(result, format='json')
        print(f"✅ Exported to: {output_path}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_competitor_research())
    sys.exit(0 if success else 1)
