# Insider & Celebrity Trade Tracker: Development Guide

## 🛠 Project Intent & Constraints
- **Goal:** Real-time tracking of SEC Form 4 filings and celebrity portfolios.
- **Strict Rule:** DO NOT use paid LLM APIs (OpenAI, Anthropic, etc.). 
- **Inference:** All AI analysis MUST be routed through local **Ollama** instances (Llama 3/Mistral).
- **Data:** Use `edgartools` for SEC scraping. Do not suggest subscription-based financial APIs.

## 🚀 Build & Environment
- **Runtime:** Python 3.11+
- **Setup:** `pip install -r requirements.txt`
- **Environment:** Use `.env` for local configs (Ollama URL, local DB credentials).
- **Service:** Ensure Ollama is running at `http://localhost:11434`.

## 🧪 Commands
- **Run Tracker:** `python -m src.ingestion_service`
- **Run Tests:** `pytest`
- **Type Check:** `mypy src`
- **Lint:** `flake8 src`

## 🎨 Coding Standards
- **Style:** Functional and modular. Avoid deep class hierarchies unless using SQLAlchemy models.
- **Async:** Use `asyncio` and `httpx` for all network calls (Ollama/SEC) to maximize throughput.
- **Types:** Strict type hinting is required for all function signatures.
- **Logging:** Use `structlog` or standard `logging` with JSON formatting. No `print()` statements in production code.
- **Database:** SQLAlchemy 2.0 (async) with local PostgreSQL/pgvector or SQLite for prototyping.

## 📈 Git & Workflow
- **Frequency:** Commit after every successful tool execution or logical sub-task.
- **Messages:** Use Conventional Commits (e.g., `feat(ai): add conviction scoring logic via ollama`).
- **Context:** Before major refactors, summarize the plan and wait for a "Go" vibe-check.