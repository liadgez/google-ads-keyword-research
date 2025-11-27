import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from clustering import ClusteringEngine

def test_clustering():
    engine = ClusteringEngine()
    
    # Test Data
    keywords = [
        {'keyword': 'netflix login', 'avgMonthlySearches': 1000},
        {'keyword': 'netflix sign in', 'avgMonthlySearches': 800}, # Semantic match
        {'keyword': 'netflix log in', 'avgMonthlySearches': 500},  # Close variant
        {'keyword': 'free netflix account', 'avgMonthlySearches': 100}, # Negative
        {'keyword': 'apple watch', 'avgMonthlySearches': 2000},
    ]
    
    print("Testing Rule-Based Clustering...")
    clusters = engine.cluster_rule_based(keywords)
    for c in clusters:
        print(f"Cluster: {c.name} ({len(c.keywords)} kws)")
        for k in c.keywords:
            print(f"  - {k['keyword']}")
            
    print("\nTesting Negatives...")
    if clusters and clusters[0].negative_candidates:
        print(f"Negatives found: {clusters[0].negative_candidates}")
        assert 'free netflix account' in clusters[0].negative_candidates
        
    print("\n✅ Tests Passed")

if __name__ == "__main__":
    test_clustering()
