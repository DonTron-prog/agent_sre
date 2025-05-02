# Code RAG - User Guide

Welcome to the User Guide for Code RAG! This guide provides detailed information on understanding and using the Code RAG system to find solutions for your coding errors and SRE incidents.

## Table of Contents

1.  [Introduction](#1-introduction)
    *   [What is RAG?](#what-is-rag)
    *   [How Code RAG Works](#how-code-rag-works)
2.  [Core Components](#2-core-components)
    *   [Data Sources](#data-sources)
    *   [Data Loader & Processor](#data-loader--processor)
    *   [Embedding Generator (OpenAI)](#embedding-generator-openai)
    *   [Vector Store (ChromaDB)](#vector-store-chromadb)
    *   [Retriever](#retriever)
    *   [LLM Integration (OpenRouter)](#llm-integration-openrouter)
    *   [API (FastAPI)](#api-fastapi)
    *   [CLI Tools](#cli-tools)
3.  [Getting Started](#3-getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Installation](#installation)
    *   [Configuration](#configuration)
    *   [Data Ingestion](#data-ingestion)
4.  [Usage Tutorials](#4-usage-tutorials)
    *   [Tutorial 1: Querying Code Errors via CLI](#tutorial-1-querying-code-errors-via-cli)
    *   [Tutorial 2: Querying SRE Incidents](#tutorial-2-querying-sre-incidents)
    *   [Tutorial 3: Querying via API](#tutorial-3-querying-via-api)
    *   [Tutorial 4: Using the Python Library](#tutorial-4-using-the-python-library)
    *   [Understanding the Output](#understanding-the-output)
5.  [SRE Incident RAG](#5-sre-incident-rag)
    *   [Overview](#overview)
    *   [Available Incident Categories](#available-incident-categories)
    *   [Document Types and Metadata](#document-types-and-metadata)
    *   [Validation and Quality Metrics](#validation-and-quality-metrics)
6.  [Troubleshooting](#6-troubleshooting)
    *   [API Key Issues](#api-key-issues)
    *   [Data Ingestion Errors](#data-ingestion-errors)
    *   [Query Errors](#query-errors)
    *   [Performance Issues](#performance-issues)
    *   [Checking System Health](#checking-system-health)

---

## 1. Introduction

### What is RAG?

RAG stands for **Retrieval-Augmented Generation**. It's a technique used in artificial intelligence, particularly with Large Language Models (LLMs), to improve the quality and factual accuracy of generated responses.

Instead of relying solely on the LLM's internal (and potentially outdated or incomplete) knowledge, a RAG system first **retrieves** relevant information from an external knowledge source based on the user's query. This retrieved information is then provided as **context** to the LLM along with the original query. The LLM then **generates** a response that is grounded in this specific, relevant context.

This approach helps to:

*   Reduce hallucinations (making things up).
*   Provide more up-to-date information.
*   Offer more specific and relevant answers.
*   Allow citation of sources (the retrieved documents).

### How Code RAG Works

Code RAG applies the RAG pattern to two domains: solving programming errors and addressing SRE incidents. Here's the workflow:

1.  **Ingestion (One-time setup):**
    *   For code errors:
        *   The `Nbeau/CodeInsight` dataset (containing error-solution pairs from Stack Overflow) is downloaded.
        *   Error messages are extracted and converted into numerical representations called **embeddings** using an OpenAI model.
    *   For SRE incidents:
        *   Synthetic SRE incident documents are generated or loaded from a JSON file.
        *   These incidents describe various operational problems with their solutions.
        *   The incidents are processed and converted into embeddings.
    *   These embeddings, along with the original messages and their corresponding solutions (as metadata), are stored in a **ChromaDB vector database**. This database allows for efficient searching based on semantic similarity.

2.  **Querying (User interaction):**
    *   A user provides a code error message or SRE incident description (via CLI, API, or Python library).
    *   The system generates an embedding for the user's input.
    *   This embedding is used to **query** the appropriate ChromaDB collection, retrieving the embeddings (and associated data) of the most similar errors or incidents stored during ingestion.
    *   The retrieved content and solutions are formatted into a **context string**.
    *   This context string, along with the user's original query, is sent as a prompt to an LLM (via OpenRouter).
    *   The LLM **generates** a detailed solution and explanation, using the provided context to ensure relevance and accuracy.
    *   The generated solution and the retrieved references are returned to the user.

## 2. Core Components

Code RAG is built from several key components:

### Data Sources

*   **CodeInsight Dataset:**
    *   **Source:** `Nbeau/CodeInsight` dataset on Hugging Face.
    *   **Content:** A collection of question-answer pairs from Stack Overflow, focusing on code errors and their solutions.
    *   **Role:** Provides the raw knowledge base for code error resolution.

*   **SRE Incident Documents:**
    *   **Source:** Generated synthetically using the `generate_sre_documents.py` script.
    *   **Content:** Realistic SRE incident scenarios across various categories with corresponding solutions.
    *   **Role:** Provides the knowledge base for SRE incident resolution.

### Data Loader & Processor

*   **Modules:** `code_rag.data.loader`, `code_rag.data.processor`
*   **Functionality:**
    *   Downloads and caches the CodeInsight dataset (`DataLoader`).
    *   Extracts relevant fields (error messages, solutions) from the dataset (`DataProcessor`).
    *   Cleans and normalizes the text data (`DataProcessor`).
    *   Prepares the data structure (documents, metadata, IDs) needed for embedding and storage (`DataProcessor`).

### Embedding Generator (OpenAI)

*   **Module:** `code_rag.core.embeddings`
*   **Model:** Configurable via `CODE_RAG_EMBEDDING_MODEL` (default: `text-embedding-ada-002`).
*   **Functionality:**
    *   Connects to the OpenAI API using the `OPENAI_API_KEY`.
    *   Converts text (specifically, error messages) into high-dimensional vector embeddings. These vectors capture the semantic meaning of the text.
    *   Includes batching and retry logic for efficiency and robustness.

### Vector Store (ChromaDB)

*   **Module:** `code_rag.db.chroma`
*   **Technology:** ChromaDB (persistent mode).
*   **Functionality:**
    *   Stores the generated embeddings along with their corresponding documents (error messages) and metadata (solutions, etc.).
    *   Provides fast similarity search capabilities, allowing retrieval of documents whose embeddings are closest to a given query embedding.
    *   Stores data locally in the directory specified by `CODE_RAG_CHROMA_PATH`.

### Retriever

*   **Module:** `code_rag.core.retriever`
*   **Functionality:**
    *   Orchestrates the retrieval process.
    *   Takes a user query (error message).
    *   Uses the `EmbeddingGenerator` to create an embedding for the query.
    *   Uses the `ChromaVectorStore` to find the `n` most similar documents (errors) from the database based on the query embedding.
    *   Formats the retrieved errors and their solutions into a context string suitable for the LLM.

### LLM Integration (OpenRouter)

*   **Module:** `code_rag.core.llm`
*   **Service:** OpenRouter.ai
*   **Model:** Configurable via `CODE_RAG_LLM_MODEL` (default: `openai/gpt-3.5-turbo`).
*   **Functionality:**
    *   Connects to the OpenRouter API using the `OPENROUTER_API_KEY`.
    *   Constructs a prompt containing the system instructions, the retrieved context (from the `Retriever`), and the user's original query.
    *   Sends the prompt to the specified LLM via OpenRouter.
    *   Receives the generated solution from the LLM.
    *   Handles API retries and streaming responses.

### API (FastAPI)

*   **Modules:** `code_rag.api.main`, `code_rag.api.routes`, `code_rag.api.models`
*   **Framework:** FastAPI
*   **Functionality:**
    *   Exposes the RAG system's capabilities via a RESTful API.
    *   Provides endpoints for querying (`/api/v1/query`) and health checks (`/api/v1/health`).
    *   Handles request validation using Pydantic models.
    *   Supports standard JSON responses and server-sent events for streaming.

### CLI Tools

*   **Code Error Tools:**
    *   **Modules:** `code_rag.scripts.ingest`, `code_rag.scripts.query`
    *   **Functionality:**
        *   `ingest.py`: Command-line tool to perform the code error data ingestion process.
        *   `query.py`: Command-line tool to query the RAG system directly with an error message.

*   **SRE Incident Tools:**
    *   **Modules:** Various script files in the scripts directory
    *   **Functionality:**
        *   `generate_sre_documents.py`: Generates realistic synthetic SRE incident documents.
        *   `ingest_sre_documents.py`: Processes and ingests SRE incident documents into ChromaDB.
        *   `query_sre_incidents.py`: Tests querying against the SRE incident collection.
        *   `validate_sre_rag.py`: Validates and evaluates the SRE RAG system performance.

## 3. Getting Started

Follow these steps to set up and run Code RAG.

### Prerequisites

*   Python 3.8 or higher.
*   `git` for cloning the repository.
*   Access to the internet (for downloading dependencies and the dataset, and for API calls).
*   API Keys:
    *   OpenAI API Key
    *   OpenRouter API Key

### Installation

1.  **Clone:** `git clone <repository-url> && cd code-rag`
2.  **Create Environment:** `python -m venv venv`
3.  **Activate Environment:** `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4.  **Install:** `pip install -e .`

### Configuration

1.  **Copy Example:** `cp .env.example .env`
2.  **Edit `.env`:** Open the `.env` file and add your `OPENAI_API_KEY` and `OPENROUTER_API_KEY`. You can also adjust other optional settings if needed (see `README.md` or `code_rag/config/settings.py` for details).

### Data Ingestion

This is a crucial one-time step to populate the vector database.

#### Code Error Data

```bash
python src/scripts/ingest.py
```

This process might take some time depending on your internet connection (for dataset download) and the number of documents being processed and embedded. Monitor the console output for progress. By default, data is stored in `./data` and the Chroma database in `./chroma_db`.

#### SRE Incident Data

To use the SRE incident RAG functionality, you need to generate and ingest SRE incident data:

```bash
# Step 1: Generate synthetic SRE incident documents
python src/scripts/generate_sre_documents.py

# Step 2: Ingest the generated documents into ChromaDB
python src/scripts/ingest_sre_documents.py
```

The first script creates a JSON file with synthetic SRE incident documents that mimic real-world operational issues. The second script processes these documents and ingests them into a separate ChromaDB collection named `sre_incidents`.

## 4. Usage Tutorials

Once data ingestion is complete, you can query the system.

### Tutorial 1: Querying Code Errors via CLI

This is the simplest way to interact with Code RAG for programming errors.

1.  **Open your terminal** (ensure your virtual environment is activated).
2.  **Run the query script** with your error message:

    ```bash
    python src/scripts/query.py "Your specific error message here"
    ```

    *Example:*
    ```bash
    python src/scripts/query.py "ValueError: dictionary update sequence element #0 has length 1; 2 is required"
    ```

3.  **Review the output:** The script will print the generated solution, followed by the references (similar errors and solutions) retrieved from the database, and finally some metadata about the process.

    *Tip: Use the `--json` flag to get the raw JSON output instead of the formatted console text.*
    ```bash
    python src/scripts/query.py "Your error" --json > output.json
    ```

### Tutorial 2: Querying SRE Incidents

To query the SRE incident database:

1.  **Open your terminal** (ensure your virtual environment is activated).
2.  **Run the SRE query script:** By default, this runs with sample test queries:

    ```bash
    python src/scripts/query_sre_incidents.py
    ```

    The script will display results for several predefined queries like "Database connection issues", "Kubernetes pods not starting", and "API rate limiting errors".

3.  **Run validation tests:** For a more comprehensive assessment:

    ```bash
    python src/scripts/validate_sre_rag.py
    ```

    This script performs a series of validations and tests for the SRE RAG system, including:
    - Verifying document count in ChromaDB
    - Validating document IDs and structure
    - Testing the embedding quality through response analysis
    - Running test queries across different incident categories
    - Computing quality metrics like average similarity scores

    Use the `--run-ingestion` flag if you want the validation script to regenerate and reingest the data before validation:

    ```bash
    python src/scripts/validate_sre_rag.py --run-ingestion
    ```

### Tutorial 3: Querying via API

Use the API if you want to integrate Code RAG into another application or service.

1.  **Start the API Server:**
    ```bash
    uvicorn code_rag.api.main:app --host 0.0.0.0 --port 8000
    ```
    *(Add `--reload` for development if you're making changes).*

2.  **Send a POST Request:** Use a tool like `curl`, Postman, Insomnia, or Python's `requests` library to send a POST request to `http://localhost:8000/api/v1/query`.

    *Example using `curl` for a code error:*
    ```bash
    curl -X POST "http://localhost:8000/api/v1/query" \
         -H "Content-Type: application/json" \
         -d '{
               "error_message": "KeyError: '\''some_key'\''",
               "num_results": 4
             }'
    ```

    *Example for an SRE incident:*
    ```bash
    curl -X POST "http://localhost:8000/api/v1/query" \
         -H "Content-Type: application/json" \
         -d '{
               "error_message": "Kubernetes pod keeps crashing with OOMKilled error",
               "collection_name": "sre_incidents",
               "num_results": 3
             }'
    ```

3.  **Examine the Response:** The API will return a JSON object containing the `solution`, `references`, and `metadata`.

    *Tip: Access the interactive API documentation (Swagger UI) in your browser at `http://localhost:8000/docs` to try out the endpoints.*

### Tutorial 4: Using the Python Library

Integrate Code RAG directly into your Python code.

1.  **Import the `CodeRAG` class:**
    ```python
    from code_rag import CodeRAG
    ```

2.  **Initialize the client:** This automatically loads settings from your `.env` file.
    ```python
    # For code errors (default collection)
    code_rag_client = CodeRAG()
    
    # For SRE incidents
    sre_rag_client = CodeRAG(collection_name="sre_incidents")
    ```
    *(You can also override other settings during initialization, e.g., `CodeRAG(llm_model="anthropic/claude-3-haiku")`)*

3.  **Call the `query` method:**
    ```python
    # Query for a code error
    error = "ModuleNotFoundError: No module named 'nonexistent_package'"
    result = code_rag_client.query(error_message=error, num_results=3)

    # Access the results
    print(f"Solution:\n{result.get('solution')}\n")
    print(f"Metadata: {result.get('metadata')}")
    
    # Query for an SRE incident
    incident = "Database query timeout affecting critical user transactions"
    sre_result = sre_rag_client.query(error_message=incident, num_results=2)
    
    print(f"SRE Solution:\n{sre_result.get('solution')}\n")
    print(f"SRE Metadata: {sre_result.get('metadata')}")
    ```

### Understanding the Output

Whether using the CLI, API, or library, the result typically contains:

*   **`solution`**: The main text generated by the LLM, explaining the error or incident and providing potential fixes.
*   **`references`**: A list of documents retrieved from the vector store that were used as context. Each reference includes:
    *   `id`: The unique ID in the database.
    *   `error`: The error message from the CodeInsight dataset or SRE incident description.
    *   `solution`: The corresponding solution from the dataset.
    *   `similarity_score`: A measure of how similar the reference is to your query (higher is more similar).
    *   `metadata`: Additional metadata associated with the reference, such as:
        * For code errors: Tags, score, etc.
        * For SRE incidents: Category, severity, affected services, document type, etc.
*   **`metadata`**: Information about the generation process:
    *   `model_used`: Which LLM generated the response.
    *   `tokens_used`: How many tokens were processed by the LLM (if available).
    *   `processing_time_ms`: How long the query took.
    *   `num_references`: How many references were provided to the LLM.
*   **`error`** (Optional): If an error occurred during the process, this field will contain details.

## 5. SRE Incident RAG

### Overview

The SRE (Site Reliability Engineering) Incident RAG extends Code RAG to help teams quickly diagnose and resolve operational incidents in cloud-native environments. Instead of using a public dataset, it leverages synthetic data generation to create realistic incident descriptions and solutions across various infrastructure categories.

### Available Incident Categories

The SRE RAG system includes incidents across six main categories:

1. **Pod and Container Issues**: Problems with Kubernetes pods and containers, including crashes, OOM kills, image pull failures, and resource constraints.

2. **Networking Issues**: Network connectivity problems, DNS resolution failures, latency spikes, timeouts, TLS handshake failures, and load balancer issues.

3. **Deployment Failures**: Issues with deployment processes including stuck rollouts, failed validations, missing configuration resources, and post-deployment test failures.

4. **Resource Constraints**: Problems related to resource exhaustion including CPU/memory pressure, quota limits, disk space issues, and connection pool exhaustion.

5. **API Errors**: Service errors, rate limiting, timeout issues, authentication failures, and circuit breaker activations.

6. **Database Issues**: Database connection problems, replication lag, query timeouts, deadlocks, and performance degradation.

### Document Types and Metadata

SRE incident documents contain rich metadata useful for filtering and context:

* **Document Type**: Categorizes the document as one of:
  * Runbook (40% of documents)
  * Incident report (35%)
  * Architecture document (10%)
  * Code snippet (10%)
  * Chat log (5%)

* **Additional Metadata**:
  * Severity level (e.g., critical, high, medium, low)
  * Affected services
  * Category (the incident category)
  * Incident date
  * Resolution date
  * Resolution time (in minutes)

### Validation and Quality Metrics

The `validate_sre_rag.py` script provides comprehensive validation capabilities:

* **Document Validation**: Verifies expected document count, ID uniqueness, and embedding quality.

* **Test Queries**: Executes queries against different incident types to evaluate relevance.

* **Quality Metrics**:
  * **Average Similarity Score**: Measures the semantic similarity between queries and retrieved results.
  * **Average Query Time**: Performance metric for retrieval operations.
  * **System Status**: Overall assessment based on validation results and quality metrics.

To run a full validation:

```bash
python src/scripts/validate_sre_rag.py
```

The validation output provides a comprehensive summary with specific metrics and an overall system status assessment.

## 6. Troubleshooting

### API Key Issues

*   **Error:** "OpenAI API key not provided" or "OpenRouter API key not provided".
*   **Solution:** Ensure your `.env` file exists in the `code-rag` directory and contains valid `OPENAI_API_KEY` and `OPENROUTER_API_KEY` values. Verify there are no typos. If running scripts, ensure they are run from the `code-rag` directory or that the `.env` file is otherwise accessible.

### Data Ingestion Errors

*   **Error:** Hugging Face download fails.
*   **Solution:** Check your internet connection. Ensure the dataset name (`Nbeau/CodeInsight`) is correct. Try running `ingest.py` again.
*   **Error:** ChromaDB write errors.
*   **Solution:** Check file permissions for the directory specified by `CODE_RAG_CHROMA_PATH`. Ensure sufficient disk space.
*   **Error:** OpenAI embedding errors (e.g., RateLimitError).
*   **Solution:** The script has built-in retries. If it persists, you might be hitting OpenAI rate limits. Wait and try again, or consider reducing the `--batch-size` for `ingest.py`.

### Query Errors

*   **Error:** "No results found for query".
*   **Reason:** The vector database might not contain errors sufficiently similar to your query. The CodeInsight dataset, while large, may not cover every possible error.
*   **Error:** LLM generation errors (e.g., API timeout, OpenRouter errors).
*   **Solution:** The system has retries built-in. Check OpenRouter's status page if errors persist. Ensure your `OPENROUTER_API_KEY` is valid and has credits/access. Try simplifying your query or adjusting parameters like `temperature`.
*   **Error:** API returns 500 Internal Server Error.
*   **Solution:** Check the logs of the `uvicorn` server for more detailed error messages.

### Performance Issues

*   **Slow Ingestion:** Embedding generation can be slow, especially for large datasets. This is largely dependent on the OpenAI API response time. Consider using the `--limit` flag during initial testing.
*   **Slow Queries:** Query time depends on embedding generation (fast), vector search (fast), and LLM generation (can be slow). LLM response time varies significantly based on the chosen model and current server load on OpenRouter.

### Checking System Health

Use the API's health check endpoint to verify component status:

```bash
curl http://localhost:8000/api/v1/health
```

This will show the status (`ok`, `degraded`, `error`) and the individual status of API keys and the vector store connection.

For the SRE RAG subsystem specifically, use the validation script:

```bash
python src/scripts/validate_sre_rag.py
```

This provides a comprehensive health check of the SRE incident RAG system, including collection status, embedding quality, and retrieval performance.