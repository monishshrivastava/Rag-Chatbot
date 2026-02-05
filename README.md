Rag-Chatbot
============

Simple RAG (Retrieval-Augmented Generation) chatbot template that ingests documents, builds a vector store, and answers questions by retrieving relevant passages.

**Contents**
- `main.py` — project entrypoint for quick runs.
- `src/` — core modules: `chatbot.py`, `document_processor.py`, `retriever.py`, `vector_store.py`.
- `data/documents/` — source documents (English and Japanese).
- `data/vector_db/` — generated vector index and serialized chunks.

**Requirements**
- Python 3.10+
- See `requirements.txt` for Python package dependencies.

Quick start
-----------

1. Create a virtual environment and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy environment variables:

```bash
cp .env.example .env
# Fill in your keys in .env (do NOT commit real secrets)
```

3. Run the app (example):

```bash
python main.py
```

Project structure
-----------------

- `main.py` — small runner for interactive queries or demos.
- `src/document_processor.py` — splits and preprocesses documents into chunks.
- `src/vector_store.py` — builds and loads the vector index (FAISS or similar).
- `src/retriever.py` — retrieves nearest chunks given a query.
- `src/chatbot.py` — combines retrieval with a language model to produce answers.
- `data/` — documents and vector DB files. The repo contains example text files in `data/documents/en` and `data/documents/jp`.

Environment variables
---------------------

Use `.env` (not committed). Example keys are in `.env.example` and include placeholders for `GROQ_API_KEY` and `OPENAI_API_KEY`.

Security
--------
- Secrets were removed from commits and a `.env.example` was added. Rotate any exposed keys immediately if they were previously pushed.

Development notes
-----------------
- Vector DB files (`data/vector_db/*`) can be large; the repo includes serialized index files for convenience. If you regenerate the index, add them to `.gitignore` if you don't want them tracked.
- Pyc files are present in the workspace; consider adding `__pycache__/` to `.gitignore` if not already.

Contributing
------------
PRs and issues welcome. For code changes, follow the repo style and run the project locally to verify behavior.

License
-------
MIT — see LICENSE (not included).

Contact
-------
Owner: monishshrivastava
# Rag-Chatbot