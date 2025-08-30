from __future__ import annotations
import json
import os
import threading
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from rag.embeddings import BGEM3DenseEmbeddings


class SemanticCache:
    """
    Semantic cache that stores query-response pairs and retrieves based on embedding similarity.
    If a new query has >0.95 cosine similarity to a cached query, returns cached response.
    """
    
    def __init__(self, cache_file: str = "semantic_cache.json", similarity_threshold: float = 0.95, max_cache_size: int = 1000):
        self.cache_file = cache_file
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.lock = threading.Lock()
        self.embedder = BGEM3DenseEmbeddings()
        
        # Cache structure: List[Dict] with keys: query, query_embedding, response, timestamp
        self.cache = self._load_cache()
    
    def _load_cache(self) -> List[Dict[str, Any]]:
        """Load cache from disk if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
    
    def _save_cache(self):
        """Save cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _cleanup_old_entries(self):
        """Remove oldest entries if cache exceeds max size."""
        if len(self.cache) > self.max_cache_size:
            # Sort by timestamp and keep the most recent entries
            self.cache.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            self.cache = self.cache[:self.max_cache_size]
    
    def get(self, query: str) -> Optional[Any]:
        """
        Retrieve cached response if query is similar to a cached query.
        
        Args:
            query: The query text to search for
            
        Returns:
            Cached response if similarity > threshold, None otherwise
        """
        with self.lock:
            if not self.cache:
                return None
            
            # Get embedding for the query
            query_embedding = self.embedder.embed_query(query)
            
            # Find most similar cached query
            best_similarity = 0.0
            best_response = None
            
            for cache_entry in self.cache:
                if 'query_embedding' not in cache_entry:
                    continue
                
                similarity = self._cosine_similarity(query_embedding, cache_entry['query_embedding'])
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_response = cache_entry.get('response')
            
            # Return cached response if similarity exceeds threshold
            if best_similarity >= self.similarity_threshold:
                return best_response
            
            return None
    
    def set(self, query: str, response: Any):
        """
        Cache a query-response pair.
        
        Args:
            query: The query text
            response: The response to cache
        """
        with self.lock:
            # Get embedding for the query
            query_embedding = self.embedder.embed_query(query)
            
            # Create cache entry
            cache_entry = {
                'query': query,
                'query_embedding': query_embedding,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to cache
            self.cache.append(cache_entry)
            
            # Cleanup old entries if needed
            self._cleanup_old_entries()
            
            # Save to disk
            self._save_cache()
    
    def clear(self):
        """Clear the entire cache."""
        with self.lock:
            self.cache = []
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'total_entries': len(self.cache),
                'cache_file': self.cache_file,
                'similarity_threshold': self.similarity_threshold,
                'max_cache_size': self.max_cache_size
            }


# Global semantic cache instance
_semantic_cache = None
_cache_lock = threading.Lock()


def get_semantic_cache(cache_file: str = "semantic_cache.json", 
                      similarity_threshold: float = 0.95, 
                      max_cache_size: int = 1000) -> SemanticCache:
    """Get or create the global semantic cache instance."""
    global _semantic_cache
    
    with _cache_lock:
        if _semantic_cache is None:
            _semantic_cache = SemanticCache(
                cache_file=cache_file,
                similarity_threshold=similarity_threshold,
                max_cache_size=max_cache_size
            )
        return _semantic_cache