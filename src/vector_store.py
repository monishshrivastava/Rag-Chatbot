import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from config import Config

class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index = None
        self.chunks = []
        self.dimension = 384  # Dimension for the multilingual model
        
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def build_index(self, chunks: List[Dict]):
        """Build FAISS index from chunks"""
        if not chunks:
            print("No chunks to index")
            return
        
        print(f"Building index for {len(chunks)} chunks...")
        
        # Extract texts for embedding
        texts = [chunk['text'] for chunk in chunks]
        
        # Create embeddings
        embeddings = self.create_embeddings(texts)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        # Store chunks for retrieval
        self.chunks = chunks
        
        print(f"Index built successfully with {self.index.ntotal} vectors")
    
    def save_index(self, index_path: str = None):
        """Save the FAISS index and chunks to disk"""
        if index_path is None:
            index_path = Config.VECTOR_DB_DIR
        
        if self.index is None:
            print("No index to save")
            return
        
        # Save FAISS index
        faiss_path = os.path.join(index_path, "faiss_index.bin")
        faiss.write_index(self.index, faiss_path)
        
        # Save chunks metadata
        chunks_path = os.path.join(index_path, "chunks.pkl")
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        print(f"Index saved to {index_path}")
    
    def load_index(self, index_path: str = None):
        """Load the FAISS index and chunks from disk"""
        if index_path is None:
            index_path = Config.VECTOR_DB_DIR
        
        faiss_path = os.path.join(index_path, "faiss_index.bin")
        chunks_path = os.path.join(index_path, "chunks.pkl")
        
        if not os.path.exists(faiss_path) or not os.path.exists(chunks_path):
            print("Index files not found")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(faiss_path)
            
            # Load chunks
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            
            print(f"Index loaded successfully with {len(self.chunks)} chunks")
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def search(self, query: str, k: int = Config.TOP_K_RESULTS, language_filter: str = None) -> List[Tuple[Dict, float]]:
        """Search for similar chunks"""
        if self.index is None:
            print("Index not built or loaded")
            return []
        
        # Create query embedding
        query_embedding = self.create_embeddings([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k * 2)  # Get more results for filtering
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                
                # Apply language filter if specified
                if language_filter and chunk['language'] != language_filter:
                    continue
                
                results.append((chunk, float(score)))
                
                if len(results) >= k:
                    break
        
        return results