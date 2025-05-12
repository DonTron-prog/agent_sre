# Agent SRE: Agentic Site Reliability Engineering

A comprehensive LLM-powered solution for automating SRE alert analysis, incident investigation, and resolution recommendation.

## Overview

Agent SRE is a modular system that combines a LangGraph-based SRE agent with Retrieval-Augmented Generation (RAG) component to automate the initial analysis and diagnosis of alerts. The system leverages historical incident data and infrastructure topology to provide actionable recommendations for resolving incidents faster.

This project consists of two main components:

1. **SRE Agent**: A LangGraph workflow-based system that processes alerts through planning, execution, reflection, and recommendation phases.
2. **Code RAG**: A specialized RAG component for retrieving similar incidents and their solutions from a vector database.

## Components

### SRE Agent (`./sre-agent`)

The SRE Agent processes alerts through a flexible LangGraph workflow:

1. **Planning**: Creates an investigation plan with specific tasks
2. **Task Execution**: Executes each task systematically
3. **RAG Lookup**: Queries the Code RAG system for similar incidents
4. **Reflection**: Analyzes findings and refines the approach
5. **Recommendation**: Generates actionable recommendations

For more details, see [SRE Agent documentation](./sre-agent/README.md).

### Code RAG (`./code-rag`)

Code RAG is a retrieval-augmented generation system specialized for SRE incidents:

* Maintains a vector database of past incidents and their solutions
* Generates embeddings for alerts and uses similarity search to find relevant incidents
* Augments LLM prompts with retrieved context for better recommendations

For more details, see [Code RAG documentation](./code-rag/README.md).

## Installation

### Prerequisites

* Python 3.8+
* A working installation of ChromaDB
* API keys for OpenAI (embeddings) and OpenRouter (LLMs)

### Clone the Repository

```bash
git clone https://github.com/DonTron-prog/agent_sre
cd agent_sre
```

### Set Up Each Component

1. **Code RAG Setup**:
   ```bash
   cd code-rag
   python -m venv venv
   source venv/bin/activate  
   pip install -e .
   cp .env.example .env  # Edit .env with your API keys
   ```

2. **SRE Agent Setup**:
   ```bash
   cd ../sre-agent
   python -m venv venv
   source venv/bin/activate  
   pip install -e .
   ```

### Data Preparation

1. **Generate and Ingest SRE Incident Data**:
   ```bash
   # Activate Code RAG environment
   cd code-rag
   source venv/bin/activate  
   
   # Generate synthetic SRE incident data
   python src/scripts/generate_sre_documents.py
   
   # Ingest the generated data into ChromaDB
   python src/scripts/ingest_sre_documents.py
   ```

## Usage

### Running the Complete System

1. **Start the Code RAG API**:
   ```bash
   # In terminal 1
   cd code-rag
   source venv/bin/activate
   uvicorn code_rag.api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start the SRE Agent API**:
   ```bash
   # In terminal 2
   cd sre-agent
   source venv/bin/activate
   uvicorn sre_agent.api.main:app --host 0.0.0.0 --port 8001
   ```

3. **Process an Alert**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '{
              "id": "alert-001",
              "type": "PodCrashLoop",
              "summary": "Pod auth-service-xyz-pod in cluster-alpha is in CrashLoopBackOff",
              "details": "The pod auth-service-xyz-pod has restarted 5 times in 15 minutes"
            }'
   ```

### Example Alert Formats

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

### Example Response

```json
{
  "alert_id": "alert-001",
  "alert_type": "PodCrashLoop",
  "recommendation_text": "Based on the analysis of the CrashLoopBackOff state of the auth-service-xyz-pod, I recommend checking the following:\n\n1. Review the container logs using: `kubectl logs auth-service-xyz-pod -n default`\n2. Check for resource constraints: `kubectl describe pod auth-service-xyz-pod -n default`\n3. Verify the container's health checks are properly configured\n\nThe most likely cause is a configuration issue in the application startup parameters, as indicated by similar past incidents.",
  "similar_incidents": [
    {
      "error": "Pod auth-service-abc-pod in cluster-beta is in CrashLoopBackOff",
      "solution": "Issue was resolved by correcting the environment variables in the deployment manifest. The application was expecting a DATABASE_URL but was receiving DATABASE_URI instead.",
      "similarity_score": 0.89
    }
  ],
  "completed_tasks": [
    "Check similar past incidents",
    "Analyze pod configuration",
    "Review cluster state"
  ],
  "investigation_summary": "The auth-service pod is failing to start properly. Similar incidents suggest a configuration issue rather than a resource constraint problem."
}
```

## Configuration

The system uses environment variables for configuration. Key variables include:

### Code RAG Configuration

```
OPENAI_API_KEY="sk-..."
OPENROUTER_API_KEY="sk-or-..."
CODE_RAG_EMBEDDING_MODEL="text-embedding-ada-002"
CODE_RAG_LLM_MODEL="openai/gpt-3.5-turbo"
CODE_RAG_CHROMA_PATH="./chroma_db"
```

### SRE Agent Configuration

```
OPENAI_API_KEY="sk-..."
OPENROUTER_API_KEY="sk-or-..."
SRE_AGENT_EMBEDDING_MODEL="text-embedding-ada-002"
SRE_AGENT_LLM_MODEL="mistralai/mistral-7b-instruct:latest"
SRE_AGENT_DEFAULT_NUM_RESULTS=3
```

## Project Structure

```
agent_sre/
├── README.md                  # This file
├── architecture.md            # Detailed architecture documentation
├── code-rag/                  # RAG component for similar incident retrieval
│   ├── README.md              # Code RAG documentation
│   ├── src/
│   │   └── code_rag/          # RAG implementation
│   └── data/                  # Raw and processed data
│
├── sre-agent/                 # SRE Agent component
│   ├── README.md              # SRE Agent documentation
│   ├── src/
│   │   └── sre_agent/         # Agent implementation
│   │       ├── api/           # FastAPI implementation
│   │       ├── graph/         # LangGraph workflow
│   │       ├── models/        # Data models
│   │       └── services/      # External service integrations
│   └── examples/              # Example scripts and alerts
│
├── chroma_db/                 # Shared ChromaDB storage
└── data/                      # Shared data directory
    └── raw/                   # Raw data files
        └── sre_incidents.json # SRE incident data
```

## Development

### Extending the System

1. **Add New Alert Types**:
   - Update the alert processing logic in the SRE Agent
   - Add relevant synthetic data to the RAG system

2. **Integrate Additional Data Sources**:
   - Extend the Infrastructure Graph Service in the SRE Agent
   - Add new connectors in the services directory

3. **Improve Recommendations**:
   - Enhance the recommendation node in the LangGraph workflow
   - Update the prompting strategy

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
