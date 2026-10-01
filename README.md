# Open Source Project Intelligence

An AI-powered system for discovering and understanding open-source GitHub projects.

## Overview

This project collects GitHub repository data, processes it with a data pipeline, enriches projects using a local LLM, and provides RAG-based agentic search through an API.

## Architecture

flowchart TD
    A[GitHub API] --> B[Raw JSON]
    B --> C[ETL]
    C --> D[PostgreSQL]
    D --> E[README Ingestion]
    E --> F[AI Data Enrichment]
    F --> G[Chunking + Embeddings]
    G --> H[pgvector / RAG]

    H --> I[LangGraph Agent]
    I --> J[Agent Node]
    J --> K{Tool Needed?}

    K -->|Yes| L[Tools]
    L --> M[search_rag]
    L --> N[get_project_details]
    L --> O[fetch_github_projects]

    M --> J
    N --> J
    O --> J

    K -->|No| P[Final Answer]
    P --> Q[FastAPI]

## Features

* GitHub repository ingestion
* Data cleaning and transformation
* PostgreSQL data storage
* LLM-based project enrichment
* Vector search with pgvector
* RAG-based project retrieval
* LangGraph agent with tools
* FastAPI API
* Docker support

## Tech Stack

* Python
* PostgreSQL
* pgvector
* FastAPI
* LangGraph
* Ollama
* Qwen2.5
* Sentence Transformers
* GitHub REST API
* Docker

## API

Start the API:

```bash
uvicorn src.api.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

Example request:

```json
{
  "query": "Tell me about AutoGPT"
}
```

Example response:

```json
{
  "answer": "AutoGPT is an AI-driven platform..."
}
```

## Project Structure

```text
open-source-project-intelligence/
├── data/
├── src/
│   ├── ingestion/
│   ├── rag/
│   ├── agent/
│   └── api/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Project Status

**V1 completed.**

The current version demonstrates a complete pipeline from data ingestion to an AI-powered API.

## Future Improvements

* Frontend
* RAG evaluation
* Agent evaluation
* Better retrieval
* Cloud deployment
* Production monitoring
