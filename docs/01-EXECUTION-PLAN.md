# The Salary Dojo - 16-Hour Execution Plan

## Executive Summary

**Project**: Voice-controlled salary negotiation simulator
**Working Hours**: ~16 hours
**Team Size**: 1 developer
**Primary Goal**: Maximize Autonomy (40%) and Real-Time UX (30%) scores
**Frontend**: Web App (React + Vite) with Discord-style call UI

### The Concept

A graduating student practices salary negotiation against "Marcus," an AI recruiter with hidden state (budget ceiling, patience meter). The user must read verbal and visual cues to extract the maximum offer without Marcus "hanging up."

### Why This Wins

1. **Natural autonomy**: Marcus must fact-check claims, adjust emotional state, and make strategic decisions
2. **Built-in turn-taking**: Negotiation format creates natural conversation flow
3. **Predictable for demo**: Tunable parameters allow scripted success/failure scenarios
4. **High engagement**: Stakes feel real, feedback is immediate

---

## UI Concept: Discord-Style Call Screen

```
+--------------------------------------------------+
|                  SALARY DOJO                     |
|                                                  |
|   +------------------+    +------------------+   |
|   |                  |    |                  |   |
|   |     ~~~~~~~~     |    |     ~~~~~~~~     |   |
|   |    ~ USER ~      |    |    ~ 😐 ~       |   |
|   |     ~~~~~~~~     |    |     ~~~~~~~~     |   |
|   |                  |    |                  |   |
|   |   [Audio Waves]  |    |   [Audio Waves]  |   |
|   +------------------+    +------------------+   |
|        You                     Marcus            |
|                                                  |
|   +--------------------------------------------+ |
|   | Current Offer: $125,000                    | |
|   | ████████████░░░░░░░░ Patience              | |
|   +--------------------------------------------+ |
|                                                  |
|              [ End Negotiation ]                 |
+--------------------------------------------------+
```

### Emoji Avatar System

Marcus's avatar warps between emojis based on his emotional state:

| State | Emoji | Trigger |
|-------|-------|---------|
| Neutral | 😐 | Default state |
| Impressed | 😊 | Good arguments, market data cited |
| Very Impressed | 😄 | Excellent negotiation moves |
| Skeptical | 🤨 | Unverified claims |
| Annoyed | 😒 | Rambling, repetition |
| Stressed | 😰 | Aggressive tactics, high demands |
| Frustrated | 😤 | Patience running low |
| Done | 😑 | About to hang up |

### Audio Visualizer

- Both sides have animated waveforms showing who's speaking
- User side pulses with microphone input
- Marcus side pulses with TTS output
- Visual rhythm helps indicate turn-taking

---

## Phase 1: Foundation (Hours 0-5)

### Objective
Audio flows end-to-end. User speaks, system transcribes, Marcus responds with voice.

### Critical Path (Must Complete)

#### 1.1 Project Setup (30 min)
- [ ] Verify backend scaffolding works (`uv sync`, `uv run uvicorn main:app`)
- [ ] Initialize React + Vite frontend with TypeScript
- [ ] Set up environment variables for API keys
- [ ] Verify Deepgram API access (both Flux and Aura)

#### 1.2 FastAPI WebSocket Skeleton (45 min)
- [ ] Create WebSocket endpoint `/ws/negotiate`
- [ ] Implement connection lifecycle (connect, disconnect, error handling)
- [ ] Add session management (in-memory dict of active sessions)
- [ ] Test with simple echo functionality

**Deliverable**: WebSocket that accepts connection and echoes messages

#### 1.3 Deepgram STT Integration (1.5 hours)
- [ ] Create `DeepgramHandler` class
- [ ] Implement audio streaming to Deepgram
- [ ] Handle interim vs final transcripts
- [ ] Implement `utterance_end` detection for turn-taking
- [ ] Test with audio input

**Deliverable**: Audio bytes in -> transcript text out

#### 1.4 Deepgram TTS Integration (1 hour)
- [ ] Create `TTSController` class
- [ ] Implement text -> audio streaming
- [ ] Handle chunked audio response
- [ ] Test with sample text

**Deliverable**: Text in -> streaming audio bytes out

#### 1.5 Minimal Web UI (1.5 hours)
- [ ] Create Discord-style call layout (two panels side by side)
- [ ] Implement microphone recording with Web Audio API
- [ ] Create WebSocket connection hook
- [ ] Stream audio to backend
- [ ] Play received audio through Web Audio API
- [ ] Add basic state indicators (connecting, listening, speaking)

**Deliverable**: Working voice round-trip (speak -> hear response)

### Phase 1 Success Criteria
- [ ] Can speak into browser and hear "Hello, I received your audio" response
- [ ] Latency under 2 seconds from speech end to response start

---

## Phase 2: The Brain (Hours 5-11)

### Objective
Marcus thinks, uses tools, has personality. The negotiation feels real.

### Critical Path (Must Complete)

#### 2.1 LLM Integration with Function Calling (2.5 hours)
- [ ] Create `LLMClient` class (support OpenAI, Anthropic as fallback)
- [ ] Implement Marcus system prompt
- [ ] Define 4 core tool schemas
- [ ] Handle streaming responses
- [ ] Implement tool call parsing and execution loop

**Deliverable**: LLM responds in character and uses tools appropriately

#### 2.2 Implement Core Tools (2 hours)

| Tool | Purpose | Complexity |
|------|---------|------------|
| `check_market_rate` | Verify salary claims | Medium |
| `adjust_internal_state` | Update patience/stress/emotion | Low |
| `make_offer` | Control salary offers | Medium |
| `end_negotiation` | Conclude the call | Low |

- [ ] Implement `ToolExecutor` class
- [ ] Implement each tool with proper state mutations
- [ ] Add tool result formatting for LLM consumption

**Deliverable**: All 4 tools functional

#### 2.3 State Management (1.5 hours)
- [ ] Create `NegotiationSession` and `MarcusState` models
- [ ] Implement patience decay logic
- [ ] Implement stress accumulation
- [ ] Create emotional state derivation (maps to emoji)
- [ ] Add session persistence (in-memory)

**Deliverable**: Marcus's behavior changes based on accumulated state

#### 2.4 Conversation Flow (1 hour)
- [ ] Build conversation history management
- [ ] Implement context window management
- [ ] Create response streaming to TTS pipeline

**Deliverable**: Multi-turn conversations that maintain context

### Phase 2 Success Criteria
- [ ] Marcus responds contextually to negotiation statements
- [ ] Saying "I have an offer from Google at $150k" triggers market rate check
- [ ] Marcus can make and adjust offers
- [ ] Emotional state changes based on conversation

---

## Phase 3: UI Polish & Demo Prep (Hours 11-16)

### Objective
Make the UI communicative and prepare for demo.

### Critical Path (Must Complete)

#### 3.1 Discord-Style UI Implementation (2 hours)
- [ ] Style the call screen (dark theme, Discord-inspired)
- [ ] Implement emoji avatar component with smooth transitions
- [ ] Create audio visualizer waveforms (CSS or Canvas)
- [ ] Add patience meter bar with color gradient
- [ ] Display current offer amount with animation
- [ ] Show "thinking" indicator when LLM processing

**Deliverable**: Polished call UI that communicates state

#### 3.2 User Interruption (1 hour)
- [ ] Detect sustained speech while TTS playing
- [ ] Cancel TTS stream when user interrupts
- [ ] Reduce patience slightly on interruption
- [ ] Visual feedback for interruption

**Deliverable**: User can interrupt Marcus mid-sentence

#### 3.3 Demo Scenarios (1 hour)
- [ ] Script "winning" conversation path with specific triggers
- [ ] Script "failing" conversation path
- [ ] Test both paths work reliably

**Deliverable**: Two reproducible demo paths

#### 3.4 Results Screen (1 hour)
- [ ] Create post-negotiation summary
- [ ] Calculate and display score (% of budget captured)
- [ ] Show letter grade with message
- [ ] Add "Try Again" button

**Deliverable**: Satisfying conclusion to the experience

#### 3.5 Final Testing & Demo Prep (1 hour)
- [ ] Full run-through of winning script
- [ ] Full run-through of failing script
- [ ] Test error handling (network issues, empty audio)
- [ ] Create "Reset" functionality for quick restart
- [ ] Practice demo flow

**Deliverable**: Ready for presentation

### Phase 3 Success Criteria
- [ ] Can interrupt Marcus mid-sentence and he stops
- [ ] Emoji avatar reflects Marcus's emotional state
- [ ] Can reliably demo both success and failure paths
- [ ] Demo completes in under 4 minutes

---

## Stretch Goals (If Time Permits)

1. **Simple Three.js Avatar** - Replace emoji with low-poly 3D face
2. **Particle effects** - Subtle stress indicators
3. **Marcus interrupts user** - After excessive rambling
4. **Hint mode** - Suggests good responses for demo
5. **Voice emotion** - Adjust Aura parameters based on Marcus state

---

## Milestone Checkpoints

| Hour | Checkpoint | Must Have |
|------|-----------|-----------|
| 2 | Infra Ready | WebSocket connected, both apps running |
| 5 | Voice Loop | Speak -> Transcribe -> TTS -> Hear |
| 8 | Smart Marcus | LLM responds with tools, state changes |
| 11 | Full Game | Complete negotiation possible |
| 14 | Polished UX | UI complete, interruptions work |
| 16 | Ship It | Demo practiced, ready to present |

---

## Simplified Tool Set

Reduced from 6 to 4 essential tools:

### 1. `check_market_rate`
```json
{
  "name": "check_market_rate",
  "description": "Look up market salary data for a role/company",
  "parameters": {
    "role": "string",
    "company": "string (optional)",
    "location": "string (optional)"
  }
}
```

### 2. `adjust_internal_state`
```json
{
  "name": "adjust_internal_state",
  "description": "Update Marcus's internal state based on conversation",
  "parameters": {
    "patience_delta": "number (-20 to +10)",
    "stress_delta": "number (-10 to +20)",
    "emotional_state": "string (enum)",
    "reason": "string"
  }
}
```

### 3. `make_offer`
```json
{
  "name": "make_offer",
  "description": "Make or adjust a salary offer",
  "parameters": {
    "amount": "number",
    "is_final": "boolean",
    "components": "object (optional: bonus, equity, etc.)"
  }
}
```

### 4. `end_negotiation`
```json
{
  "name": "end_negotiation",
  "description": "End the negotiation",
  "parameters": {
    "outcome": "string (accepted, rejected, hung_up)",
    "final_offer": "number",
    "reason": "string"
  }
}
```

---

## Resource Allocation

### Time Budget (16 hours)

| Category | Hours | Percentage |
|----------|-------|------------|
| Backend Core (WebSocket, Deepgram) | 4 | 25% |
| AI/LLM Integration | 4 | 25% |
| Frontend UI | 4 | 25% |
| Polish & Demo | 4 | 25% |

### API Budget Estimates

| Service | Estimated Usage | Cost |
|---------|----------------|------|
| Deepgram STT | ~1.5 hours audio | ~$1 |
| Deepgram TTS | ~45 min audio | ~$12 |
| OpenAI GPT-4 | ~80k tokens | ~$4 |
| **Total** | | **~$17** |

---

## Contingency Plans

### If Running Behind Schedule
- **Hour 8**: Cut interruption system, focus on basic turn-taking
- **Hour 12**: Simplify UI to just emoji + patience bar, cut visualizer
- **Hour 14**: Use screen recording as backup demo

### If Deepgram Issues
- Fall back to Deepgram batch API (higher latency)
- Use browser Web Speech API as last resort

### If LLM Latency Too High
- Reduce system prompt size
- Use GPT-3.5-turbo for faster inference

---

## Definition of Done

The project is complete when:

1. **Functional**
   - [ ] User can have 3-minute voice negotiation with Marcus
   - [ ] Marcus uses at least 2 tools during conversation
   - [ ] Patience meter reflects conversation quality
   - [ ] Emoji avatar reflects emotional state
   - [ ] Negotiation ends with offer or hang-up

2. **Demonstrable**
   - [ ] Can show successful negotiation ($140k+ offer)
   - [ ] Can show failed negotiation (Marcus hangs up)
   - [ ] Demo completes in under 4 minutes

3. **Presentable**
   - [ ] 2-minute pitch ready
   - [ ] Technical decisions documented
   - [ ] Code is reasonably clean
