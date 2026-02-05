import os
import re
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("PyMuPDF not available, using pdfplumber only")

import pdfplumber
from typing import List, Dict, Tuple
from langdetect import detect
from config import Config

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using available libraries"""
        text = ""
        
        # Try PyMuPDF first if available
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                print(f"PyMuPDF failed for {file_path}: {e}, trying pdfplumber...")
        
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try different encodings
            try:
                with open(file_path, 'r', encoding='cp1252') as file:
                    return file.read()
            except Exception as e:
                print(f"Error reading text file {file_path} with cp1252: {e}")
                return ""
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            # Take a sample of text for language detection (first 1000 chars)
            sample_text = text[:1000] if len(text) > 1000 else text
            lang = detect(sample_text)
            # Map detected language to our supported languages
            if lang == 'ja':
                return 'jp'
            elif lang == 'en':
                return 'en'
            else:
                # Default to English for unknown languages
                return 'en'
        except Exception as e:
            print(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Japanese characters and basic punctuation
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBF.,!?;:()\-]', ' ', text)
        return text.strip()
    
    def chunk_text(self, text: str, language: str) -> List[str]:
        """Split text into chunks"""
        # Clean text first
        text = self.clean_text(text)
        
        if not text.strip():
            return []
        
        # For Japanese, split by sentences (。) and paragraphs
        if language == 'jp':
            sentences = re.split(r'[。\n]', text)
        else:
            sentences = re.split(r'[.!?\n]', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Filter very short chunks
        return [chunk for chunk in chunks if len(chunk.strip()) > 20]
    
    def process_document(self, file_path: str) -> List[Dict]:
        """Process a document and return chunks with metadata"""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        print(f"Processing: {filename} (type: {file_ext})")
        
        # Extract text based on file type - THIS WAS THE BUG!
        text = ""
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.txt', '.md']:
            text = self.extract_text_from_txt(file_path)  # Fixed: was calling extract_text_from_pdf
        else:
            print(f"Unsupported file type: {file_ext}")
            return []
        
        if not text.strip():
            print(f"No text extracted from {filename}")
            return []
        
        print(f"Extracted {len(text)} characters from {filename}")
        
        # Detect language
        language = self.detect_language(text)
        
        # Chunk text
        chunks = self.chunk_text(text, language)
        
        if not chunks:
            print(f"No valid chunks created from {filename}")
            return []
        
        # Create chunk objects with metadata
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                'text': chunk,
                'filename': filename,
                'language': language,
                'chunk_id': i,
                'file_path': file_path
            })
        
        print(f"Processed {filename}: {len(chunks)} chunks, language: {language}")
        return processed_chunks
    
    def process_directory(self, directory_path: str) -> List[Dict]:
        """Process all documents in a directory"""
        all_chunks = []
        
        if not os.path.exists(directory_path):
            print(f"Directory does not exist: {directory_path}")
            return all_chunks
        
        print(f"Scanning directory: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.pdf', '.txt', '.md')):
                    file_path = os.path.join(root, file)
                    try:
                        chunks = self.process_document(file_path)
                        all_chunks.extend(chunks)
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                        continue
        
        print(f"Total chunks processed: {len(all_chunks)}")
        return all_chunks