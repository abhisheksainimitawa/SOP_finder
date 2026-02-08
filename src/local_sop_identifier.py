"""
Local SOP Identifier using Sentence Transformers, FAISS, and BM25
No external API calls - fully offline and lightweight
"""

import json
import os
import re
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss
import warnings
warnings.filterwarnings('ignore')


class LocalSOPIdentifier:
    """
    Lightweight SOP identifier using local models:
    - Sentence Transformers (all-MiniLM-L6-v2) for semantic similarity
    - FAISS for efficient vector search
    - BM25 for keyword-based retrieval
    - Hybrid scoring for robust results
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: str = './models'):
        """
        Initialize the local SOP identifier
        
        Args:
            model_name: Sentence transformer model name
            cache_dir: Directory to cache the model
        """
        print(f"Initializing Local SOP Identifier with {model_name} and FAISS...")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        
        # Load sentence transformer model (small, fast, offline-capable)
        
        self.encoder = SentenceTransformer(model_name, cache_folder=cache_dir)
        self.model_name = model_name
        self.vector_dimension = 384  # all-MiniLM-L6-v2 embedding dimension
        
        # Storage for SOPs
        self.sop_chunks = []
        self.faiss_index = None
        self.bm25 = None
        self.tokenized_corpus = []
        
        print("Model loaded successfully")
    
    def parse_sops(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse SOPs from structured text file into chunks
        
        Args:
            file_path: Path to the structured SOPs text file
            
        Returns:
            List of SOP chunks with metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by the --- separator
        sop_sections = content.split('---')
        
        chunks = []
        
        for section in sop_sections:
            section = section.strip()
            if section and section.startswith('SOP-'):
                # Extract SOP number and title from first line
                lines = section.split('\n')
                first_line = lines[0].strip()
                
                # Parse "SOP-X: Title" format
                if ':' in first_line:
                    sop_part, title = first_line.split(':', 1)
                    sop_number = int(sop_part.replace('SOP-', ''))
                    title = title.strip()
                    
                    chunks.append({
                        'id': f'sop_{sop_number}',
                        'title': f"SOP-{sop_number}: {title}",
                        'content': section,
                        'sop_number': sop_number
                    })
        
        print(f"Parsed {len(chunks)} SOP chunks")
        return chunks
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def build_index(self, sop_file_path: str, save_path: str = './data/sop_index.pkl'):
        """
        Build the search index with FAISS, semantic embeddings and BM25
        
        Args:
            sop_file_path: Path to SOPs file
            save_path: Path to save the index
        """
        print("Building search index with FAISS...")
        
        # Parse SOPs
        self.sop_chunks = self.parse_sops(sop_file_path)
        
        if not self.sop_chunks:
            raise ValueError("No SOP chunks found in the file")
        
        # Extract content for indexing
        corpus = [chunk['content'] for chunk in self.sop_chunks]
        
        # Build semantic embeddings
        print("Generating semantic embeddings...")
        sop_embeddings = self.encoder.encode(
            corpus, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create FAISS index
        print("Building FAISS index...")
        # Use IndexFlatIP for cosine similarity (after normalization)
        self.faiss_index = faiss.IndexFlatIP(self.vector_dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(sop_embeddings)
        
        # Add vectors to FAISS index
        self.faiss_index.add(sop_embeddings)
        
        # Build BM25 index
        print("Building BM25 index...")
        self.tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        # Save index
        print(f"Saving index to {save_path}...")
        index_data = {
            'sop_chunks': self.sop_chunks,
            'tokenized_corpus': self.tokenized_corpus,
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension
        }
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save FAISS index separately
        faiss_index_path = save_path.replace('.pkl', '.faiss')
        faiss.write_index(self.faiss_index, faiss_index_path)
        
        # Save metadata
        with open(save_path, 'wb') as f:
            pickle.dump(index_data, f)
        
        print(f"Index built successfully with {len(self.sop_chunks)} SOPs")
        print(f"FAISS index saved to {faiss_index_path}")
    
    def load_index(self, index_path: str = './data/sop_index.pkl'):
        """
        Load a pre-built index
        
        Args:
            index_path: Path to the saved index
        """
        print(f"Loading index from {index_path}...")
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        # Load metadata
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        self.sop_chunks = index_data['sop_chunks']
        self.tokenized_corpus = index_data['tokenized_corpus']
        self.vector_dimension = index_data.get('vector_dimension', 384)
        
        # Load FAISS index
        faiss_index_path = index_path.replace('.pkl', '.faiss')
        if not os.path.exists(faiss_index_path):
            raise FileNotFoundError(f"FAISS index file not found: {faiss_index_path}")
        
        self.faiss_index = faiss.read_index(faiss_index_path)
        
        # Rebuild BM25 from tokenized corpus
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        print(f"Index loaded successfully with {len(self.sop_chunks)} SOPs")
        print(f"FAISS index: {self.faiss_index.ntotal} vectors")
    
    def retrieve_relevant_sops(
        self, 
        query: str, 
        top_k: int = 5,
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant SOPs using hybrid retrieval (FAISS semantic + BM25)
        
        Args:
            query: Search query
            top_k: Number of top results to return
            semantic_weight: Weight for semantic similarity (0-1)
            bm25_weight: Weight for BM25 score (0-1)
            
        Returns:
            List of relevant SOPs with scores
        """
        if not self.sop_chunks or self.faiss_index is None:
            raise ValueError("Index not built or loaded. Call build_index() or load_index() first.")
        
        print(f"Searching for: {query[:100]}...")
        
        # Generate and normalize query embedding
        query_embedding = self.encoder.encode(query, convert_to_numpy=True)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search FAISS index for semantic similarity
        # Get all documents to compute full ranking
        k = min(len(self.sop_chunks), 100)  # Search more than top_k for better hybrid ranking
        distances, indices = self.faiss_index.search(query_embedding, k)
        
        # FAISS returns distances (inner product after normalization = cosine similarity)
        # Create full semantic scores array
        semantic_scores = np.zeros(len(self.sop_chunks))
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # Valid index
                semantic_scores[idx] = distances[0][i]
        
        # Calculate BM25 scores
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize scores to [0, 1] range
        if semantic_scores.max() > 0:
            semantic_scores_norm = semantic_scores / semantic_scores.max()
        else:
            semantic_scores_norm = semantic_scores
        
        if bm25_scores.max() > 0:
            bm25_scores_norm = bm25_scores / bm25_scores.max()
        else:
            bm25_scores_norm = bm25_scores
        
        # Hybrid scoring
        hybrid_scores = (
            semantic_weight * semantic_scores_norm + 
            bm25_weight * bm25_scores_norm
        )
        
        # Get top-k indices
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        # Prepare results with confidence scores
        results = []
        for idx in top_indices:
            confidence = float(hybrid_scores[idx])
            
            # Determine confidence level
            if confidence >= 0.7:
                confidence_level = "HIGH"
            elif confidence >= 0.4:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"
            
            results.append({
                'id': self.sop_chunks[idx]['id'],
                'title': self.sop_chunks[idx]['title'],
                'sop_number': self.sop_chunks[idx]['sop_number'],
                'confidence_score': round(confidence, 4),
                'confidence_level': confidence_level,
                'semantic_score': round(float(semantic_scores_norm[idx]), 4),
                'bm25_score': round(float(bm25_scores_norm[idx]), 4),
                'content_preview': self.sop_chunks[idx]['content'][:200] + "..."
            })
        
        print(f"Found {len(results)} relevant SOPs using FAISS")
        return results
    
    def select_best_sop(
        self, 
        incident_context: str, 
        top_k: int = 3,
        confidence_threshold: float = 0.4
    ) -> Dict[str, Any]:
        """
        Select the best SOP for an incident with confidence assessment
        
        Args:
            incident_context: Description of the incident
            top_k: Number of candidates to consider
            confidence_threshold: Minimum confidence to accept result
            
        Returns:
            Dictionary with selected SOP and metadata
        """
        # Retrieve relevant SOPs
        relevant_sops = self.retrieve_relevant_sops(
            query=incident_context,
            top_k=top_k
        )
        
        if not relevant_sops:
            return {
                'selected_sop_id': None,
                'selected_sop_title': None,
                'confidence_score': 0.0,
                'confidence_level': 'NONE',
                'recommendation': 'NO_MATCH',
                'reason': 'No relevant SOPs found',
                'retrieved_sops': []
            }
        
        # Best SOP is the top result
        best_sop = relevant_sops[0]
        
        # Determine recommendation based on confidence
        if best_sop['confidence_score'] >= 0.7:
            recommendation = 'ACCEPT'
            reason = f"High confidence match. The incident strongly aligns with {best_sop['title']}."
        elif best_sop['confidence_score'] >= confidence_threshold:
            recommendation = 'REVIEW'
            reason = f"Moderate confidence match. Review {best_sop['title']} to confirm applicability."
        else:
            recommendation = 'REJECT'
            reason = f"Low confidence. The top match ({best_sop['title']}) may not be appropriate. Consider manual review."
        
        return {
            'selected_sop_id': best_sop['id'],
            'selected_sop_number': best_sop['sop_number'],
            'selected_sop_title': best_sop['title'],
            'confidence_score': best_sop['confidence_score'],
            'confidence_level': best_sop['confidence_level'],
            'semantic_score': best_sop['semantic_score'],
            'bm25_score': best_sop['bm25_score'],
            'recommendation': recommendation,
            'reason': reason,
            'retrieved_sops': relevant_sops,
            'alternative_sops': relevant_sops[1:] if len(relevant_sops) > 1 else []
        }
    
    def process_incident(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incident data and select best SOP
        
        Args:
            input_data: Incident data dictionary
            
        Returns:
            SOP selection result
        """
        # Extract incident context
        incident = input_data.get('incident_details', {})
        log_insights = input_data.get('log_insights', {})
        
        context_parts = []
        
        # Basic incident info
        if incident.get('short_description'):
            context_parts.append(f"Issue: {incident['short_description']}")
        if incident.get('description'):
            context_parts.append(f"Description: {incident['description']}")
        
        # Log analysis
        if log_insights.get('full_analysis'):
            context_parts.append(f"Log Summary: {log_insights['full_analysis']}")
        
        incident_context = " | ".join(context_parts)
        
        if not incident_context:
            incident_context = str(input_data)
        
        # Select best SOP
        result = self.select_best_sop(incident_context)
        
        return result
