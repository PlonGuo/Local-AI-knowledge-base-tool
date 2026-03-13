# KnowHive

A local-first AI knowledge base desktop app. Import your Markdown and PDF files, chat with them using any LLM (Ollama, OpenAI-compatible, or Anthropic Claude), and build a spaced-repetition review practice — all without your data leaving your machine.

## Features

- **RAG Chat** — Ask questions about your knowledge base; get answers with source citations
- **File Management** — Import `.md` and `.pdf` files, rename, delete, and edit Markdown in-app
- **File Watcher** — Automatically re-indexes files when they change on disk
- **Spaced Repetition** — SM-2–based review queue with AI-generated summaries
- **Knowledge Overview** — Browse all documents with on-demand AI summaries
- **Community Packs** — Import curated knowledge packs from the community manifest
- **Embedding Models** — Download and switch sentence-transformer models (English / Chinese / Mixed)
- **Data Export** — Export your full knowledge base + chat history as a ZIP
- **Multi-provider LLM** — Ollama, any OpenAI-compatible endpoint, or Anthropic Claude
- **Onboarding Flow** — First-run wizard to check dependencies and configure your LLM

## Prerequisites

| Requirement | Notes |
|---|---|
| Node.js 18+ | For the Electron/React frontend |
| pnpm | `npm install -g pnpm` |
| Python 3.11+ | For the FastAPI sidecar |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Python package manager — required |
| [Ollama](https://ollama.com/) (optional) | Local LLM runner; or use OpenAI-compatible / Anthropic |

## Installation

```bash
git clone https://github.com/PlonGuo/knowhive.git
cd knowhive

# Install frontend dependencies
pnpm install

# Install backend dependencies
cd backend && uv sync && cd ..
```

## Development

Run all three processes (backend + Vite + Electron) in one command:

```bash
pnpm dev:all
```

Or start them separately:

```bash
# Terminal 1 — FastAPI backend
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 18200

# Terminal 2 — Electron + Vite (after backend is up)
BACKEND_URL=http://127.0.0.1:18200 pnpm dev
```

## Running Tests

```bash
# Frontend + Electron tests (Vitest)
pnpm test

# Backend tests (pytest)
cd backend
uv run pytest
```

## Building

```bash
# macOS (arm64 + x64 universal DMG)
pnpm build:mac

# Windows
pnpm build:win
```

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop shell | Electron 28 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| Backend sidecar | FastAPI + Python 3.11 |
| Package manager (Python) | uv |
| Vector store | ChromaDB |
| Embeddings | sentence-transformers (local) |
| Database | SQLite (aiosqlite) |
| File parsing | LangChain text splitters + PyMuPDF (PDF) |
| File watching | watchdog |
| LLM providers | Ollama · OpenAI-compatible · Anthropic Claude |

## Project Structure

```
knowhive/
├── src/                  # React frontend (TypeScript)
│   └── components/
│       ├── layout/       # AppLayout, Sidebar, StatusBar
│       ├── chat/         # ChatArea (SSE streaming)
│       ├── knowledge/    # FileTree, MarkdownEditor, KnowledgeOverview
│       ├── settings/     # SettingsPage
│       ├── review/       # ReviewPage (spaced repetition)
│       ├── community/    # CommunityBrowser
│       └── onboarding/   # OnboardingPage (first-run wizard)
├── electron/             # Electron main process + preload
│   ├── main.ts           # BrowserWindow, IPC handlers, sidecar management
│   ├── sidecar.ts        # FastAPI process lifecycle
│   └── preload.ts        # contextBridge API
├── backend/              # FastAPI sidecar (Python)
│   └── app/
│       ├── main.py       # App factory, lifespan, service wiring
│       ├── routers/      # chat, config, ingest, knowledge, review, …
│       └── services/     # RAGService, IngestService, EmbeddingService, …
└── tests/                # Vitest frontend + Electron tests
```

## License

MIT
