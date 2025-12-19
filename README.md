# Agentic Research Assistant

An LLM-powered research assistant that uses Wikipedia as an external data source to generate comprehensive research reports. Supports multimodal input (text + images), handles large context through chunking and summarization, and runs background jobs using a Redis queue.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                    (index.html - Simple UI)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (:8000)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ POST /jobs   │  │ GET /jobs/id │  │ GET /jobs/id/download │  │
│  │ (submit job) │  │ (check stat) │  │ (get files)           │  │
│  └──────┬───────┘  └──────────────┘  └───────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │ Enqueue
          ▼
┌─────────────────────┐         ┌─────────────────────────────────┐
│    Redis Queue      │◄────────│         RQ Worker               │
│    (tasks)          │ Poll    │  ┌───────────────────────────┐  │
└─────────────────────┘         │  │    Research Agent         │  │
                                │  │  ┌─────────────────────┐  │  │
                                │  │  │ Wikipedia Tools     │  │  │
                                │  │  │ - search(query)     │  │  │
                                │  │  │ - summary(title)    │  │  │
                                │  │  └─────────────────────┘  │  │
                                │  │  ┌─────────────────────┐  │  │
                                │  │  │ OpenAI LLM          │  │  │
                                │  │  │ (gpt-4o-mini)       │  │  │
                                │  │  └─────────────────────┘  │  │
                                │  └───────────────────────────┘  │
                                │              │                   │
                                │              ▼                   │
                                │  ┌───────────────────────────┐  │
                                │  │   Output Files            │  │
                                │  │   - report.md             │  │
                                │  │   - report.pdf            │  │
                                │  │   - sources.json          │  │
                                │  └───────────────────────────┘  │
                                └─────────────────────────────────┘
```

## Requirements Satisfied

| Requirement | Implementation |
|-------------|----------------|
| **Multimodal Input** | Accepts text prompt + optional image (PNG/JPG/WebP). Image is encoded as base64 data URL and sent to OpenAI's vision model. |
| **File Output** | Generates three files per job: `report.md` (Markdown report), `report.pdf` (PDF version), `sources.json` (tool outputs). |
| **External Data Source** | Uses Wikipedia API (no key required) via `wikipedia_search()` and `wikipedia_summary()` tools. |
| **High Context Handling** | Large text inputs (>15,000 chars) are chunked into ~12,000 char segments, summarized individually, then merged. |
| **Queue + Worker Pattern** | Uses Redis + RQ for async job processing. API enqueues jobs, worker processes them in background. |
| **Cross-Platform/Runnable** | Docker Compose setup with `api`, `worker`, and `redis` services. |

## Setup Instructions

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentic-app-bonus
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Open the application**
   
   Navigate to [http://localhost:8000](http://localhost:8000)

### Option 2: Local Development (venv)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis** (required)
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or install Redis locally
   ```

4. **Set environment variables**
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="sk-your-key-here"
   
   # macOS/Linux
   export OPENAI_API_KEY="sk-your-key-here"
   ```

5. **Start the API server** (Terminal 1)
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Start the worker** (Terminal 2)
   ```bash
   python -m app.worker
   ```

## How to Run a Job

1. **Open the UI** at [http://localhost:8000](http://localhost:8000)

2. **Enter your research prompt** (required)
   - Example: "What are the main causes and effects of climate change?"

3. **Optionally upload an image** (PNG, JPG, or WebP)
   - The image will be analyzed along with your prompt

4. **Optionally paste large context text**
   - Large texts are automatically chunked and summarized

5. **Click "Run Research"**
   - You'll receive a job ID
   - Status will update automatically (queued → started → finished)

## How to Retrieve Results

### Via UI
- Once the job finishes, download links appear automatically
- Click on `report.md`, `report.pdf`, or `sources.json` to download

### Via API

```bash
# Check job status
curl http://localhost:8000/jobs/{job_id}

# List available files
curl http://localhost:8000/jobs/{job_id}/files

# Download specific file
curl -O http://localhost:8000/jobs/{job_id}/download/report.pdf
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve HTML UI |
| `POST` | `/jobs` | Submit a new research job |
| `GET` | `/jobs/{job_id}` | Get job status |
| `GET` | `/jobs/{job_id}/files` | List output files |
| `GET` | `/jobs/{job_id}/download/{filename}` | Download a file |
| `GET` | `/health` | Health check |

## Output Files

Each completed job produces:

- **`report.md`** - Structured Markdown report with title, sections, and references
- **`report.pdf`** - PDF version of the report (generated with ReportLab)
- **`sources.json`** - JSON log of all Wikipedia tool calls and their outputs

## Trade-offs / What's Missing

Given the 2-hour timeboxing constraint, the following trade-offs were made:

1. **Simple UI** - Basic HTML/CSS/JS, no framework (React, Vue, etc.)
2. **No authentication** - Jobs are publicly accessible by ID
3. **No job persistence** - Jobs are lost when Redis restarts (no persistent backend)
4. **Basic PDF styling** - Simple text-based PDF, no fancy formatting
5. **No retry logic** - Failed jobs are not automatically retried
6. **No rate limiting** - API could be abused without limits
7. **No tests** - No unit or integration tests
8. **Minimal error handling** - Basic error capture, could be more robust
9. **No streaming** - Results returned only when complete
10. **Single worker** - Could scale horizontally with more workers

## Timeboxing: 2 Hours

This project was built with a strict 2-hour time constraint in mind. The focus was on:
- Working end-to-end functionality
- Clear architecture and code organization
- Meeting all core requirements
- Pragmatic implementation over perfection

## License

MIT

