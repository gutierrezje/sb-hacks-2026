# The Salary Dojo - Documentation

> A voice-controlled salary negotiation simulator for the 24-hour hackathon challenge: "Make Your App Talk Back"

## Quick Links

| Document | Purpose |
|----------|---------|
| [01-EXECUTION-PLAN.md](./01-EXECUTION-PLAN.md) | 24-hour phased development plan with milestones |
| [02-SYSTEM-DESIGN.md](./02-SYSTEM-DESIGN.md) | Technical system design and component specifications |
| [03-ARCHITECTURE.md](./03-ARCHITECTURE.md) | Detailed architecture, module structure, and protocols |
| [04-MARCUS-PERSONALITY.md](./04-MARCUS-PERSONALITY.md) | AI character design, prompts, and behavior patterns |
| [05-THREEJS-AVATAR.md](./05-THREEJS-AVATAR.md) | 3D avatar design with expressions, lip sync, and effects |

## Project Overview

### The Pitch

A graduating student practices salary negotiation against "Marcus," an AI recruiter with hidden state. The user must read verbal and visual cues to extract the maximum offer without Marcus "hanging up."

### Key Features

- **Real-time voice interaction** via Deepgram Flux (STT) and Aura (TTS)
- **Autonomous AI agent** that fact-checks claims, adjusts emotions, and makes strategic decisions
- **Hidden game state** (budget, patience, stress) that drives emergent behavior
- **3D animated avatar** - Marcus's face reflects his emotional state in real-time
- **Bidirectional interruption** - both user and Marcus can interrupt each other
- **Visual effects** - sweat particles when stressed, vignette when impatient

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Vite + TypeScript |
| 3D Avatar | Three.js + React Three Fiber |
| Backend | Python (FastAPI) |
| STT | Deepgram Flux (streaming) |
| TTS | Deepgram Aura (streaming) |
| LLM | OpenAI GPT-4 / Anthropic Claude (with function calling) |
| Transport | WebSocket (binary audio + JSON control) |

## Judging Criteria Alignment

| Criterion | Weight | How We Win |
|-----------|--------|------------|
| **Autonomy** | 40% | 6 tools for fact-checking, state management, UI control, offer negotiation |
| **Real-time UX** | 30% | Streaming everything, 3D avatar reactions, bidirectional interruption, <1.5s latency |
| **Engineering** | 20% | Clean architecture, proper error handling, state management |
| **Accessibility** | 10% | Clear visual cues via 3D avatar, patience meter, transcript display |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- Node.js 18+
- Deepgram API key
- OpenAI or Anthropic API key
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
cd backend && uv run uvicorn main:app --reload --host 0.0.0.0

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Development Phases

### Phase 1: Foundation (Hours 0-6)
- [ ] Project setup (backend + frontend)
- [ ] WebSocket skeleton
- [ ] Deepgram STT integration
- [ ] Deepgram TTS integration
- [ ] Minimal web app with audio

### Phase 2: The Brain (Hours 6-14)
- [ ] LLM integration with function calling
- [ ] 6 Marcus tools implemented
- [ ] State machine integration
- [ ] Conversation flow

### Phase 3: Real-Time Polish (Hours 14-20)
- [ ] Interruption system
- [ ] Three.js Marcus avatar
- [ ] Expression blending & lip sync
- [ ] Demo mode / scripted scenarios

### Phase 4: Polish & Demo (Hours 20-24)
- [ ] End-to-end testing
- [ ] Results screen
- [ ] Particle effects & post-processing
- [ ] Demo preparation

## File Structure

```
salary-dojo/
├── docs/                       # This documentation
│   ├── README.md
│   ├── 01-EXECUTION-PLAN.md
│   ├── 02-SYSTEM-DESIGN.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-MARCUS-PERSONALITY.md
│   └── 05-THREEJS-AVATAR.md
│
├── backend/                    # Python FastAPI server (uv)
│   ├── pyproject.toml          # uv project config
│   ├── uv.lock
│   ├── main.py
│   ├── api/
│   │   └── websocket.py
│   ├── core/
│   │   ├── audio_pipeline.py
│   │   ├── tts_controller.py
│   │   ├── interruption.py
│   │   └── llm_client.py
│   ├── engine/
│   │   ├── negotiation.py
│   │   ├── state_manager.py
│   │   └── conversation.py
│   ├── tools/
│   │   ├── definitions.py
│   │   ├── executor.py
│   │   └── market_data.py
│   ├── models/
│   │   ├── session.py
│   │   └── state.py
│   ├── prompts/
│   │   └── marcus.py
│   └── config.py
│
└── frontend/                   # React + Vite + Three.js
    ├── index.html
    ├── vite.config.ts
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── pages/
    │   │   ├── HomePage.tsx
    │   │   ├── NegotiationPage.tsx
    │   │   └── ResultsPage.tsx
    │   ├── components/
    │   │   ├── ui/
    │   │   │   ├── PatienceMeter.tsx
    │   │   │   └── TranscriptView.tsx
    │   │   └── three/
    │   │       ├── MarcusScene.tsx
    │   │       ├── MarcusHead.tsx
    │   │       └── ParticleEffects.tsx
    │   ├── hooks/
    │   │   ├── useWebSocket.ts
    │   │   ├── useAudioRecorder.ts
    │   │   └── useAvatar.ts
    │   ├── stores/
    │   │   └── negotiationStore.ts
    │   └── services/
    │       └── audioService.ts
    └── assets/
        └── models/
            └── marcus-head.glb
```

## Key Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State storage | In-memory dict | Hackathon simplicity, single server |
| LLM provider | OpenAI (primary) | Better function calling, faster |
| Audio format | PCM 16-bit 16kHz | Deepgram native, minimal processing |
| Python tooling | uv | 10-100x faster than pip, lockfile for reproducibility |
| UI framework | React + Vite | Fast iteration, easy Three.js integration |
| 3D library | React Three Fiber | React-friendly Three.js wrapper |
| Avatar style | Low-poly stylized | Achievable in hackathon timeframe |
| Interruption debounce | 300ms | Balance responsiveness vs. false triggers |

## Demo Checklist

- [ ] Winning negotiation path works (~$140k outcome)
- [ ] Failing negotiation path works (Marcus hangs up)
- [ ] Marcus avatar shows correct emotions
- [ ] Lip sync works during speech
- [ ] Patience meter animates smoothly
- [ ] Interruption works both directions
- [ ] Results screen displays correctly
- [ ] Network disconnection handled gracefully
- [ ] Demo can reset quickly between runs

## Contact

For questions during the hackathon, reach out to the team lead.

---

*Built for the "Make Your App Talk Back" hackathon challenge*
