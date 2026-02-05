import os
from typing import List, Dict, Optional
from config import Config
from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .retriever import Retriever

# Groq integration for enhanced responses
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class BilingualIRChatbot:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.retriever = Retriever(self.vector_store)
        self.groq_client = None
        
        # Initialize Groq if API key is available
        if GROQ_AVAILABLE and Config.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
                print("✅ Groq API initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize Groq API: {e}")
                self.groq_client = None
    
    def initialize(self, rebuild_index: bool = False):
        """Initialize the chatbot by loading or building the vector index"""
        Config.create_directories()
        
        # Try to load existing index
        if not rebuild_index and self.vector_store.load_index():
            print("Loaded existing vector index")
            return True
        
        # Build new index from documents
        print("Building new vector index...")
        chunks = self.document_processor.process_directory(Config.DOCUMENTS_DIR)
        
        if not chunks:
            print("No documents found to process. Please add documents to the data/documents/ directory.")
            return False
        
        self.vector_store.build_index(chunks)
        self.vector_store.save_index()
        return True
    
    def add_document(self, file_path: str):
        """Add a new document to the knowledge base"""
        chunks = self.document_processor.process_document(file_path)
        if chunks:
            # For simplicity, rebuild the entire index
            # In production, you'd want incremental updates
            all_chunks = self.vector_store.chunks + chunks
            self.vector_store.build_index(all_chunks)
            self.vector_store.save_index()
            print(f"Added document: {os.path.basename(file_path)}")
        else:
            print(f"Failed to process document: {file_path}")
    
    def generate_simple_answer(self, query: str, context: str, language: str) -> str:
        """Generate a simple answer by returning the most relevant context"""
        if not context or "No relevant information found" in context or "関連する情報が見つかりませんでした" in context:
            if language == 'jp':
                return "申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。別の質問をお試しください。"
            else:
                return "I'm sorry, but I couldn't find relevant information for your question. Please try asking something else."
        
        # Simple answer: return the context with a header
        if language == 'jp':
            return f"以下の情報が見つかりました：\n\n{context}"
        else:
            return f"Here's the relevant information I found:\n\n{context}"
    
    def generate_enhanced_answer(self, query: str, context: str, language: str) -> str:
        """Generate an enhanced answer using Groq API"""
        if not self.groq_client:
            return self.generate_simple_answer(query, context, language)
        
        try:
            if language == 'jp':
                system_prompt = """あなたは投資家向け情報に特化したAIアシスタントです。
提供された文書の内容に基づいて、正確で有用な回答を日本語で提供してください。
以下のガイドラインに従ってください：
1. 文書に含まれている情報のみを使用してください
2. 推測や憶測は避けてください
3. 文書に情報がない場合は「提供された情報では確認できません」と明記してください
4. 回答は簡潔で分かりやすくしてください
5. 必要に応じて数値や具体的なデータを引用してください"""
                
                user_prompt = f"""質問: {query}

関連文書の内容:
{context}

上記の文書内容に基づいて、質問に対する回答を日本語で提供してください。"""
            else:
                system_prompt = """You are an AI assistant specialized in investor relations information.
Provide accurate and helpful answers based strictly on the provided document content.
Follow these guidelines:
1. Only use information contained in the provided documents
2. Do not speculate or make assumptions beyond the given information
3. If information is not available in the documents, clearly state "This information is not available in the provided documents"
4. Keep responses concise and clear
5. Quote specific numbers or data when relevant"""
                
                user_prompt = f"""Question: {query}

Relevant document content:
{context}

Based on the above document content, please provide a comprehensive answer to the question."""
            
            # Create chat completion using Groq
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=Config.GROQ_MODEL,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for factual responses
                top_p=0.9
            )
            
            return chat_completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating enhanced answer with Groq: {e}")
            return self.generate_simple_answer(query, context, language)
    
    def answer_question(self, query: str, use_llm: bool = False) -> Dict:
        """Answer a user question"""
        if not query.strip():
            return {
                'answer': 'Please provide a valid question.',
                'language': 'en',
                'sources': [],
                'method': 'error'
            }
        
        # Retrieve relevant chunks
        chunks, language = self.retriever.retrieve(query)
        
        # Format context
        context = self.retriever.format_context(chunks, language)
        
        # Generate answer
        if use_llm and self.groq_client:
            answer = self.generate_enhanced_answer(query, context, language)
            method = 'groq_enhanced'
        else:
            answer = self.generate_simple_answer(query, context, language)
            method = 'simple_retrieval'
        
        # Prepare sources
        sources = []
        for chunk in chunks:
            sources.append({
                'filename': chunk.get('filename', 'Unknown'),
                'score': chunk.get('similarity_score', 0),
                'text_preview': chunk.get('text', '')[:200] + '...' if len(chunk.get('text', '')) > 200 else chunk.get('text', '')
            })
        
        return {
            'answer': answer,
            'language': language,
            'sources': sources,
            'method': method,
            'model_used': Config.GROQ_MODEL if method == 'groq_enhanced' else 'retrieval_only'
        }
    
    def get_stats(self) -> Dict:
        """Get chatbot statistics"""
        if not self.vector_store.chunks:
            return {'total_chunks': 0, 'languages': {}, 'documents': {}}
        
        stats = {
            'total_chunks': len(self.vector_store.chunks),
            'languages': {},
            'documents': {},
            'groq_available': self.groq_client is not None,
            'groq_model': Config.GROQ_MODEL if self.groq_client else None
        }
        
        for chunk in self.vector_store.chunks:
            lang = chunk.get('language', 'unknown')
            filename = chunk.get('filename', 'unknown')
            
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            stats['documents'][filename] = stats['documents'].get(filename, 0) + 1
        
        return stats
    
    def test_groq_connection(self) -> bool:
        """Test Groq API connection"""
        if not self.groq_client:
            return False
        
        try:
            # Simple test query
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello, please respond with 'Connection successful'"}],
                model=Config.GROQ_MODEL,
                max_tokens=10
            )
            return "successful" in response.choices[0].message.content.lower()
        except Exception as e:
            print(f"Groq connection test failed: {e}")
            return False