# Code RAG: Retrieval-Augmented Generation for Code Errors and SRE Incidents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Code RAG is a lightweight Retrieval-Augmented Generation (RAG) component designed to help developers find solutions to code errors and SRE incidents. It leverages a vector database (Chroma) populated with error-solution pairs from the CodeInsight dataset and synthetic SRE incident documents, then uses a Large Language Model (LLM) via OpenRouter to generate relevant solutions based on retrieved context.

## Overview

When faced with a cryptic error message or an unfamiliar SRE incident, developers and operators often spend significant time searching online forums like Stack Overflow or internal documentation. Code RAG aims to streamline this process by:

1.  **Retrieving** similar error messages/incidents and their corresponding solutions from a pre-indexed knowledge base (CodeInsight dataset and SRE incident documents stored in Chroma).
2.  **Augmenting** a prompt to an LLM with this retrieved context.
3.  **Generating** a tailored solution and explanation based on the user's specific error message or incident description and the relevant context.

This project provides:

*   A Python library (`code_rag`) for programmatic integration.
*   A REST API (built with FastAPI) for easy service deployment.
*   Command-line tools for data ingestion and querying both code errors and SRE incidents.

## Features

*   **Vector Store:** Uses ChromaDB for efficient similarity search of error and incident embeddings.
*   **Embeddings:** Generates embeddings using OpenAI's `text-embedding-ada-002` model.
*   **LLM Integration:** Connects to various LLMs via OpenRouter (defaults to `openai/gpt-3.5-turbo`).
*   **Datasets:**
    * Utilizes the `Nbeau/CodeInsight` dataset from Hugging Face (Stack Overflow error-solution pairs)
    * Generates synthetic SRE incident documents with realistic scenarios and solutions
*   **API:** Provides a FastAPI-based REST API for querying.
*   **CLI:** Includes scripts for data ingestion and querying for both code errors and SRE incidents:
    * Code error scripts: `ingest.py` and `query.py`
    * SRE incident scripts: `generate_sre_documents.py`, `ingest_sre_documents.py`, `query_sre_incidents.py`, and `validate_sre_rag.py`
*   **Configurable:** Settings managed via environment variables (`.env` file).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace with the actual URL
    cd code-rag
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .
    ```
    This installs the package in editable mode along with its core dependencies listed in `pyproject.toml`.

4.  **Install development dependencies (optional):**
    ```bash
    pip install -e .[dev]
    ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the `code-rag` directory by copying the example:

```bash
cp .env.example .env
```

Edit the `.env` file and provide the necessary API keys and settings:

```dotenv
# API Keys (Required)
OPENAI_API_KEY="sk-..."
OPENROUTER_API_KEY="sk-or-..."

# Model Configuration (Optional - Defaults shown)
# CODE_RAG_EMBEDDING_MODEL="text-embedding-ada-002"
# CODE_RAG_LLM_MODEL="openai/gpt-3.5-turbo"

# Data Paths (Optional - Defaults shown)
# CODE_RAG_DATA_DIR="./data"
# CODE_RAG_CHROMA_PATH="./chroma_db"

# Retrieval Configuration (Optional - Defaults shown)
# CODE_RAG_DEFAULT_NUM_RESULTS=3

# API Server Configuration (Optional - Defaults shown)
# CODE_RAG_API_HOST="0.0.0.0"
# CODE_RAG_API_PORT=8000
```

**Required Variables:**

*   `OPENAI_API_KEY`: Your API key from OpenAI (used for generating embeddings).
*   `OPENROUTER_API_KEY`: Your API key from OpenRouter.ai (used for LLM generation).

**Optional Variables:**

*   `CODE_RAG_EMBEDDING_MODEL`: The OpenAI model used for embeddings.
*   `CODE_RAG_LLM_MODEL`: The OpenRouter model identifier for generation.
*   `CODE_RAG_DATA_DIR`: Base directory for raw and processed data.
*   `CODE_RAG_CHROMA_PATH`: Path to store the Chroma vector database.
*   `CODE_RAG_DEFAULT_NUM_RESULTS`: Default number of documents to retrieve.
*   `CODE_RAG_API_HOST`: Host address for the API server.
*   `CODE_RAG_API_PORT`: Port for the API server.

## Usage

### 1. Data Ingestion (Required First Step)

Before querying, you need to populate the Chroma vector database with the necessary data.

#### a) Code Error Data

```bash
python src/scripts/ingest.py
```

This script will:
*   Download the `Nbeau/CodeInsight` dataset (if not already cached in `data/raw`).
*   Process the error-solution pairs (saving to `data/processed`).
*   Generate embeddings for the error messages using the configured OpenAI model.
*   Store the documents, metadata (including solutions), and embeddings in the Chroma database located at `CODE_RAG_CHROMA_PATH`.

**Ingestion Options:**

*   `--batch-size <N>`: Set the batch size for embedding generation (default: 16).
*   `--limit <N>`: Process only the first N documents.
*   `--chroma-path <path>`: Override the Chroma DB path specified in `.env`.
*   `--processed-data <path>`: Use previously processed data from a specific JSON file.
*   `--force`: Force reprocessing even if processed data exists.
*   `--log-level <LEVEL>`: Set logging level (DEBUG, INFO, WARNING, ERROR).

#### b) SRE Incident Data

For SRE incidents, you'll need to first generate synthetic data and then ingest it:

```bash
# Generate synthetic SRE incident documents
python src/scripts/generate_sre_documents.py

# Ingest the generated documents into Chroma
python src/scripts/ingest_sre_documents.py
```

The generation script creates realistic SRE incident scenarios across various categories (container issues, networking, deployments, etc.) and saves them to `data/raw/sre_incidents.json`.

The ingestion script processes these documents and stores them in a separate collection named `sre_incidents` in the same Chroma database.

**SRE Ingestion Options:**
*   `--input-file <path>`: Path to the input JSON file.
*   `--batch-size <N>`: Set the batch size for embedding generation.
*   `--collection-name <name>`: Name of the Chroma collection (default: "sre_incidents").
*   Plus all the standard ingestion options available in the regular ingest script.

### 2. Querying

#### a) Using the Command Line Interface (CLI) for Code Errors

```bash
python src/scripts/query.py "Your error message here"
```

**Example:**

```bash
python src/scripts/query.py "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
```

The script will output the generated solution, the references used, and metadata.

**Query Options:**

*   `<query>`: The error message (required, can be prompted if omitted).
*   `--num-results <N>`: Number of documents to retrieve (default: 3).
*   `--temperature <T>`: LLM generation temperature (0.0-1.0, default: 0.7).
*   `--max-tokens <N>`: Max tokens for LLM response (default: 1024).
*   `--chroma-path <path>`: Override the Chroma DB path.
*   `--log-level <LEVEL>`: Set logging level.
*   `--json`: Output the results in JSON format instead of formatted text.

#### b) Using the Command Line Interface (CLI) for SRE Incidents

```bash
python src/scripts/query_sre_incidents.py
```

This script runs predefined test queries against the SRE incident collection. To validate the SRE RAG system more thoroughly:

```bash
python src/scripts/validate_sre_rag.py
```

The validation script performs comprehensive testing including document count verification, embedding validation, and quality metrics calculation.

#### b) Using the REST API

First, start the API server:

```bash
uvicorn code_rag.api.main:app --host 0.0.0.0 --port 8000 --reload
```
*(Note: The `--reload` flag is for development)*

Then, send a POST request to the `/api/v1/query` endpoint.

**Example using `curl`:**

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{
           "error_message": "AttributeError: '\''list'\'' object has no attribute '\''append_row'\''",
           "num_results": 5,
           "temperature": 0.5
         }'
```

**API Request Body (`QueryRequest`):**

```json
{
  "error_message": "string (required)",
  "num_results": "integer (optional, default: 3, min: 1, max: 10)",
  "temperature": "float (optional, default: 0.7, min: 0.0, max: 1.0)",
  "max_tokens": "integer (optional, default: 1024, min: 1, max: 4096)",
  "stream": "boolean (optional, default: false)"
}
```

**API Response Body (`QueryResponse`):**

```json
{
  "solution": "string",
  "references": [
    {
      "id": "string",
      "error": "string",
      "solution": "string",
      "similarity_score": "float",
      "metadata": "object | null"
    }
  ],
  "metadata": {
    "model_used": "string",
    "tokens_used": "integer | null",
    "processing_time_ms": "integer | null",
    "num_references": "integer"
  },
  "error": "string | null"
}
```

**API Endpoints:**

*   `POST /api/v1/query`: Submit an error message, get a generated solution. Supports streaming if `"stream": true` is set in the request (returns `text/event-stream`).
*   `GET /api/v1/health`: Check the health status of the API and its components.
*   `GET /docs`: Access Swagger UI for interactive API documentation.
*   `GET /redoc`: Access ReDoc documentation.

#### c) Using the Python Library

```python
from code_rag import CodeRAG

# Initialize the RAG client (loads settings from .env)
rag_client = CodeRAG()

# Define the error message
error = "IndexError: list index out of range"

# Query the system
result = rag_client.query(
    error_message=error,
    num_results=5,
    temperature=0.6
)

# Print the solution
print("Solution:", result.get("solution"))

# Print references
print("\nReferences:")
for i, ref in enumerate(result.get("references", []), 1):
    print(f"  {i}. Score: {ref.get('similarity_score'):.2f}")
    print(f"     Error: {ref.get('error')[:80]}...") # Truncated for brevity
    # print(f"     Solution: {ref.get('solution')}")
```

## SRE RAG Features

The SRE (Site Reliability Engineering) incident RAG system extends Code RAG's capabilities to help operations teams and SREs quickly resolve infrastructure and service incidents. Key features include:

* **Synthetic Data Generation**: Creates realistic SRE incident documents across categories including:
  * Pod and container issues
  * Networking problems
  * Deployment failures
  * Resource constraints
  * API errors
  * Database issues

* **Rich Metadata**: Each incident includes contextual metadata such as:
  * Severity level
  * Affected services
  * Incident category
  * Document type (runbook, incident report, architecture doc, etc.)

* **Validation Tools**: The `validate_sre_rag.py` script provides comprehensive validation including:
  * Document count verification
  * Document ID validation
  * Embedding quality testing
  * Result relevance metrics

* **Test Suite**: Includes predefined test queries covering common incident types to evaluate retrieval quality.

* **Integration**: Uses the same underlying RAG architecture as the code error system, allowing for a unified approach to knowledge retrieval.

## Contributing

Contributions are welcome! Please refer to the `DEVELOPER_GUIDE.md` for details on the development workflow, code structure, and testing procedures.

Key areas for contribution include:

*   Improving retrieval strategies (e.g., reranking).
*   Supporting different vector databases or embedding models.
*   Enhancing the LLM prompting techniques.
*   Adding more sophisticated data cleaning or processing steps.
*   Improving API features or performance.
*   Expanding test coverage.
*   Adding new categories of SRE incidents or enhancing the synthetic data generator.
*   Creating universal query capability to search across both code errors and SRE incidents.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.