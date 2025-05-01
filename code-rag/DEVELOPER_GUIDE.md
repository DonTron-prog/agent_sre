# Code RAG - Developer Guide

This guide provides technical details for developers interested in understanding, modifying, or contributing to the Code RAG project.

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Architecture Overview](#2-architecture-overview)
    *   [High-Level Flow](#high-level-flow)
    *   [External Services](#external-services)
3.  [Code Organization](#3-code-organization)
4.  [Key Components Deep Dive](#4-key-components-deep-dive)
    *   [`Settings`](#settings)
    *   [`DataLoader`](#dataloader)
    *   [`DataProcessor`](#dataprocessor)
    *   [`EmbeddingGenerator`](#embeddinggenerator)
    *   [`ChromaVectorStore`](#chromavectorstore)
    *   [`Retriever`](#retriever)
    *   [`LLMIntegration`](#llmintegration)
    *   [`CodeRAG`](#coderag)
5.  [Configuration Management](#5-configuration-management)
6.  [API Layer (FastAPI)](#6-api-layer-fastapi)
    *   [Structure](#structure)
    *   [Dependency Injection](#dependency-injection)
7.  [CLI Scripts](#7-cli-scripts)
    *   [`ingest.py`](#ingestpy)
    *   [`query.py`](#querypy)
8.  [Extending the System](#8-extending-the-system)
    *   [Data Sources](#data-sources)
    *   [Embedding Models](#embedding-models)
    *   [Vector Stores](#vector-stores)
    *   [LLMs / Providers](#llms--providers)
    *   [Retrieval Strategy](#retrieval-strategy)
9.  [Testing](#9-testing)
    *   [Framework](#framework)
    *   [Running Tests](#running-tests)
    *   [Coverage](#coverage)
10. [Code Style & Linting](#10-code-style--linting)
11. [Contribution Workflow](#11-contribution-workflow)
12. [Logging](#12-logging)

---

## 1. Introduction

This document outlines the architecture, code structure, and development practices for the Code RAG project. It aims to help developers understand how the system works internally and how to contribute effectively.

## 2. Architecture Overview

Code RAG implements a standard Retrieval-Augmented Generation pipeline tailored for solving code errors.

### High-Level Flow

1.  **Ingestion:**
    *   Load error/solution data (CodeInsight dataset via `DataLoader`).
    *   Process and clean the data (`DataProcessor`).
    *   Generate vector embeddings for error messages (`EmbeddingGenerator`).
    *   Store embeddings and associated metadata (solutions) in a vector database (`ChromaVectorStore`).
2.  **Querying:**
    *   Receive user query (error message) via API or CLI.
    *   Generate embedding for the query (`EmbeddingGenerator`).
    *   Retrieve semantically similar errors and their solutions from the vector database (`Retriever` using `ChromaVectorStore`).
    *   Format retrieved data as context (`Retriever`).
    *   Construct a prompt including the original query and the retrieved context.
    *   Send the prompt to an LLM for response generation (`LLMIntegration`).
    *   Return the generated solution and references to the user.

The central orchestrator for the querying flow is the `CodeRAG` class.

### External Services

*   **Hugging Face:** Hosts the `Nbeau/CodeInsight` dataset.
*   **OpenAI:** Provides the API for generating text embeddings (default: `text-embedding-ada-002`).
*   **OpenRouter.ai:** Acts as a gateway to various LLMs for the generation step (default: `openai/gpt-3.5-turbo`).

## 3. Code Organization

The project follows a standard Python project structure with source code located in the `src` directory.

```
code-rag/
├── .env.example           # Example environment variables
├── .gitignore
├── pyproject.toml         # Project metadata and dependencies (PEP 517/518)
├── README.md
├── setup.py               # Setuptools configuration (for editable installs)
├── data/                  # Default directory for datasets
│   ├── processed/         # Processed data (e.g., cleaned JSON)
│   └── raw/               # Raw downloaded data (e.g., Hugging Face cache)
├── chroma_db/             # Default directory for ChromaDB persistent storage
├── src/
│   └── code_rag/          # Main package source code
│       ├── __init__.py
│       ├── api/           # FastAPI application components
│       │   ├── __init__.py
│       │   ├── main.py    # FastAPI app creation and middleware
│       │   ├── models.py  # Pydantic request/response models
│       │   └── routes.py  # API endpoint definitions
│       ├── config/        # Configuration management
│       │   ├── __init__.py
│       │   └── settings.py# Pydantic settings model, loading from .env
│       ├── core/          # Core RAG logic
│       │   ├── __init__.py
│       │   ├── embeddings.py # Embedding generation logic
│       │   ├── llm.py     # LLM interaction logic (OpenRouter)
│       │   ├── rag.py     # Main RAG pipeline orchestrator class
│       │   └── retriever.py # Document retrieval logic
│       ├── data/          # Data loading and processing
│       │   ├── __init__.py
│       │   ├── loader.py  # Loading data from Hugging Face
│       │   └── processor.py # Cleaning and preparing data
│       ├── db/            # Database interactions (Vector Store)
│       │   ├── __init__.py
│       │   └── chroma.py  # ChromaDB client and operations
│       ├── utils/         # Utility functions
│       │   ├── __init__.py
│       │   └── helpers.py # Logging setup, etc.
│       └── scripts/       # Command-line interface scripts
│           ├── ingest.py  # Data ingestion CLI tool
│           └── query.py   # Querying CLI tool
├── tests/                 # Unit and integration tests (using pytest)
│   └── ...
└── USER_GUIDE.md
└── DEVELOPER_GUIDE.md
```

## 4. Key Components Deep Dive

Refer to the `USER_GUIDE.md` for a functional overview. This section focuses on implementation details relevant to developers.

### `Settings`

*   **Location:** `code_rag/config/settings.py`
*   **Implementation:** Uses Pydantic's `BaseSettings` (implicitly via `BaseModel` and `ConfigDict(env_prefix=...)`) to load configuration from environment variables (prefixed with `CODE_RAG_`) and `.env` files. Provides type hints and validation. Default values are defined. `computed_field` is used for derived paths.

### `DataLoader`

*   **Location:** `code_rag/data/loader.py`
*   **Implementation:** Uses the `datasets` library from Hugging Face to load and cache the dataset specified (`Nbeau/CodeInsight` by default). Manages caching in the `raw_data_dir` defined in `Settings`.

### `DataProcessor`

*   **Location:** `code_rag/data/processor.py`
*   **Implementation:** Takes a `Dataset` object (usually from `DataLoader`). Extracts specified columns (`error_key`, `solution_key`), performs basic cleaning (`strip`), and structures the output into a list of dictionaries containing `error`, `solution`, and `metadata`. Prepares data specifically for embedding (separating documents, metadata, and IDs). Can save/load processed data to/from JSON.

### `EmbeddingGenerator`

*   **Location:** `code_rag/core/embeddings.py`
*   **Implementation:** Uses the `openai` Python client library. Requires `OPENAI_API_KEY`. Implements batching (`get_embeddings`) and uses the `tenacity` library for automatic retries with exponential backoff on specific OpenAI API errors (`RateLimitError`, `APITimeoutError`). Includes a simple in-memory cache.

### `ChromaVectorStore`

*   **Location:** `code_rag/db/chroma.py`
*   **Implementation:** Uses the `chromadb` client library in persistent mode (`PersistentClient`). Initializes or connects to a collection. The `add_documents` method handles batching and optionally calls `EmbeddingGenerator` if embeddings aren't pre-computed. The `query` method takes a text query, generates its embedding, and queries Chroma for nearest neighbors.

### `Retriever`

*   **Location:** `code_rag.core/retriever.py`
*   **Implementation:** Acts as a bridge between the query input and the LLM context. Uses `ChromaVectorStore` to perform the similarity search. Formats the results from Chroma (including errors and solutions from metadata) into a structured context string (`format_for_context`) designed to be informative for the LLM.

### `LLMIntegration`

*   **Location:** `code_rag.core/llm.py`
*   **Implementation:** Uses the `requests` library to interact with the OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`). Requires `OPENROUTER_API_KEY`. Constructs the JSON payload including the model, messages (system prompt, context, query), and parameters (temperature, max_tokens). Uses `tenacity` for retries on network errors. Includes basic handling for streaming responses (`process_streaming_response`).

### `CodeRAG`

*   **Location:** `code_rag.core/rag.py`
*   **Implementation:** The main orchestrator class. Initializes all other core components (`EmbeddingGenerator`, `ChromaVectorStore`, `Retriever`, `LLMIntegration`) based on `Settings`. The `query` method executes the RAG pipeline: calls `Retriever.retrieve_and_format` to get context, then calls `LLMIntegration.generate_response` with the query and context. Includes a `health_check` method.

## 5. Configuration Management

*   Configuration is centralized in `code_rag.config.settings.py` using a Pydantic `Settings` model.
*   Environment variables (prefixed with `CODE_RAG_`) take precedence.
*   A `.env` file in the project root (`code-rag/`) is automatically loaded using `python-dotenv`.
*   The `get_settings` function provides a singleton instance of the `Settings`.
*   Components generally accept an optional `settings` argument in their constructor, defaulting to `get_settings()`.

## 6. API Layer (FastAPI)

### Structure

*   `main.py`: Creates the `FastAPI` app instance, sets up middleware (CORS, logging), defines the root endpoint, and includes the router. Can be run directly with `uvicorn` for development.
*   `routes.py`: Defines `APIRouter` and the main endpoints (`/query`, `/health`). Uses dependency injection to get the `CodeRAG` client. Handles request processing and response formatting.
*   `models.py`: Defines Pydantic models for request body validation (`QueryRequest`) and response serialization (`QueryResponse`, `HealthCheckResponse`, etc.).

### Dependency Injection

*   The `get_rag_client` function in `routes.py` acts as a FastAPI dependency.
*   It initializes a `CodeRAG` instance (which in turn loads settings and initializes other components).
*   FastAPI automatically calls this function for endpoints that declare `rag_client: CodeRAG = Depends(get_rag_client)` and injects the returned client instance.

## 7. CLI Scripts

Located in `src/code_rag/scripts/`. These scripts provide command-line access to core functionalities.

### `ingest.py`

*   Uses `argparse` to handle command-line arguments (`--batch-size`, `--limit`, etc.).
*   Initializes `DataLoader`, `DataProcessor`, `EmbeddingGenerator`, `ChromaVectorStore`.
*   Orchestrates the full data ingestion pipeline: load -> process -> embed -> store in Chroma.
*   Can optionally load previously processed data to skip initial steps.

### `query.py`

*   Uses `argparse` to handle command-line arguments (`query`, `--num-results`, etc.).
*   Initializes the main `CodeRAG` client.
*   Takes a query string (from args or stdin).
*   Calls `rag_client.query`.
*   Formats the result for console output or outputs raw JSON (`--json` flag).

## 8. Extending the System

The modular design allows for extensions:

### Data Sources

*   Modify `DataLoader` or create a new loader class to support different datasets or data formats.
*   Adjust `DataProcessor` if the new data source has different fields or requires different cleaning steps. Update the `error_key` and `solution_key` logic if necessary.

### Embedding Models

*   Modify `EmbeddingGenerator` to use a different embedding API or library (e.g., Sentence Transformers, Cohere).
*   Update `Settings` to include configuration for the new model/API key.
*   Ensure the chosen `ChromaVectorStore` (or alternative) is compatible with the embedding dimensions.

### Vector Stores

*   Create a new class implementing a similar interface to `ChromaVectorStore` (e.g., `add_documents`, `query`) for a different vector database (e.g., Weaviate, Pinecone, FAISS).
*   Update the `CodeRAG` and `Retriever` classes to use the new vector store implementation, potentially adding configuration options to `Settings`.

### LLMs / Providers

*   Modify `LLMIntegration` to support different LLM providers (e.g., direct OpenAI API, Anthropic, Cohere, local models via Ollama/LM Studio).
*   Update `Settings` for new API keys or model identifiers.

### Retrieval Strategy

*   Modify the `Retriever` class:
    *   Implement different context formatting (`format_for_context`).
    *   Add a reranking step after the initial retrieval from ChromaDB to improve relevance.
    *   Experiment with different numbers of retrieved documents (`n_results`).

## 9. Testing

### Framework

*   The project is set up to use `pytest` (see `pyproject.toml` under `[project.optional-dependencies].dev`).
*   Tests should be placed in the `tests/` directory, mirroring the structure of `src/code_rag/`.

### Running Tests

1.  Install development dependencies: `pip install -e .[dev]`
2.  Run tests from the `code-rag` directory:
    ```bash
    pytest tests/
    ```

### Coverage

*   `pytest-cov` is included for measuring test coverage.
*   Run tests with coverage:
    ```bash
    pytest --cov=code_rag tests/
    ```
*   Generate an HTML coverage report:
    ```bash
    pytest --cov=code_rag --cov-report=html tests/
    ```
    (Report will be in `htmlcov/index.html`)

*Note: Ensure comprehensive tests are written for new features or modifications, including unit tests for individual components and integration tests for workflows like querying.*

## 10. Code Style & Linting

*   **Formatting:** The project uses `black` for code formatting and `isort` for import sorting.
*   **Type Checking:** `mypy` is used for static type checking.
*   **Configuration:** See `pyproject.toml` for tool configuration (if any).

Before committing code, ensure it's formatted and passes type checks:

```bash
black src/ tests/
isort src/ tests/
mypy src/
```

Consider integrating these checks into pre-commit hooks for automation.

## 11. Contribution Workflow

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally: `git clone <your-fork-url>`
3.  Create a **new branch** for your feature or bugfix: `git checkout -b feature/your-feature-name` or `bugfix/issue-description`.
4.  **Make changes:** Implement your feature or fix the bug.
5.  **Add tests:** Write unit and/or integration tests for your changes in the `tests/` directory.
6.  **Run tests:** Ensure all tests pass (`pytest tests/`).
7.  **Check coverage:** Aim to maintain or increase test coverage (`pytest --cov=code_rag tests/`).
8.  **Format and lint:** Run `black`, `isort`, and `mypy` to ensure code style and type correctness.
9.  **Commit** your changes with a clear commit message.
10. **Push** your branch to your fork: `git push origin feature/your-feature-name`.
11. **Create a Pull Request (PR)** from your branch to the `main` branch of the original repository.
12. **Address review comments:** Respond to any feedback on your PR.
13. Once approved, your PR will be merged.

## 12. Logging

*   A standard logger is configured in `code_rag.utils.helpers.setup_logger`.
*   Components import and use this logger (`from code_rag.utils.helpers import logger`).
*   Log levels can be configured via the `--log-level` argument in CLI scripts or potentially via environment variables for the API (though not explicitly implemented in `settings.py` currently).
*   The FastAPI middleware in `api/main.py` logs request/response information.