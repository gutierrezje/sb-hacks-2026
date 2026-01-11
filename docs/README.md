# Salary Kombat - Documentation

> A voice-controlled salary negotiation simulator for SB Hacks 2026

## Project Overview

### The Pitch

Few people practice the rather awkward process of salary negotiation. So I came up with "Marcus," an AI recruiter that gamifies and teaches people how to employ strategies in order to improve their standing while bargaining. The user must read verbal and visual cues to extract the maximum offer without Marcus "hanging up."

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- Node.js 18+
- Deepgram API key
- Gemini API key
- Modern browser with microphone access (Chrome recommended)

### Setup

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Backend
cd backend
uv sync                    # Creates venv and installs deps (fast!)
cp .env.example .env
# Edit .env with your API keys

# Frontend
cd frontend
npm install
cp .env.example .env
# Edit .env with backend URL

# Run
# Terminal 1: Backend
cd backend && uv run uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

---
