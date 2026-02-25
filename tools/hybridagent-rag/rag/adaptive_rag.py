"""
Adaptive RAG System with Vector Database
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional
from collections import defaultdict


class AdaptiveRAG:
    """
    Adaptive Retrieval-Augmented Generation system
    Uses vector similarity to find relevant historical resolutions
    """
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.documents = []
        self.embeddings = []
        self.index_built = False
        
    def add_document(self, document: Dict[str, Any]):
        """
        Add a document to the knowledge base
        
        Args:
            document: {
                'snippet_id': str,
                'imports': List[str],
                'python_version': str,
                'packages': Dict[str, str],
                'success': bool,
                ...
            }
        """
        self.documents.append(document)
        
        # Generate embedding
        if self.embedding_model:
            text = self._document_to_text(document)
            embedding = self.embedding_model.encode(text)
            self.embeddings.append(embedding)
        
        self.index_built = False
    
    def build_index(self):
        """
        Build search index from documents
        """
        if self.embeddings:
            self.embeddings = np.array(self.embeddings)
            self.index_built = True
    
    def retrieve(
        self,
        query: Dict[str, Any],
        top_k: int = 10,
        filter_success: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents
        
        Args:
            query: {
                'imports': List[str],
                'python_version': str,
                'features': List[str]
            }
            top_k: Number of results to return
            filter_success: Only return successful resolutions
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self.documents:
            return []
        
        # Simple retrieval based on import overlap
        query_imports = set(query.get('imports', []))
        
        results = []
        for doc in self.documents:
            # Filter by success if requested
            if filter_success and not doc.get('success', False):
                continue
            
            doc_imports = set(doc.get('imports', []))
            
            # Calculate similarity (Jaccard similarity for imports)
            if query_imports and doc_imports:
                intersection = len(query_imports & doc_imports)
                union = len(query_imports | doc_imports)
                similarity = intersection / union if union > 0 else 0.0
            else:
                similarity = 0.0
            
            # Boost score if Python versions match
            if query.get('python_version') == doc.get('python_version'):
                similarity *= 1.2
            
            results.append({
                **doc,
                'similarity_score': min(1.0, similarity)
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:top_k]
    
    def _document_to_text(self, document: Dict[str, Any]) -> str:
        """
        Convert document to text for embedding
        """
        imports = ', '.join(document.get('imports', []))
        python_version = document.get('python_version', '')
        packages = ', '.join([f"{k}=={v}" for k, v in document.get('packages', {}).items()])
        
        text = f"Python {python_version} imports: {imports} packages: {packages}"
        return text
    
    def load_from_pllm_results(self, pllm_results_path: str):
        """
        Load historical resolutions from PLLM results
        
        Args:
            pllm_results_path: Path to PLLM CSV results file
        """
        try:
            import pandas as pd
            
            df = pd.read_csv(pllm_results_path)
            
            for _, row in df.iterrows():
                # Extract information from PLLM results
                # Adjust column names based on actual CSV structure
                if row.get('success', False):
                    document = {
                        'snippet_id': row.get('snippet_id', ''),
                        'imports': [],  # Would need to parse from snippet
                        'python_version': row.get('python_version', '3.8'),
                        'packages': {},  # Would need to parse from results
                        'success': True,
                        'source': 'pllm'
                    }
                    self.add_document(document)
            
            print(f"Loaded {len(self.documents)} documents from PLLM results")
            
        except Exception as e:
            print(f"Failed to load PLLM results: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get RAG statistics
        """
        total = len(self.documents)
        successful = sum(1 for doc in self.documents if doc.get('success', False))
        
        return {
            'total_documents': total,
            'successful_resolutions': successful,
            'failed_resolutions': total - successful,
            'index_built': self.index_built
        }
