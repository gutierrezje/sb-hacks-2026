# The Salary Dojo - 16-Hour Execution Plan

## Executive Summary

**Project**: Voice-controlled salary negotiation simulator
**Working Hours**: ~16 hours
**Team Size**: 1 developer
**Primary Goal**: Maximize Autonomy (40%) and Real-Time UX (30%) scores
**Frontend**: Web App (React + Vite) with Discord-style call UI
**LLM**: Gemini 3.0 Flash (free tier) or GPT-4o-mini (cheap fallback)

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

## Phase 1: Voice Pipeline (Hours 0-6)

**Goal**: End-to-end voice working. Speak -> Transcribe -> Simple LLM -> TTS -> Hear response.

### 1.1 Data Models First (30 min)
Since tools need state, build this first:

- [x] Create `models/state.py` with Marcus state (patience, stress, emotion, budget, current_offer)
- [x] Create `models/session.py` with NegotiationSession (history, marcus_state, phase)
- [x] Add basic state transitions and validation

**Deliverable**: Can instantiate a session with Marcus state

### 1.2 Deepgram STT Integration (2 hours)
- [x] Create `core/deepgram_handler.py`
- [x] Implement bidirectional streaming (WebSocket -> Deepgram -> WebSocket)
- [x] Handle interim vs final transcripts
- [x] Implement `utterance_end` detection for turn-taking
- [x] Wire into existing `/ws/negotiate` endpoint
- [x] Test with audio from frontend (even if TTS not ready yet)

**Deliverable**: Can see transcript appear in backend logs

### 1.3 Deepgram TTS Integration (1.5 hours)
- [x] Create `core/tts_controller.py`
- [x] Implement text -> streaming audio via Deepgram Aura
- [x] Handle chunked audio response
- [x] Send audio chunks back through WebSocket
- [x] Test with hardcoded text first

**Deliverable**: Backend can send spoken audio to frontend

### 1.4 Simple LLM Response (1 hour)
- [x] Create `core/llm_client.py` with Gemini 3.0 Flash client
- [x] Wire up basic chat (NO tools yet, just conversation)
- [x] Use simple Marcus prompt: "You are Marcus, a recruiter. Be brief."
- [x] Connect: transcript -> LLM -> TTS -> audio out
- [x] Test the full loop

**Deliverable**: Can speak and hear Marcus respond (generic responses, no tools)

### 1.5 Basic Frontend UI (1 hour)
- [x] Create simple layout (two circles for user/Marcus)
- [x] Implement microphone access and recording
- [x] WebSocket connection to `/ws/negotiate`
- [x] Stream audio chunks to backend
- [x] Play received audio through `<audio>` element or Web Audio API
- [x] Show connection status

**Deliverable**: Voice round-trip works end-to-end

**Phase 1 Success**: Speak -> hear Marcus respond in voice (even if dumb responses)

---

## Phase 2: The Brain (Hours 6-11)

**Goal**: Marcus uses tools autonomously and negotiates intelligently.

### 2.1 Tool Definitions & Mock Data (1 hour)
- [x] Create `tools/__init__.py` with 4 tool schemas (OpenAI/Gemini format)
- [x] Create `tools/market_data.py` with hardcoded salary data for 10 companies
- [x] Keep it simple - just return mock JSON responses

**Deliverable**: Tool schemas defined, mock data ready

### 2.2 Tool Executor (1.5 hours)
- [ ] Create `tools/executor.py` with ToolExecutor class
- [ ] Implement each tool:
  - `check_market_rate`: Query mock data, return salary range
  - `adjust_internal_state`: Mutate session.marcus_state (patience, stress, emotion)
  - `make_offer`: Set session.current_offer
  - `end_negotiation`: Set session outcome
- [ ] Add validation and error handling
- [ ] Tools modify the session state in-place

**Deliverable**: Can call tools manually and see state change

### 2.3 LLM Function Calling Loop (2.5 hours)
This is the hard part - the orchestration engine:

- [ ] Extend `LLMClient` to support tools
- [ ] Implement the agentic loop:
  1. Call LLM with messages + tools
  2. If tool_calls returned -> execute tools -> append results -> loop back
  3. If text returned -> done, send to TTS
- [ ] Handle multi-tool calls in one turn
- [ ] Add max iteration limit (prevent infinite loops)
- [ ] Stream responses when possible
- [ ] Load full Marcus system prompt from `prompts/marcus.txt`

**Deliverable**: Marcus calls tools during conversation

### 2.4 Integration & Testing (1 hour)
- [ ] Test: "I have an offer from Google at $200k" -> triggers market check
- [ ] Test: Rambling -> patience decreases
- [ ] Test: Good argument -> Marcus makes counter-offer
- [ ] Test: Low patience -> Marcus ends negotiation
- [ ] Fix any bugs in the loop

**Deliverable**: Full negotiation possible, tools work correctly

**Phase 2 Success**: Marcus uses all 4 tools appropriately during negotiation

---

## Phase 3: UI & Demo (Hours 11-16)

**Goal**: Beautiful UI, reliable demo, ready to present.

### 3.1 Discord-Style UI (2.5 hours)
- [ ] Dark theme styling (Discord-inspired)
- [ ] Two-panel layout with user/Marcus sides
- [ ] Emoji avatar component with smooth transitions (CSS animations)
- [ ] Audio visualizer waveforms:
  - Simple approach: CSS animation on SVG bars
  - Use Web Audio API's `analyser` for real audio-reactive waves
- [ ] Patience meter bar with color gradient (green -> yellow -> red)
- [ ] Current offer display with number animation
- [ ] "Marcus is thinking..." indicator

**Deliverable**: Polished call screen

### 3.2 State Synchronization (1 hour)
- [ ] Send Marcus state updates from backend to frontend via WebSocket
- [ ] Update emoji avatar when emotion changes
- [ ] Update patience bar in real-time
- [ ] Update current offer when Marcus makes offer
- [ ] Show "negotiation ended" state

**Deliverable**: UI reflects backend state changes

### 3.3 User Interruption (30 min)
- [ ] Detect when user starts speaking while Marcus is talking
- [ ] Cancel TTS stream on backend
- [ ] Show visual feedback (maybe flash the user's panel)
- [ ] Slightly reduce patience

**Deliverable**: Can interrupt Marcus mid-sentence

### 3.4 Results Screen (45 min)
- [ ] Create post-negotiation summary component
- [ ] Calculate score: `(final_offer / budget_ceiling) * 100`
- [ ] Show letter grade (A: 90%+, B: 80-89%, C: 70-79%, F: <70% or hung up)
- [ ] Display key moments (what impressed/annoyed Marcus)
- [ ] "Try Again" button to reset

**Deliverable**: Satisfying ending experience

### 3.5 Demo Scenarios & Testing (1.5 hours)
- [ ] Create "winning" script with specific phrases:
  - Mention competing offer (reasonable amount)
  - Ask about benefits
  - Cite market data
  - Be polite and concise
- [ ] Create "failing" script:
  - Ramble excessively
  - Make outrageous claims
  - Be aggressive
  - Ignore Marcus's cues
- [ ] Test both paths 5x each, fix any issues
- [ ] Add "Reset" functionality
- [ ] Practice demo timing (aim for 3 min)

**Deliverable**: Reliable demo ready

**Phase 3 Success**: Can demo both winning and losing paths flawlessly

---

## Stretch Goals (If Time Permits)

1. **Transcript panel** - Show real-time transcript of conversation
2. **Simple Three.js avatar** - Low-poly 3D face instead of emoji
3. **Marcus interrupts user** - After excessive rambling (10+ seconds)
4. **Hint system** - Suggest good responses during practice mode
5. **Voice emotion** - Adjust Deepgram Aura parameters based on Marcus's stress

---

## Milestone Checkpoints

| Hour | Checkpoint | Must Have |
|------|-----------|-----------|
| 2 | Models + STT | Can see transcripts in logs |
| 4 | TTS working | Can hear backend speak |
| 6 | Voice loop | Full round-trip working |
| 9 | Tools defined | LLM can call all 4 tools |
| 11 | Smart Marcus | Full negotiation possible |
| 14 | UI polished | Discord-style interface done |
| 16 | Demo ready | Both paths tested, presentation ready |

---

## Simplified Tool Set

### 1. `check_market_rate`
Look up salary data for role/company. Returns mock data from hardcoded table.

```python
{
  "name": "check_market_rate",
  "description": "Look up market salary data for a specific role at a company. Use this when the candidate mentions competing offers or asks about market rates.",
  "parameters": {
    "type": "object",
    "properties": {
      "role": {
        "type": "string",
        "description": "Job role (e.g. 'Software Engineer', 'Product Manager')"
      },
      "company": {
        "type": "string",
        "description": "Company name (e.g. 'Google', 'Meta', 'Startup')"
      },
      "level": {
        "type": "string",
        "description": "Seniority level (e.g. 'new_grad', 'mid', 'senior')",
        "enum": ["new_grad", "mid", "senior"]
      }
    },
    "required": ["role", "company"]
  }
}
```

### 2. `adjust_internal_state`
Update Marcus's hidden state. LLM should call this frequently.

```python
{
  "name": "adjust_internal_state",
  "description": "Update your internal emotional state based on the conversation. Call this whenever the candidate says something that affects your patience or stress. This is private - the candidate cannot see this.",
  "parameters": {
    "type": "object",
    "properties": {
      "patience_delta": {
        "type": "number",
        "description": "Change in patience (-20 to +10). Negative for annoying behavior, positive for good responses."
      },
      "stress_delta": {
        "type": "number",
        "description": "Change in stress level (-10 to +20). Positive for high demands, negative for reasonable requests."
      },
      "emotional_state": {
        "type": "string",
        "enum": ["neutral", "impressed", "very_impressed", "skeptical", "annoyed", "stressed", "frustrated", "done"],
        "description": "Your current emotional state"
      },
      "reason": {
        "type": "string",
        "description": "Brief internal note about why you're adjusting state"
      }
    },
    "required": ["emotional_state", "reason"]
  }
}
```

### 3. `make_offer`
Make or adjust salary offer.

```python
{
  "name": "make_offer",
  "description": "Make a salary offer or counter-offer to the candidate. Only call this when you're ready to put a number on the table.",
  "parameters": {
    "type": "object",
    "properties": {
      "amount": {
        "type": "number",
        "description": "Total compensation amount in USD"
      },
      "is_final": {
        "type": "boolean",
        "description": "Whether this is your final offer (true) or there's room to negotiate (false)"
      },
      "components": {
        "type": "object",
        "description": "Optional breakdown of compensation",
        "properties": {
          "base": {"type": "number"},
          "bonus": {"type": "number"},
          "equity": {"type": "number"}
        }
      }
    },
    "required": ["amount", "is_final"]
  }
}
```

### 4. `end_negotiation`
Conclude the negotiation session.

```python
{
  "name": "end_negotiation",
  "description": "End the negotiation. Call this when: (1) you and candidate agree on terms, (2) you're rejecting them, or (3) you're hanging up due to frustration.",
  "parameters": {
    "type": "object",
    "properties": {
      "outcome": {
        "type": "string",
        "enum": ["accepted", "rejected", "hung_up"],
        "description": "accepted: deal reached, rejected: polite decline, hung_up: frustrated ending"
      },
      "final_offer": {
        "type": "number",
        "description": "The final offer amount, if any"
      },
      "reason": {
        "type": "string",
        "description": "Brief explanation for ending (e.g. 'Candidate accepted $145k', 'Unrealistic expectations', 'Lost patience')"
      }
    },
    "required": ["outcome", "reason"]
  }
}
```

---

## Resource Allocation

### Time Budget (16 hours)

| Phase | Hours | Focus |
|-------|-------|-------|
| Phase 1: Voice Pipeline | 6 | Deepgram + basic LLM |
| Phase 2: The Brain | 5 | Tools + orchestration |
| Phase 3: UI & Demo | 5 | Polish + testing |

### API Budget Estimates

| Service | Estimated Usage | Cost |
|---------|----------------|------|
| Deepgram STT | ~1.5 hours audio | ~$1 |
| Deepgram TTS | ~45 min audio | ~$12 |
| Gemini 3.0 Flash | ~100k tokens | Free tier |
| GPT-4o-mini (fallback) | ~80k tokens | ~$0.12 |
| **Total** | | **~$13** |

---

## LLM Provider Recommendations

**Primary: Google Gemini 3.0 Flash**
- Free tier: 1500 requests/day
- Good function calling support
- Fast inference
- Use `google-generativeai` Python SDK

**Fallback: OpenAI GPT-4o-mini**
- Very cheap: $0.15/1M input tokens
- Excellent function calling
- More reliable if Gemini rate limits

**Setup both, make it configurable via env var**

---

## Contingency Plans

### If Running Behind Schedule
- **Hour 8**: Skip interruption feature, use basic turn-taking
- **Hour 12**: Simplify UI - emoji + patience bar only, no visualizer
- **Hour 14**: Use screen recording as backup demo

### If Deepgram Issues
- Fall back to Deepgram batch API (higher latency but works)
- Use browser Web Speech API as last resort

### If LLM Issues
- Gemini rate limit: switch to GPT-4o-mini
- High latency: reduce system prompt size
- Function calling bugs: simplify to 2 tools (market_rate + end_negotiation)

---

## Definition of Done

The project is complete when:

1. **Functional**
   - [ ] User can have 3-minute voice negotiation with Marcus
   - [ ] Marcus autonomously uses at least 2 tools during conversation
   - [ ] Patience meter reflects conversation quality
   - [ ] Emoji avatar reflects emotional state
   - [ ] Negotiation ends with clear outcome (accepted/rejected/hung_up)

2. **Demonstrable**
   - [ ] Can show successful negotiation ($140k+ offer)
   - [ ] Can show failed negotiation (Marcus hangs up or rejects)
   - [ ] Demo completes in under 4 minutes
   - [ ] No crashes or awkward pauses

3. **Presentable**
   - [ ] 2-minute pitch ready
   - [ ] Can explain autonomy (how Marcus uses tools)
   - [ ] Can explain real-time UX (interruptions, visual feedback)
   - [ ] Code is clean enough to show

---

## Key Differences from Original Plan

**What changed:**
1. Moved state models to beginning (tools need them)
2. Added simple LLM first, THEN tools (incremental validation)
3. Increased LLM orchestration time (2.5 hrs, this is the hard part)
4. Increased UI time (2.5 hrs, visualizers are finicky)
5. Split tool implementation (define -> implement -> integrate)
6. Added explicit integration/testing buffers
7. More realistic time estimates based on complexity

**Why this is better:**
- Each deliverable is testable independently
- Less risk of getting stuck on one hard part
- Clearer dependencies between tasks
- More buffer time for debugging
