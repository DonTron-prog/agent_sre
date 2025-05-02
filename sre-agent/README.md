# SRE Agent

## Overview

The SRE Agent is an intelligent system designed to assist Site Reliability Engineers (SREs) by automating the initial analysis and diagnosis of alerts. Built using LangGraph, it orchestrates a workflow to process incoming alerts, gather relevant context from various sources, and provide actionable recommendations.

**Purpose:**

*   Reduce Mean Time To Acknowledge (MTTA) and Mean Time To Resolve (MTTR) for incidents.
*   Provide consistent and data-driven initial diagnosis for alerts.
*   Leverage historical data and documentation through Retrieval-Augmented Generation (RAG).
*   Integrate with infrastructure monitoring and topology information.

**Key Features:**

*   **LangGraph Workflow:** Utilizes a graph-based approach for flexible and robust alert processing logic, including planning, execution simulation, reflection, and recommendation generation.
*   **RAG Integration:** Connects with the `code-rag` system to retrieve relevant context (e.g., past incidents, runbooks, documentation) based on alert details.
*   **Infrastructure Awareness:** Can integrate with infrastructure data sources to understand system topology and dependencies (via `services/infra_service.py`).
*   **Modular Design:** Components like LangGraph nodes (`graph/nodes/`), service adapters (`services/`), and the API layer (`api/`) are organized for maintainability and extension.
*   **Extensible Alert Handling:** Designed to process various alert types through configurable processing steps.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd agent_sre/sre-agent
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    The project uses `pyproject.toml` for dependency management. Install the agent and its dependencies, including LangGraph:
    ```bash
    pip install -e .
    ```
    *Note: This command installs the package in editable mode.*

## Configuration

The SRE Agent requires configuration, typically managed through environment variables or a configuration file (`src/sre_agent/config/settings.py`). Key configuration areas include:

*   **RAG System:**
    *   Endpoint URL for the `code-rag` API service.
    *   Authentication details (if required).
*   **Infrastructure Graph/Service:**
    *   Connection details for the infrastructure data source (e.g., API endpoint, database connection string).
    *   Credentials for accessing infrastructure data.
*   **LLM Configuration:**
    *   API keys and model names for the Language Models used in the LangGraph workflow.

Refer to `src/sre_agent/config/settings.py` and potentially an `.env.example` file (if provided in the project root) for specific variable names and formats.

## Usage

### Process Alerts Manually

You can process sample alerts or specific alerts manually using the example script:

```bash
python examples/run_workflow.py --alert-file examples/sample_alerts.json
```

*   Modify `examples/sample_alerts.json` or provide a different file path with alerts conforming to the expected format (see `src/sre_agent/models/alert.py`).
*   The script will execute the LangGraph workflow for each alert and print the results, including generated recommendations.

### Run the Agent as a Service

The agent includes an API layer built with FastAPI (defined in `src/sre_agent/api/main.py`). To run it as a service:

1.  Ensure all configurations (environment variables) are set correctly.
2.  Run the FastAPI application using Uvicorn:
    ```bash
    uvicorn sre_agent.api.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `--reload` is useful for development. Remove it for production deployments.
3.  The API service will be available at `http://localhost:8000`. You can send alerts to the appropriate endpoint (e.g., `/process-alert`) via HTTP requests. Check `src/sre_agent/api/main.py` for specific endpoint definitions.

### Interpret Recommendations

The agent's output typically includes:

*   **Analysis:** A summary of the alert and findings from the RAG lookup and infrastructure context.
*   **Recommendations:** Suggested actions or investigation steps based on the analysis. These might include specific commands to run, documentation links, or potential root causes.
*   **Confidence Score:** (Optional) An indicator of the agent's confidence in its recommendations.

Review the analysis and recommendations carefully. They are intended as starting points for SRE investigation, not definitive solutions.

## Example Alerts

Here are examples of the alert format the agent expects (as found in `examples/sample_alerts.json`):

```json
{
  "id": "alert-001",
  "type": "PodCrashLoop",
  "summary": "Pod auth-service-xyz-pod in cluster-alpha is in CrashLoopBackOff",
  "details": "The pod auth-service-xyz-pod has restarted 5 times in 15 minutes"
}
```

```json
{
  "id": "alert-002",
  "type": "LatencySpike",
  "summary": "High latency observed for payment-service requests in us-east-1",
  "details": "99th percentile latency increased from 200ms to 1.2s in the last 10 minutes"
}
```

```json
{
  "id": "alert-003",
  "type": "DeployFail",
  "summary": "Deployment failed for auth-service version 2.4.0 in ProjectA",
  "details": "New deployment rollout halted due to errors in startup health check"
}
```

## Integration with code-rag

The SRE Agent leverages the `code-rag` system to enhance its diagnostic capabilities. This integration works as follows:

1.  **RAG Lookup Node:** The LangGraph workflow includes a dedicated node (`src/sre_agent/graph/nodes/rag_lookup.py`) responsible for querying the RAG system.
2.  **Contextual Queries:** When an alert is processed, this node formulates queries based on the alert's summary, details, type, and potentially related infrastructure components.
3.  **Retrieval:** The `code-rag` service (`src/sre_agent/services/rag_service.py` likely handles the communication) receives these queries and searches its knowledge base (containing indexed documentation, past incident reports, runbooks, etc.).
4.  **Augmentation:** The relevant information retrieved from `code-rag` is returned to the SRE Agent's workflow.
5.  **Informed Recommendations:** Subsequent nodes in the LangGraph workflow (e.g., planning, recommendation) use this augmented context, alongside real-time data, to generate more accurate analyses and actionable recommendations.

This integration allows the agent to benefit from historical knowledge and documented procedures, leading to more informed and relevant suggestions for SREs.