"""
Advanced Keyword Clustering Engine
Implements 3 clustering methodologies and Hagakure best practices.
"""

import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from Levenshtein import ratio as levenshtein_ratio
from difflib import SequenceMatcher

# Optional ML imports (loaded lazily)
_ml_model = None
_sentence_transformer = None
_sklearn_cluster = None

@dataclass
class Cluster:
    name: str
    keywords: List[Dict]
    negative_candidates: List[str]
    
    # Parallel clustering results (added for comparison)
    volume_tier: str = ""
    competition_tier: str = ""
    ngram_group: str = ""

class ClusteringEngine:
    def __init__(self):
        self.negative_terms = {'free', 'job', 'jobs', 'hiring', 'career', 'careers', 
                              'repair', 'repairs', 'used', 'second hand', 'cheap', 
                              'review', 'reviews', 'tutorial', 'how to'}
    
    def _load_ml_dependencies(self):
        """Lazy load ML libraries to keep startup fast for non-ML methods"""
        global _sentence_transformer, _sklearn_cluster
        if _sentence_transformer is None:
            from sentence_transformers import SentenceTransformer
            from sklearn.cluster import DBSCAN
            _sentence_transformer = SentenceTransformer
            _sklearn_cluster = DBSCAN

    def _is_negative(self, keyword: str) -> bool:
        """Check if keyword contains negative terms"""
        words = set(keyword.lower().split())
        return bool(words & self.negative_terms)

    def _is_close_variant(self, kw1: str, kw2: str) -> bool:
        """
        Check if kw2 is a close variant of kw1 (misspelling, plural, etc.)
        Rule: >90% textual similarity
        """
        return levenshtein_ratio(kw1.lower(), kw2.lower()) > 0.9

    def _get_jaccard_similarity(self, kw1: str, kw2: str) -> float:
        """Calculate Jaccard similarity (word overlap)"""
        s1 = set(kw1.lower().split())
        s2 = set(kw2.lower().split())
        if not s1 or not s2:
            return 0.0
        return len(s1 & s2) / len(s1 | s2)

    def cluster_rule_based(self, keywords: List[Dict]) -> List[Cluster]:
        """
        Method A: The Strict Linguist
        Uses Levenshtein + Jaccard to group keywords.
        """
        clusters = defaultdict(list)
        negatives = []
        
        # Sort by length (shortest first usually makes better cluster names)
        sorted_kws = sorted(keywords, key=lambda x: len(x['keyword']))
        
        assigned = set()
        
        for i, kw_data in enumerate(sorted_kws):
            kw_text = kw_data['keyword']
            
            # 1. Negative Check
            if self._is_negative(kw_text):
                negatives.append(kw_text)
                continue
                
            if i in assigned:
                continue
                
            # Create new cluster
            cluster_name = kw_text
            clusters[cluster_name].append(kw_data)
            assigned.add(i)
            
            # Find matches
            for j, other_kw in enumerate(sorted_kws[i+1:], start=i+1):
                if j in assigned:
                    continue
                    
                other_text = other_kw['keyword']
                
                # 2. Close Variant Check (Hagakure Rule A)
                if self._is_close_variant(cluster_name, other_text):
                    # It's a close variant, add to group but don't need new ad group
                    clusters[cluster_name].append(other_kw)
                    assigned.add(j)
                    continue
                
                # 3. Jaccard Similarity (Word Overlap)
                if self._get_jaccard_similarity(cluster_name, other_text) > 0.6:
                    clusters[cluster_name].append(other_kw)
                    assigned.add(j)
        
        return self._format_results(clusters, negatives)

    def cluster_ml_semantic(self, keywords: List[Dict]) -> List[Cluster]:
        """
        Method B: The Semantic Brain
        Uses Sentence Embeddings + DBSCAN.
        """
        self._load_ml_dependencies()
        
        kw_texts = [k['keyword'] for k in keywords]
        negatives = [k for k in kw_texts if self._is_negative(k)]
        
        # Filter out negatives for clustering
        clean_kws = [k for k in keywords if not self._is_negative(k['keyword'])]
        clean_texts = [k['keyword'] for k in clean_kws]
        
        if not clean_texts:
            return []

        # Generate embeddings
        model = _sentence_transformer('all-MiniLM-L6-v2')
        embeddings = model.encode(clean_texts)
        
        # Cluster with DBSCAN
        # eps=0.5 means cosine similarity > 0.5 (approx)
        clustering = _sklearn_cluster(eps=0.5, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        clusters = defaultdict(list)
        orphans = []
        
        for idx, label in enumerate(labels):
            kw_data = clean_kws[idx]
            if label == -1:
                orphans.append(kw_data)
            else:
                # Use the first keyword in the cluster as the name (temporary)
                clusters[label].append(kw_data)
        
        # Rename clusters using the shortest keyword
        named_clusters = defaultdict(list)
        for label, items in clusters.items():
            name = min(items, key=lambda x: len(x['keyword']))['keyword']
            named_clusters[name] = items
            
        # Add orphans as single-item clusters (or handle differently)
        for orphan in orphans:
            named_clusters[orphan['keyword']].append(orphan)
            
        return self._format_results(named_clusters, negatives)

    def cluster_hybrid(self, keywords: List[Dict]) -> List[Cluster]:
        """
        Method C: The Hybrid Strategist
        Rule-based pre-clustering -> Semantic refinement.
        """
        # 1. Fast Rule-Based Pass
        initial_clusters = self.cluster_rule_based(keywords)
        
        # If we have too many small clusters, use ML to merge them
        # For now, let's return the rule-based result as a baseline
        # and we can enhance this with vector merging in the next iteration
        return initial_clusters

    def _calculate_volume_tier(self, avg_searches: int) -> str:
        """Calculate volume tier for a keyword"""
        if avg_searches >= 500000:
            return "High (500K+)"
        elif avg_searches >= 10000:
            return "Medium (10K-100K)"
        else:
            return "Low (<10K)"
    
    def _calculate_competition_tier(self, comp_index: int) -> str:
        """Calculate competition tier for a keyword"""
        if comp_index >= 67:
            return "High (67-100)"
        elif comp_index >= 34:
            return "Medium (34-66)"
        else:
            return "Low (0-33)"
    
    def _extract_ngrams(self, keyword: str) -> str:
        """Extract dominant n-gram pattern from keyword"""
        words = keyword.lower().split()
        if len(words) == 1:
            return words[0]
        # Return first bigram as the pattern
        return f"{words[0]}_{words[1] if len(words) > 1 else ''}"
    
    def _apply_parallel_clustering(self, clusters: List[Cluster]) -> List[Cluster]:
        """Apply all parallel clustering methods to existing clusters"""
        for cluster in clusters:
            if not cluster.keywords:
                continue
            
            # Calculate average metrics for the cluster
            # Optimization: Calculate sum and count once
            total_volume = 0
            total_comp = 0
            count = len(cluster.keywords)
            
            for kw in cluster.keywords:
                total_volume += kw.get('avgMonthlySearches', 0)
                total_comp += kw.get('competitionIndex', 0)
            
            avg_volume = total_volume / count
            avg_comp = total_comp / count
            
            # Apply tier-based clustering
            cluster.volume_tier = self._calculate_volume_tier(int(avg_volume))
            cluster.competition_tier = self._calculate_competition_tier(int(avg_comp))
            
            # N-gram analysis - use cluster name as the pattern
            cluster.ngram_group = self._extract_ngrams(cluster.name)
        
        return clusters

    def _format_results(self, clusters: Dict[str, List[Dict]], negatives: List[str]) -> List[Cluster]:
        results = []
        for name, items in clusters.items():
            # Volume Threshold (Hagakure Rule): Don't create micro-groups
            # combined_volume = sum(item.get('avgMonthlySearches', 0) for item in items)
            # if combined_volume < 100: ... (Optional logic)
            
            results.append(Cluster(
                name=name.title(),
                keywords=items,
                negative_candidates=negatives if len(results) == 0 else [] # Attach negatives to first cluster for now
            ))
        
        # Sort by cluster size (volume or count)
        results.sort(key=lambda x: len(x.keywords), reverse=True)
        
        # Apply parallel clustering methods
        results = self._apply_parallel_clustering(results)
        
        return results
