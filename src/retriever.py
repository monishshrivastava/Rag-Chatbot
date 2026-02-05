from typing import List, Tuple, Dict
from langdetect import detect
from config import Config
from .vector_store import VectorStore

class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def detect_query_language(self, query: str) -> str:
        """Detect the language of the query"""
        try:
            lang = detect(query)
            if lang == 'ja':
                return 'jp'
            elif lang == 'en':
                return 'en'
            else:
                return 'en'  # Default to English
        except:
            return 'en'
    
    def retrieve(self, query: str, k: int = Config.TOP_K_RESULTS) -> Tuple[List[Dict], str]:
        """Retrieve relevant chunks for a query"""
        # Detect query language
        query_language = self.detect_query_language(query)
        
        # Search for relevant chunks
        results = self.vector_store.search(
            query=query,
            k=k,
            language_filter=query_language  # Filter by detected language
        )
        
        # Extract chunks and scores
        chunks = []
        for chunk, score in results:
            chunk_with_score = chunk.copy()
            chunk_with_score['similarity_score'] = score
            chunks.append(chunk_with_score)
        
        return chunks, query_language
    
    def format_context(self, chunks: List[Dict], language: str) -> str:
        """Format retrieved chunks into context for answer generation"""
        if not chunks:
            if language == 'jp':
                return "関連する情報が見つかりませんでした。"
            else:
                return "No relevant information found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.get('filename', 'Unknown')
            text = chunk.get('text', '')
            score = chunk.get('similarity_score', 0)
            
            context_parts.append(f"[Document {i}: {filename} (Score: {score:.3f})]\n{text}")
        
        return "\n\n".join(context_parts)