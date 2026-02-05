#!/usr/bin/env python3
import os
import sys
from src.chatbot import BilingualIRChatbot
from config import Config

def print_welcome():
    print("Supported languages: English (EN) / Japanese (JP)")
    print("Commands:")
    print("  /help    - Show this help message")
    print("  /stats   - Show knowledge base statistics")
    print("  /add     - Add a new document")
    print("  /rebuild - Rebuild the vector index")
    print("  /test    - Test Groq API connection")
    print("  /quit    - Exit the chatbot")
    print("=" * 60)

def print_help():
    print("• Ask questions in English or Japanese")
    print("• The bot will automatically detect your language")
    print("• Questions should be related to investor relations")
    print("• Use /add <file_path> to add new documents")
    print("• Use /stats to see knowledge base information")
    print("• Enhanced responses powered by Groq's Mixtral model")

def main():
    # Initialize chatbot
    chatbot = BilingualIRChatbot()
    
    print_welcome()
    
    # Test Groq connection if available
    if chatbot.groq_client:
        print("Testing Groq API connection...")
        if chatbot.test_groq_connection():
            print(" Groq API connection successful!")
        else:
            print(" Groq API connection failed. Enhanced responses will be unavailable.")
    else:
        print(" Groq API not configured. Only basic retrieval responses available.")
        print(" Add GROQ_API_KEY to .env file for enhanced responses.")
    
    # Initialize the knowledge base
    print("\nInitializing knowledge base...")
    if not chatbot.initialize():
        print(" Failed to initialize. Please check if documents exist in data/documents/")
        print(" Add PDF or TXT files to:")
        print(f"   - {os.path.join(Config.DOCUMENTS_DIR, 'en')} (for English documents)")
        print(f"   - {os.path.join(Config.DOCUMENTS_DIR, 'jp')} (for Japanese documents)")
        return
    
    print("Chatbot initialized successfully!")
    print("\nYou can now ask questions. Type /help for more information.\n")
    
    # Main chat loop
    while True:
        try:
            user_input = input(" You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command == '/quit' or command == '/exit':
                    print("Goodbye!")  # Fixed escape sequence
                    break
                
                elif command == '/help':
                    print_help()
                    continue
                
                elif command == '/test':
                    if chatbot.groq_client:
                        print("Testing Groq API...")
                        if chatbot.test_groq_connection():
                            print("Groq API is working correctly!")
                        else:
                            print("Groq API test failed.")
                    else:
                        print(" Groq API not configured.")
                    continue
                
                elif command == '/stats':
                    stats = chatbot.get_stats()
                    print(f"\nKnowledge Base Statistics:")
                    print(f"   Total chunks: {stats['total_chunks']}")
                    print(f"   Languages: {dict(stats['languages'])}")
                    print(f"   Documents: {len(stats['documents'])}")
                    print(f"   Groq API: {'Available' if stats['groq_available'] else 'Not available'}")
                    if stats['groq_model']:
                        print(f"   Groq Model: {stats['groq_model']}")
                    
                    for doc, count in stats['documents'].items():
                        print(f"     - {doc}: {count} chunks")
                    print()
                    continue
                
                elif command.startswith('/add '):
                    file_path = command[5:].strip()
                    if os.path.exists(file_path):
                        print(f"Adding document: {file_path}")
                        chatbot.add_document(file_path)
                    else:
                        print(f"File not found: {file_path}")
                    continue
                
                elif command == '/rebuild':
                    print("Rebuilding vector index...")
                    chatbot.initialize(rebuild_index=True)
                    print("Index rebuilt successfully!")
                    continue
                
                else:
                    print("Unknown command. Type /help for available commands.")
                    continue
            
            # Process question
            print("Thinking...")
            
            # Ask if user wants enhanced response (if Groq is available)
            use_llm = False
            if chatbot.groq_client:
                llm_choice = input("Use Groq-enhanced AI response? (y/N): ").strip().lower()
                use_llm = llm_choice in ['y', 'yes']
            
            result = chatbot.answer_question(user_input, use_llm=use_llm)
            
            # Display answer
            print(f"\n Bot ({result['language'].upper()}):")
            print(result['answer'])
            
            # Display sources
            if result['sources']:
                print(f"\nSources ({len(result['sources'])} documents):")
                for i, source in enumerate(result['sources'], 1):
                    print(f"   {i}. {source['filename']} (Score: {source['score']:.3f})")
                    print(f"      Preview: {source['text_preview']}")
            
            print(f"\nMethod: {result['method']}")
            if 'model_used' in result and result['model_used'] != 'retrieval_only':
                print(f"Model: {result['model_used']}")
            print("-" * 60)
        
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break
        except Exception as e:
            print(f" Error: {e}")
            continue

if __name__ == "__main__":
    main()