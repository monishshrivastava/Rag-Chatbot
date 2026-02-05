import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Directories
    DATA_DIR = "data"
    DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
    VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
    MODELS_DIR = "models"
    
    # Model configurations
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Chunk settings
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Retrieval settings
    TOP_K_RESULTS = 3
    
    # Groq API configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = "mixtral-8x7b-32768"  # Free model with good multilingual support
    # Alternative models: "llama2-70b-4096", "gemma-7b-it"
    
    # Supported languages
    SUPPORTED_LANGUAGES = ["en", "ja"]
    
    # Create directories if they don't exist
    @classmethod
    def create_directories(cls):
        os.makedirs(cls.DOCUMENTS_DIR, exist_ok=True)
        os.makedirs(os.path.join(cls.DOCUMENTS_DIR, "en"), exist_ok=True)
        os.makedirs(os.path.join(cls.DOCUMENTS_DIR, "jp"), exist_ok=True)
        os.makedirs(cls.VECTOR_DB_DIR, exist_ok=True)
        os.makedirs(cls.MODELS_DIR, exist_ok=True)