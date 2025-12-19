# 🔍 Agentic Research Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**An LLM-powered research assistant that generates comprehensive reports using Wikipedia as a knowledge source.**

[Features](#-features) •
[Quick Start](#-quick-start) •
[Architecture](#-architecture) •
[API Reference](#-api-reference) •
[Configuration](#%EF%B8%8F-configuration)

</div>

---

## 📖 Overview

**Agentic Research Assistant** is an intelligent research tool that leverages OpenAI's GPT models to generate well-structured research reports. It implements an **agentic pattern** where the AI autonomously decides when to search Wikipedia and gather information to answer your research questions.

### What makes it "Agentic"?

Unlike simple chatbots, this assistant:
- 🧠 **Reasons** about what information it needs
- 🔍 **Searches** Wikipedia autonomously using tool calls
- 📚 **Synthesizes** multiple sources into coherent reports
- 📄 **Generates** downloadable artifacts (Markdown, PDF, JSON)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Multimodal Input** | Submit text prompts with optional images (PNG, JPG, WebP) for visual analysis |
| 🌐 **External Data Source** | Automatic Wikipedia search and summary retrieval (no API key needed) |
| 📊 **High Context Handling** | Large text inputs are automatically chunked and summarized |
| ⚡ **Async Job Processing** | Background job queue with Redis + RQ for long-running tasks |
| 📁 **File Output** | Generates `report.md`, `report.pdf`, and `sources.json` for each job |
| 🐳 **Docker Ready** | One-command deployment with Docker Compose |
| 🔧 **Local Dev Mode** | Run without Redis using `USE_FAKE_REDIS=true` |

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Chouaib6801/agentic-app-bonus.git
cd agentic-app-bonus

# 2. Create your .env file
cp .env.example .env

# 3. Add your OpenAI API key to .env
# Edit .env and set: OPENAI_API_KEY=sk-your-key-here

# 4. Start all services
docker compose up --build

# 5. Open http://localhost:8000
```

### Option 2: Local Development (No Docker)

```bash
# 1. Clone and setup
git clone https://github.com/Chouaib6801/agentic-app-bonus.git
cd agentic-app-bonus

# 2. Create virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and USE_FAKE_REDIS=true

# 5. Run the server
python -m uvicorn app.main:app --reload --port 8000

# 6. Open http://localhost:8000
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER BROWSER                                  │
│                         http://localhost:8000                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  📝 Prompt    │  🖼️ Image (opt)  │  📄 Context (opt)  │  ▶️ Run  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP POST /jobs
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER (:8000)                           │
│                                                                          │
│   POST /jobs ──────────────► Enqueue job to Redis                       │
│   GET  /jobs/{id} ─────────► Check job status                           │
│   GET  /jobs/{id}/files ───► List output files                          │
│   GET  /jobs/{id}/download ► Download files                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
┌──────────────────────────┐    ┌─────────────────────────────────────────┐
│      REDIS QUEUE         │    │              RQ WORKER                   │
│  ┌────────────────────┐  │    │                                          │
│  │ Job: abc-123       │◄─┼────┤  ┌────────────────────────────────────┐  │
│  │ Status: queued     │  │    │  │         RESEARCH AGENT              │  │
│  └────────────────────┘  │    │  │                                      │  │
└──────────────────────────┘    │  │  1. Process context (chunk/summarize)│  │
                                │  │  2. Extract search query via LLM     │  │
                                │  │  3. wikipedia_search(query)          │  │
                                │  │  4. wikipedia_summary(title) x3      │  │
                                │  │  5. Generate report via LLM          │  │
                                │  │  6. Create PDF with ReportLab        │  │
                                │  │                                      │  │
                                │  └────────────────────────────────────┘  │
                                │                    │                     │
                                │                    ▼                     │
                                │  ┌────────────────────────────────────┐  │
                                │  │        OUTPUT FILES                 │  │
                                │  │   📄 report.md   (Markdown report)  │  │
                                │  │   📕 report.pdf  (PDF version)      │  │
                                │  │   📋 sources.json (Tool outputs)    │  │
                                │  └────────────────────────────────────┘  │
                                └─────────────────────────────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Server** | FastAPI + Uvicorn | HTTP endpoints, file serving, job management |
| **Job Queue** | Redis + RQ | Async task queue for background processing |
| **Research Agent** | OpenAI GPT-4o | LLM reasoning, tool orchestration, report generation |
| **Wikipedia Tools** | MediaWiki API | External knowledge retrieval (no API key) |
| **PDF Generator** | ReportLab | Convert Markdown reports to PDF |

---

## 📡 API Reference

### Submit a Job

```http
POST /jobs
Content-Type: multipart/form-data
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | ✅ | Research question or topic |
| `image` | file | ❌ | Image for multimodal analysis (PNG/JPG/WebP) |
| `context_text` | string | ❌ | Additional context (large text supported) |

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/jobs/550e8400-e29b-41d4-a716-446655440000",
  "result_url": "/jobs/550e8400-e29b-41d4-a716-446655440000/files"
}
```

### Check Job Status

```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "finished",
  "files": ["report.md", "report.pdf", "sources.json"],
  "download_urls": {
    "report.md": "/jobs/.../download/report.md",
    "report.pdf": "/jobs/.../download/report.pdf",
    "sources.json": "/jobs/.../download/sources.json"
  }
}
```

**Status Values:**
| Status | Description |
|--------|-------------|
| `queued` | Job waiting in queue |
| `started` | Job is being processed |
| `finished` | Job completed successfully |
| `failed` | Job failed (check `error` field) |

### List Job Files

```http
GET /jobs/{job_id}/files
```

### Download File

```http
GET /jobs/{job_id}/download/{filename}
```

### Health Check

```http
GET /health
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional
OPENAI_MODEL=gpt-4o-mini          # Model to use (default: gpt-4o-mini)
REDIS_URL=redis://localhost:6379  # Redis connection URL
DATA_DIR=./data                   # Output directory for job files
USE_FAKE_REDIS=false              # Set to 'true' for local dev without Redis
```

### Supported OpenAI Models

| Model | Best For |
|-------|----------|
| `gpt-4o-mini` | Fast, cost-effective (default) |
| `gpt-4o` | Higher quality, multimodal |
| `gpt-4-turbo` | Balance of speed and quality |

---

## 📂 Project Structure

```
agentic-app-bonus/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application & endpoints
│   ├── queue.py              # Redis/fakeredis connection handling
│   ├── worker.py             # RQ worker process
│   ├── tasks.py              # Background job definitions
│   ├── agent.py              # Research agent with LLM integration
│   ├── tools_wikipedia.py    # Wikipedia API tools
│   ├── utils_files.py        # PDF generation utilities
│   └── static/
│       └── index.html        # Web UI
├── data/
│   └── jobs/                 # Output files per job (gitignored)
├── .env.example              # Environment template
├── .gitignore
├── requirements.txt          # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── README.md
└── TODO.md
```

---

## 🔧 How It Works

### 1. High Context Handling

When you provide large text input (>15,000 characters):

```
Input Text (50,000 chars)
         │
         ▼
┌─────────────────────────────┐
│  Chunk into ~12,000 chars   │
│  [Chunk 1] [Chunk 2] [...]  │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Summarize each chunk       │
│  via LLM                    │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Merge summaries            │
│  → Condensed context        │
└─────────────────────────────┘
```

### 2. Agentic Tool Usage

The agent uses a pragmatic tool-calling pattern:

```python
# 1. Extract search query from user prompt
query = llm.extract_topic(prompt)  # "climate change effects"

# 2. Search Wikipedia
titles = wikipedia_search(query, limit=5)
# → ["Climate change", "Effects of climate change", ...]

# 3. Get summaries for top results
for title in titles[:3]:
    summary = wikipedia_summary(title)
    sources.append(summary)

# 4. Generate report with all gathered information
report = llm.generate_report(prompt, sources, context)
```

### 3. Output Generation

Each completed job produces:

| File | Format | Content |
|------|--------|---------|
| `report.md` | Markdown | Structured report with sections and references |
| `report.pdf` | PDF | Formatted version for printing/sharing |
| `sources.json` | JSON | All tool calls and their outputs |

---

## 🐳 Docker Services

```yaml
services:
  redis:      # Message queue
  api:        # FastAPI server (port 8000)
  worker:     # Background job processor
```

**Commands:**
```bash
# Start all services
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up --build
```

---

## 🧪 Example Usage

### Via Web UI

1. Open http://localhost:8000
2. Enter: "What are the main causes and effects of climate change?"
3. (Optional) Upload an image
4. (Optional) Paste additional context
5. Click "Run Research"
6. Wait for completion, then download your report

### Via cURL

```bash
# Submit a job
curl -X POST http://localhost:8000/jobs \
  -F "prompt=Explain quantum computing and its applications"

# Check status
curl http://localhost:8000/jobs/{job_id}

# Download report
curl -O http://localhost:8000/jobs/{job_id}/download/report.pdf
```

### Via Python

```python
import requests

# Submit job
response = requests.post(
    "http://localhost:8000/jobs",
    data={"prompt": "History of artificial intelligence"}
)
job_id = response.json()["job_id"]

# Poll for completion
import time
while True:
    status = requests.get(f"http://localhost:8000/jobs/{job_id}").json()
    if status["status"] == "finished":
        break
    time.sleep(2)

# Download report
report = requests.get(f"http://localhost:8000/jobs/{job_id}/download/report.md")
print(report.text)
```

---

## ✅ Requirements Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Multimodal prompt input | ✅ | Image uploaded as base64 data URL to GPT-4 Vision |
| File output | ✅ | Generates report.md, report.pdf, sources.json |
| External data source | ✅ | Wikipedia API (search + summary, no key needed) |
| High context handling | ✅ | Chunking at 12K chars + LLM summarization |
| Queue + worker pattern | ✅ | Redis + RQ with async job processing |
| Runnable by evaluator | ✅ | Docker Compose with 3 services |
| Clear documentation | ✅ | This README + inline code comments |

---

## ⚠️ Trade-offs & Limitations

Given the timeboxing constraint, the following trade-offs were made:

| What's Missing | Why | Future Solution |
|----------------|-----|-----------------|
| Authentication | MVP scope | Add JWT or API keys |
| Job persistence | Redis-only storage | Add PostgreSQL/SQLite |
| Retry logic | Complexity | Implement exponential backoff |
| Rate limiting | MVP scope | Add slowapi middleware |
| Unit tests | Time constraint | Add pytest suite |
| Streaming | Complexity | SSE or WebSocket |

---

## 🚧 Future Improvements

See [TODO.md](TODO.md) for the complete roadmap. Key items:

- [ ] Add more data sources (ArXiv, news APIs)
- [ ] Implement proper citation formatting
- [ ] Add job cancellation
- [ ] Create React/Vue frontend
- [ ] Add comprehensive test suite
- [ ] Implement result caching

---

## 📝 License

MIT License - feel free to use this project for any purpose.

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for GPT models
- [Wikipedia](https://wikipedia.org) for the free knowledge API
- [FastAPI](https://fastapi.tiangolo.com) for the excellent web framework
- [RQ](https://python-rq.org) for simple job queuing

---

<div align="center">

**Built with ❤️ as a demonstration of agentic AI patterns**

*Timeboxing: 2 hours*

</div>
