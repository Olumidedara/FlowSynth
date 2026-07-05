<div align="center">

# FlowSynth

### AI-Powered Multi-Agent Research Pipeline

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-339933?style=flat&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLM-F97316?style=flat&logo=groq&logoColor=white)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/Neon-PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://neon.tech)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat)](LICENSE)

</div>

---

## The Story

You have a question. You need a well-researched, polished article and not a messy pile of search tabs and half-read links.

FlowSynth is your **AI research team in a box**. It doesn't just search the web and dump results. It orchestrates six specialised AI agents that work together like a tiny editorial department:

→ A **strategist** plans your research.  
→ A **librarian** scours the web for sources.  
→ An **analyst** connects the dots between findings.  
→ A **writer** crafts the narrative.  
→ A **critic** reviews the work (and sends it back if it's not good enough).  
→ A **finalizer** polishes the final draft.

All of this happens automatically, in about a minute and it costs exactly **zero dollars**.

---

## Pipeline Architecture

```
                      +------------------+
                      |   Orchestrator   |  Creates research plan
                      +--------+---------+
                               |
                               v
                      +------------------+
                      |   Researcher     |  Searches the web (DuckDuckGo)
                      +--------+---------+
                               |
                               v
                      +------------------+
                      |   Analyst        |  Extracts insights & patterns
                      +--------+---------+
                               |
                               v
                      +------------------+
                      |   Writer         |  Drafts the article
                      +--------+---------+
                               |
                               v
                      +------------------+
                      |   Reviewer       |  Scores 1-10, gives feedback
                      +--------+---------+
                               |
                 +-------------+-------------+
                 |                           |
          (score < 7)                  (score >= 7)
          (revisions < 3)              (revisions >= 3)
                 |                           |
                 v                           v
          +----------+              +------------------+
          |  Writer  |  (revise)    |   Finalizer      |  Polish & output
          +----------+              +--------+---------+
                                               |
                                               v
                                        DONE ✓
```

---

## The Six Agents

| # | Agent | What it does |
|---|-------|-------------|
| 1 | **Orchestrator** | Breaks your query into 2–4 subtopics with targeted search questions. |
| 2 | **Researcher** | Runs up to 4 DuckDuckGo searches, collecting 10+ results with snippets. |
| 3 | **Analyst** | Examines findings for key insights, contradictions, gaps, and connections. |
| 4 | **Writer** | Produces a structured article — introduction, body sections, conclusion. |
| 5 | **Reviewer** | Scores the draft (1–10) on accuracy, completeness, structure, and clarity. Returns feedback + verdict. |
| 6 | **Finalizer** | Polishes the final draft, adds a summary, ensures clean formatting. |

The review loop runs up to **3 revision cycles**; if the critic isn't satisfied, the writer goes back to work with specific feedback. Once the score hits 7+ or max revisions are reached, the finalizer takes over.

---

## Features

- **Six AI agents** working in sequence with a quality review loop
- **Groq** with three-model fallback chain — free LLMs, no credit card
- **DuckDuckGo search** — free, no API key
- **Real-time progress** — see each agent work as it happens
- **User accounts** — JWT authentication with 48h sessions
- **Research history** — saved to PostgreSQL (Neon), browseable and searchable
- **Delete research** — clean up your history
- **Markdown rendering** — articles displayed with proper formatting
- **Dark/light theme** — persisted in localStorage
- **Responsive design** — works on desktop and mobile
- **Zero cost** — no paid APIs, no paid hosting

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com) + [Jinja2](https://jinja.palletsprojects.com) | Web server + server-side rendering |
| **Pipeline** | [LangGraph](https://langchain-ai.github.io/langgraph/) | State graph for agent orchestration |
| **Primary LLM** | [Groq](https://groq.com) (`llama-3.1-8b-instant`) | Fast inference at zero cost |
| **Fallback LLMs** | [Groq](https://groq.com) (`llama-3.3-70b-versatile`, `gemma2-9b-it`) | Auto-fallback on rate limits |
| **Search** | [DuckDuckGo](https://duckduckgo.com) (via `ddgs`) | Web search, no API key |
| **Database** | [Neon](https://neon.tech) PostgreSQL via `asyncpg` | Serverless, free tier |
| **Auth** | JWT via `pyjwt` | Password hashing with SHA-256 + salt |
| **Deployment** | [Render](https://render.com) | Free tier web service |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Olumidedara/FlowSynth.git
cd FlowSynth

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
```

Edit `.env` with your API keys:

```env
GROQ_API_KEY=gsk_your_groq_key_here
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
```

> **Get free keys:** [Groq](https://console.groq.com) · [Neon](https://neon.tech)

```bash
# Run the app
uvicorn src.main:app --host 127.0.0.1 --port 8005
```

Open **http://127.0.0.1:8005** in your browser.

---

## Configuration

All configuration is via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Primary Groq model |
| `GROQ_FALLBACK_MODEL` | No | — | 1st fallback on rate limit |
| `GROQ_FALLBACK_MODEL_2` | No | — | 2nd fallback on rate limit |
| `DATABASE_URL` | Yes | — | Neon PostgreSQL connection string |
| `JWT_SECRET` | No | auto-generated | JWT signing key |
| `JWT_EXPIRE_MINUTES` | No | `2880` | Token lifetime (48h) |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page |
| `POST` | `/api/research` | Submit a research query |
| `GET` | `/api/status/{task_id}` | Poll pipeline status |
| `GET` | `/api/result/{task_id}` | Get completed result |
| `GET` | `/result/{task_id}` | View result page |
| `GET` | `/api/history` | List research history |
| `DELETE` | `/api/research/{id}` | Delete a research record |
| `POST` | `/auth/signup` | Create account |
| `POST` | `/auth/signin` | Sign in |
| `GET` | `/auth/me` | Current user info |

---

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Olumidedara/FlowSynth)

Or manually:

1. Connect your GitHub repo to Render
2. Choose **Web Service**
3. Set **Build Command:** `pip install -r requirements.txt`
4. Set **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `GROQ_API_KEY`, `DATABASE_URL`
6. Pick **Free** plan → **Deploy**

A `render.yaml` is also included for Blueprint-based deployment.

> **Tip:** Set up a free [cron-job.org](https://cron-job.org) ping every 5 minutes to prevent Render's free tier from spinning down.

---

## Project Structure

```
FlowSynth/
├── src/
│   ├── main.py                 # FastAPI app & routes
│   ├── config.py               # Settings from .env
│   ├── database.py             # asyncpg PostgreSQL layer
│   ├── auth.py                 # JWT auth router
│   ├── llm.py                  # Groq LLM abstraction (3-model fallback)
│   ├── workflow/
│   │   ├── graph.py            # LangGraph pipeline
│   │   ├── state.py            # TypedDict state definition
│   │   ├── progress.py         # Thread-safe stage tracking
│   │   ├── nodes/
│   │   │   ├── orchestrator.py # Research planner
│   │   │   ├── researcher.py   # Web searcher
│   │   │   ├── analyst.py      # Insight extractor
│   │   │   ├── writer.py       # Article drafter
│   │   │   ├── reviewer.py     # Quality scorer
│   │   │   └── finalizer.py    # Final polisher
│   │   └── tools/
│   │       └── search.py       # DuckDuckGo wrapper
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS, favicon
├── requirements.txt
├── Procfile                    # Render start command
├── render.yaml                 # Render Blueprint config
├── runtime.txt                 # Python version
└── .env.example                # Environment template
```

---

## License

MIT

---

<div align="center">

**FlowSynth** — Multi-Agent Research Pipeline · Powered by [Groq](https://groq.com)

Built with ❤️ for the open-source community

</div>
