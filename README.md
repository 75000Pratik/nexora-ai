# Nexora AI

**Production Agentic Knowledge Intelligence Platform**

Nexora AI is a production-oriented AI platform designed to answer complex questions from organizational knowledge using advanced retrieval, agentic workflows, grounded generation, and measurable evaluation.

## Project Goal

The goal of Nexora AI is to go beyond basic vector-based RAG systems by combining:

- Multi-document ingestion
- Hybrid dense + sparse retrieval
- Metadata filtering
- Cross-encoder reranking
- Grounded response generation
- Source citations and claim-level validation
- Agent routing and tool calling
- Evaluation pipelines
- Production backend engineering
- Authentication and tenant isolation
- Structured logging and request tracking
- Containerization and deployment

## Current Status

The project has progressed beyond its initial foundation phase.

### Completed

- Python 3.12 development environment
- FastAPI backend architecture
- PostgreSQL database integration
- SQLAlchemy ORM and Alembic migrations
- JWT authentication and Argon2 password hashing
- User ownership and project-based data isolation
- PDF document ingestion and validation
- Qdrant vector database integration
- Dense and sparse hybrid retrieval
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Ollama LLM integration
- Grounded answer generation
- Source citations and claim-level citation validation
- Request ID middleware
- Structured JSON logging
- API health and readiness endpoints
- Automated tests with pytest
- Docker image and non-root container execution
- Docker Compose orchestration
- Persistent PostgreSQL and Qdrant volumes

## Architecture

```text
User
  |
  v
FastAPI
  |
  +------ Authentication / Authorization
  |
  +------ Project and Document Management
  |
  v
Agent Orchestrator
  |
  v
Hybrid Retrieval
  |
  +------ Dense Retrieval (Qdrant)
  |
  +------ Sparse Retrieval (BM25)
  |
  v
Reciprocal Rank Fusion
  |
  v
Cross-Encoder Reranking
  |
  v
Grounded LLM Response (Ollama)
  |
  v
Citation and Claim Validation
  |
  v
Response with Sources
```

## Technology Stack

| Category         | Technology             |
| ---------------- | ---------------------- |
| Language         | Python 3.12            |
| Backend          | FastAPI                |
| Validation       | Pydantic               |
| Database         | PostgreSQL 17          |
| ORM              | SQLAlchemy             |
| Migrations       | Alembic                |
| Vector Database  | Qdrant                 |
| Embeddings       | Sentence Transformers  |
| Retrieval        | Dense + BM25           |
| Rank Fusion      | Reciprocal Rank Fusion |
| Reranking        | Cross-Encoder          |
| LLM Runtime      | Ollama                 |
| LLM Model        | Qwen 2.5 1.5B          |
| PDF Processing   | pypdf                  |
| Authentication   | JWT + Argon2           |
| Testing          | pytest                 |
| Containerization | Docker                 |
| Orchestration    | Docker Compose         |

## Project Structure

```text
nexora-ai/
|-- app/
|   |-- api/
|   |-- core/
|   |-- models/
|   |-- repositories/
|   |-- schemas/
|   |-- services/
|   |-- utils/
|   `-- main.py
|-- docs/
|-- migrations/
|-- scripts/
|-- tests/
|-- uploads/
|-- Dockerfile
|-- compose.yaml
|-- .dockerignore
|-- .env.example
|-- requirements.txt
|-- alembic.ini
`-- README.md
```

## Running with Docker Compose

### Prerequisites

- Docker Desktop
- Docker Compose
- Ollama installed and running on the Windows host
- Required Ollama model available locally

### Environment Configuration

Create the following local environment files in the project root. These files are intentionally excluded from Git.

**1. `.env.compose`**

Contains the API configuration:

```dotenv
DATABASE_URL=postgresql+psycopg://nexora:YOUR_PASSWORD@postgres:5432/nexora
JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://host.docker.internal:11434
```

Use the actual PostgreSQL password configured for your database. Generate a strong JWT secret of at least 32 characters.

**2. `.env.postgres`**

Contains PostgreSQL initialization settings:

```dotenv
POSTGRES_USER=nexora
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_DB=nexora
```

The PostgreSQL password must match the password in `.env.compose`.

Do not commit these files or expose their secret values.

### Persistent Volumes

The Compose configuration uses two external Docker volumes:

- `nexora_postgres_data` — PostgreSQL database storage
- `nexora_qdrant_storage` — Qdrant vector storage

These volumes must exist before starting the Compose services. Existing deployments should reuse their existing volumes to preserve data.

### Start Ollama

Ensure Ollama is running on the Windows host and the configured model is available:

```powershell
ollama list
```

The default configuration uses:

```text
qwen2.5:1.5b
```

### Start Nexora AI

Open PowerShell in the project directory:

```powershell
docker compose up -d
```

To rebuild the API image after code or dependency changes:

```powershell
docker compose up -d --build
```

### Check Container Status

```powershell
docker compose ps
```

### Check Application Readiness

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

A successful response should report:

- `status`: `ready`
- `database`: `True`
- `qdrant`: `True`
- `ollama`: `True`

### View Logs

```powershell
docker compose logs --tail 50
```

To inspect only API logs:

```powershell
docker compose logs --tail 50 api
```

### Stop Services

```powershell
docker compose down
```

**Important:** Do not use `docker compose down -v` for routine shutdown. Preserve the PostgreSQL and Qdrant persistent volumes.

## Testing

Run the automated test suite from the Python virtual environment:

```powershell
pytest -v
```

## Development Principles

This project is being built with the following principles:

- No fabricated benchmark results
- No unnecessary architectural complexity
- Measurable retrieval and generation quality
- Production-style backend design
- Security-aware AI engineeringgit diff --check

- Automated testing from early development
- Clean Git history
- Clear documentation of design decisions
- Persistent and recoverable application data

## Author

Pratik Tekade
