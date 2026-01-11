# The Salary Dojo - Architecture Document

## 1. Architecture Overview

### 1.1 Architecture Style

The Salary Dojo follows a **real-time event-driven architecture** with three primary characteristics:

1. **Bidirectional streaming**: Audio and events flow both directions simultaneously
2. **Stateful sessions**: Each negotiation maintains persistent in-memory state
3. **Autonomous agent pattern**: The LLM operates as an agent with tool access

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                                     │
│                         React + Vite Web App                                │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        Presentation Layer                            │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │ Negotiation │  │ Marcus      │  │ Transcript  │  │ Results    │  │   │
│   │  │ Screen      │  │ Avatar      │  │ View        │  │ Screen     │  │   │
│   │  │             │  │ (Emoji)     │  │             │  │            │  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         Service Layer                                │   │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │   │
│   │  │ AudioService    │  │ WebSocketService│  │ EmojiController     │  │   │
│   │  │ • Web Audio API │  │ • Connection    │  │ • Emotion display │  │   │
│   │  │ • Playback      │  │ • Message queue │  │ • Animations      │  │   │
│   │  │ • Level monitor │  │ • Reconnection  │  │ • Pulse effects   │  │   │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                           WebSocket Connection                               │
│                    (Binary audio + JSON messages)                           │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     │ wss://
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              SERVER TIER                                     │
│                         Python FastAPI                                      │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        Gateway Layer                                 │   │
│   │  ┌───────────────────────────────────────────────────────────────┐  │   │
│   │  │                   WebSocket Handler                            │  │   │
│   │  │  • Connection lifecycle    • Binary/JSON routing              │  │   │
│   │  │  • Session binding         • Error handling                   │  │   │
│   │  └───────────────────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                       Processing Layer                               │   │
│   │                                                                      │   │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │   │
│   │  │ Audio Pipeline  │  │ Negotiation     │  │ Response Pipeline   │  │   │
│   │  │                 │  │ Engine          │  │                     │  │   │
│   │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────────┐ │  │   │
│   │  │ │ STT Handler │ │  │ │ LLM Client  │ │  │ │ TTS Controller  │ │  │   │
│   │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────────┘ │  │   │
│   │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────────┐ │  │   │
│   │  │ │ Transcript  │ │  │ │ Tool        │ │  │ │ Interruption    │ │  │   │
│   │  │ │ Accumulator │ │  │ │ Executor    │ │  │ │ Manager         │ │  │   │
│   │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────────┘ │  │   │
│   │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────────┐ │  │   │
│   │  │ │ Turn        │ │  │ │ State       │ │  │ │ Event           │ │  │   │
│   │  │ │ Detector    │ │  │ │ Manager     │ │  │ │ Broadcaster     │ │  │   │
│   │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────────┘ │  │   │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         Data Layer                                   │   │
│   │  ┌───────────────────────────────────────────────────────────────┐  │   │
│   │  │                   Session Store                                │  │   │
│   │  │  dict[session_id: str, NegotiationSession]                    │  │   │
│   │  │                                                                │  │   │
│   │  │  NegotiationSession:                                          │  │   │
│   │  │    ├── marcus: MarcusState                                    │  │   │
│   │  │    │     ├── budget_ceiling, patience, stress                 │  │   │
│   │  │    │     ├── candidate_claims, verified_facts                 │  │   │
│   │  │    │     └── offers_made, emotional_state                     │  │   │
│   │  │    ├── conversation: list[ConversationTurn]                   │  │   │
│   │  │    └── outcome, final_salary                                  │  │   │
│   │  └───────────────────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│    EXTERNAL SERVICE     │ │    EXTERNAL SERVICE     │ │    EXTERNAL SERVICE     │
│                         │ │                         │ │                         │
│    Deepgram Flux        │ │    Deepgram Aura        │ │    OpenAI / Anthropic   │
│    (Streaming STT)      │ │    (Streaming TTS)      │ │    (LLM + Tools)        │
│                         │ │                         │ │                         │
│  • WebSocket protocol   │ │  • HTTP streaming       │ │  • HTTP streaming       │
│  • Real-time transcripts│ │  • Multiple voices      │ │  • Function calling     │
│  • Utterance detection  │ │  • Low latency          │ │  • Context window       │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Client Components

#### 2.1.1 Component Hierarchy

```
App
├── Router (React Router)
│   ├── HomePage
│   │   ├── HeroSection
│   │   └── StartButton
│   │
│   ├── NegotiationPage
│   │   ├── MarcusAvatar (Emoji Component)
│   │   │   ├── EmotionDisplay
│   │   │   └── PulseAnimation
│   │   │
│   │   ├── UIOverlay
│   │   │   ├── PatienceMeter
│   │   │   │   ├── MeterFill (CSS animated)
│   │   │   │   └── WarningPulse
│   │   │   ├── TranscriptView
│   │   │   │   ├── UserBubble
│   │   │   │   └── MarcusBubble
│   │   │   ├── OfferDisplay
│   │   │   │   └── AnimatedNumber
│   │   │   └── StatusIndicator
│   │   │       └── ("Listening" | "Thinking" | "Speaking")
│   │   │
│   │   └── ControlBar
│   │       ├── MuteButton
│   │       └── EndCallButton
│   │
│   └── ResultsPage
│       ├── FinalOfferDisplay
│       ├── ScoreVisualization
│       ├── GradeDisplay
│       ├── HighlightsList
│       └── ActionButtons
│
└── Providers
    ├── WebSocketProvider
    ├── AudioProvider
    └── NegotiationStateProvider
```

#### 2.1.2 State Management (Client)

```typescript
// Using React Context for simplicity in hackathon

interface NegotiationContextState {
  // Connection
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';

  // Session
  sessionId: string | null;
  phase: 'waiting' | 'listening' | 'thinking' | 'speaking' | 'ended';

  // Marcus state (from server)
  patience: number;
  currentOffer: number | null;
  marcusEmotion: string;

  // Transcript
  transcript: TranscriptEntry[];

  // Audio
  isRecording: boolean;
  isPlaying: boolean;
  audioLevel: number;

  // Outcome
  outcome: NegotiationOutcome | null;
}

interface NegotiationContextActions {
  connect: () => Promise<void>;
  disconnect: () => void;
  startRecording: () => void;
  stopRecording: () => void;
  resetSession: () => void;
}

// Avatar-specific state for emoji display
interface AvatarState {
  targetEmotion: EmotionType;
  currentEmotion: EmotionType;      // For smooth transitions
  emotionBlend: number;              // 0-1, for fade animations
  isSpeaking: boolean;
  isPulsing: boolean;                // Pulse effect when speaking
}
```

### 2.2 Server Components

#### 2.2.1 Module Structure

```
backend/
├── pyproject.toml              # uv/Python project config
├── uv.lock                     # Locked dependencies
├── .python-version             # Python version (3.11+)
├── main.py                     # FastAPI app entry point
│
├── api/
│   ├── __init__.py
│   ├── websocket.py            # WebSocket endpoint handler
│   └── health.py               # Health check endpoint
│
├── core/
│   ├── __init__.py
│   ├── audio_pipeline.py       # STT integration
│   ├── tts_controller.py       # TTS integration
│   ├── interruption.py         # Turn-taking logic
│   └── llm_client.py           # LLM wrapper
│
├── engine/
│   ├── __init__.py
│   ├── negotiation.py          # Main negotiation logic
│   ├── state_manager.py        # State transitions
│   └── conversation.py         # Conversation history
│
├── tools/
│   ├── __init__.py
│   ├── definitions.py          # Tool schemas
│   ├── executor.py             # Tool dispatch
│   ├── market_data.py          # Market rate lookup
│   └── ui_events.py            # Client event triggers
│
├── models/
│   ├── __init__.py
│   ├── session.py              # NegotiationSession
│   ├── state.py                # MarcusState
│   ├── conversation.py         # ConversationTurn
│   └── events.py               # Event types
│
├── prompts/
│   ├── __init__.py
│   └── marcus.py               # System prompts
│
├── store/
│   ├── __init__.py
│   └── sessions.py             # Session storage
│
└── config.py                   # Settings

frontend/                        # React + Vite
├── index.html
├── vite.config.ts
├── package.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   │
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── NegotiationPage.tsx
│   │   └── ResultsPage.tsx
│   │
│   ├── components/
│   │   ├── ui/
│   │   │   ├── PatienceMeter.tsx
│   │   │   ├── TranscriptView.tsx
│   │   │   ├── OfferDisplay.tsx
│   │   │   └── StatusIndicator.tsx
│   │   │
│   │   └── emoji/
│   │       └── MarcusAvatar.tsx      # Emoji avatar component
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAudioRecorder.ts
│   │   └── useAudioPlayer.ts
│   │
│   ├── stores/
│   │   └── negotiationStore.ts       # Zustand store
│   │
│   ├── services/
│   │   └── audioService.ts
│   │
│   ├── types/
│   │   └── index.ts
│   │
│   └── assets/
│       └── images/
```

#### 2.2.2 Dependency Graph

```
main.py
    │
    └── api/websocket.py
            │
            ├── core/audio_pipeline.py
            │       │
            │       └── [Deepgram SDK]
            │
            ├── engine/negotiation.py
            │       │
            │       ├── core/llm_client.py
            │       │       │
            │       │       └── [OpenAI/Anthropic SDK]
            │       │
            │       ├── tools/executor.py
            │       │       │
            │       │       ├── tools/market_data.py
            │       │       └── tools/ui_events.py
            │       │
            │       ├── engine/state_manager.py
            │       │       │
            │       │       └── models/state.py
            │       │
            │       └── engine/conversation.py
            │               │
            │               └── models/conversation.py
            │
            ├── core/tts_controller.py
            │       │
            │       └── [Deepgram Aura API]
            │
            ├── core/interruption.py
            │
            └── store/sessions.py
                    │
                    └── models/session.py
```

---

## 3. Detailed Component Design

### 3.1 Audio Pipeline

```python
# core/audio_pipeline.py

class AudioPipeline:
    """
    Responsible for:
    1. Receiving raw audio from client
    2. Streaming to Deepgram for transcription
    3. Detecting end of utterance
    4. Notifying negotiation engine when turn is complete
    """

    def __init__(
        self,
        on_interim_transcript: Callable[[str], Awaitable[None]],
        on_final_transcript: Callable[[str], Awaitable[None]],
        on_utterance_complete: Callable[[str], Awaitable[None]],
        on_speech_started: Callable[[], Awaitable[None]],
    ):
        self.on_interim_transcript = on_interim_transcript
        self.on_final_transcript = on_final_transcript
        self.on_utterance_complete = on_utterance_complete
        self.on_speech_started = on_speech_started

        self._deepgram: DeepgramClient = None
        self._connection: LiveConnection = None
        self._transcript_buffer: str = ""
        self._is_speaking: bool = False

    async def initialize(self) -> None:
        """Set up Deepgram connection"""
        self._deepgram = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        self._connection = self._deepgram.listen.asynclive.v("1")

        # Event handlers
        self._connection.on(LiveTranscriptionEvents.Open, self._on_open)
        self._connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
        self._connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
        self._connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
        self._connection.on(LiveTranscriptionEvents.Error, self._on_error)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=True,
            utterance_end_ms=1000,
            vad_events=True,
            punctuate=True,
        )

        await self._connection.start(options)

    async def process_audio(self, chunk: bytes) -> None:
        """Send audio chunk to Deepgram"""
        if self._connection:
            await self._connection.send(chunk)

    async def shutdown(self) -> None:
        """Clean up connection"""
        if self._connection:
            await self._connection.finish()

    # Private event handlers
    async def _on_transcript(self, *args, result=None, **kwargs) -> None:
        transcript = result.channel.alternatives[0].transcript

        if not transcript:
            return

        if result.is_final:
            self._transcript_buffer += transcript + " "
            await self.on_final_transcript(transcript)
        else:
            await self.on_interim_transcript(transcript)

    async def _on_utterance_end(self, *args, **kwargs) -> None:
        if self._transcript_buffer.strip():
            await self.on_utterance_complete(self._transcript_buffer.strip())
            self._transcript_buffer = ""

    async def _on_speech_started(self, *args, **kwargs) -> None:
        if not self._is_speaking:
            self._is_speaking = True
            await self.on_speech_started()
```

### 3.2 Negotiation Engine

```python
# engine/negotiation.py

class NegotiationEngine:
    """
    The brain of Marcus. Responsible for:
    1. Processing user input
    2. Managing LLM interactions
    3. Executing tools
    4. Maintaining state consistency
    """

    def __init__(self, session: NegotiationSession):
        self.session = session
        self.llm = LLMClient()
        self.tools = ToolExecutor(session)
        self.conversation = ConversationManager(session)
        self.state = StateManager(session.marcus)

    async def process_turn(
        self,
        user_input: str
    ) -> AsyncIterator[NegotiationEvent]:
        """
        Process a user turn and generate Marcus's response.
        Yields events for the response pipeline.
        """
        # Record user input
        self.conversation.add_user_turn(user_input)

        # Analyze input for claims
        claims = self._extract_claims(user_input)
        for claim in claims:
            self.session.marcus.candidate_claims[claim.type] = claim.value

        # LLM loop with tools
        async for event in self._llm_loop():
            yield event

    async def _llm_loop(self) -> AsyncIterator[NegotiationEvent]:
        """
        Run LLM with tool calling until complete response.
        """
        messages = self.conversation.get_messages_for_llm()

        while True:
            # Get LLM response
            response = await self.llm.chat_with_tools(
                messages=messages,
                tools=MARCUS_TOOLS,
                system=MARCUS_SYSTEM_PROMPT,
            )

            # Collect tool calls and content
            tool_calls = []
            content_chunks = []

            async for chunk in response:
                if chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)
                if chunk.content:
                    content_chunks.append(chunk.content)
                    yield TextChunkEvent(text=chunk.content)

            # If no tool calls, we're done
            if not tool_calls:
                full_response = "".join(content_chunks)
                self.conversation.add_assistant_turn(full_response)
                break

            # Execute tools
            for tool_call in tool_calls:
                result = await self.tools.execute(
                    name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                )

                # Yield UI events from tools
                if result.ui_event:
                    yield UIEvent(
                        type=result.ui_event.type,
                        data=result.ui_event.data
                    )

                # Add tool result to messages
                messages.append({
                    "role": "assistant",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result.data)
                })

    def _extract_claims(self, text: str) -> list[Claim]:
        """Extract salary claims, experience claims, etc."""
        claims = []

        # Simple pattern matching (could use NLP)
        salary_pattern = r'\$?(\d{2,3}),?(\d{3})'
        if match := re.search(salary_pattern, text):
            salary = int(match.group(1) + match.group(2))
            claims.append(Claim(type="salary_expectation", value=salary))

        years_pattern = r'(\d+)\s*years?\s*(of)?\s*experience'
        if match := re.search(years_pattern, text.lower()):
            years = int(match.group(1))
            claims.append(Claim(type="years_experience", value=years))

        return claims
```

### 3.3 Tool System

```python
# tools/definitions.py

MARCUS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_market_rate",
            "description": "Look up market salary data for a role. Use when verifying candidate salary claims.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string",
                        "description": "The job title to look up"
                    },
                    "location": {
                        "type": "string",
                        "description": "Geographic location (city or 'remote')"
                    },
                    "years_experience": {
                        "type": "integer",
                        "description": "Years of experience"
                    }
                },
                "required": ["job_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_internal_state",
            "description": "Update your patience and stress levels based on the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patience_delta": {
                        "type": "integer",
                        "description": "Change to patience (-20 to +10)"
                    },
                    "stress_delta": {
                        "type": "integer",
                        "description": "Change to stress (-10 to +20)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why you're adjusting"
                    }
                },
                "required": ["patience_delta", "stress_delta", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_offer",
            "description": "Make a salary offer to the candidate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "Base salary in dollars"
                    },
                    "is_final": {
                        "type": "boolean",
                        "description": "Whether this is your final offer"
                    },
                    "signing_bonus": {
                        "type": "integer",
                        "description": "Optional signing bonus"
                    }
                },
                "required": ["amount", "is_final"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_candidate_claim",
            "description": "Record something the candidate claimed for later reference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_type": {
                        "type": "string",
                        "enum": ["experience", "other_offer", "current_salary", "skill", "education"]
                    },
                    "claim_value": {
                        "type": "string"
                    },
                    "suspicious": {
                        "type": "boolean"
                    }
                },
                "required": ["claim_type", "claim_value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_ui_event",
            "description": "Send visual/haptic feedback to the user's phone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": ["patience_warning", "offer_made", "lie_detected", "impressed", "stressed"]
                    },
                    "intensity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"]
                    }
                },
                "required": ["event_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_negotiation",
            "description": "End the negotiation call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "outcome": {
                        "type": "string",
                        "enum": ["accepted", "rejected", "hung_up"]
                    },
                    "final_message": {
                        "type": "string"
                    }
                },
                "required": ["outcome"]
            }
        }
    }
]
```

```python
# tools/executor.py

@dataclass
class ToolResult:
    data: dict
    ui_event: Optional[UIEventData] = None


class ToolExecutor:
    """Dispatches and executes tool calls"""

    def __init__(self, session: NegotiationSession):
        self.session = session
        self._handlers = {
            "check_market_rate": self._check_market_rate,
            "adjust_internal_state": self._adjust_state,
            "make_offer": self._make_offer,
            "record_candidate_claim": self._record_claim,
            "trigger_ui_event": self._trigger_event,
            "end_negotiation": self._end_negotiation,
        }

    async def execute(self, name: str, arguments: dict) -> ToolResult:
        handler = self._handlers.get(name)
        if not handler:
            return ToolResult(data={"error": f"Unknown tool: {name}"})
        return await handler(**arguments)

    async def _check_market_rate(
        self,
        job_title: str,
        location: str = "US",
        years_experience: int = 0
    ) -> ToolResult:
        # Realistic market data simulation
        base_rates = {
            "software engineer": 95000,
            "senior software engineer": 140000,
            "staff software engineer": 180000,
            "principal engineer": 220000,
            "engineering manager": 170000,
        }

        base = base_rates.get(job_title.lower(), 100000)

        location_multipliers = {
            "san francisco": 1.35,
            "new york": 1.30,
            "seattle": 1.25,
            "austin": 1.05,
            "denver": 1.00,
            "remote": 0.95,
        }
        multiplier = location_multipliers.get(location.lower(), 1.0)

        experience_bonus = min(years_experience * 5000, 40000)

        market_rate = int((base + experience_bonus) * multiplier)

        result = {
            "job_title": job_title,
            "location": location,
            "years_experience": years_experience,
            "market_rate_p25": int(market_rate * 0.85),
            "market_rate_p50": market_rate,
            "market_rate_p75": int(market_rate * 1.15),
            "market_rate_p90": int(market_rate * 1.30),
            "source": "Industry salary benchmarks (2024)"
        }

        # Store for reference
        self.session.marcus.verified_facts["market_rate"] = result

        return ToolResult(data=result)

    async def _adjust_state(
        self,
        patience_delta: int,
        stress_delta: int,
        reason: str
    ) -> ToolResult:
        old_patience = self.session.marcus.patience
        old_stress = self.session.marcus.stress

        self.session.marcus.patience = max(0, min(100,
            self.session.marcus.patience + patience_delta
        ))
        self.session.marcus.stress = max(0, min(100,
            self.session.marcus.stress + stress_delta
        ))

        # Update emotional state
        self._update_emotional_state()

        # Generate UI event if significant change
        ui_event = None
        if self.session.marcus.patience < 30 and old_patience >= 30:
            ui_event = UIEventData(type="patience_warning", intensity="high")
        elif self.session.marcus.stress > 70 and old_stress <= 70:
            ui_event = UIEventData(type="stressed", intensity="medium")

        return ToolResult(
            data={
                "patience": {"old": old_patience, "new": self.session.marcus.patience},
                "stress": {"old": old_stress, "new": self.session.marcus.stress},
                "emotional_state": self.session.marcus.emotional_state,
                "reason": reason
            },
            ui_event=ui_event
        )

    async def _make_offer(
        self,
        amount: int,
        is_final: bool,
        signing_bonus: int = 0
    ) -> ToolResult:
        # Enforce budget ceiling
        amount = min(amount, self.session.marcus.budget_ceiling)

        self.session.marcus.current_offer = amount
        self.session.marcus.offers_made.append(amount)
        self.session.marcus.rounds_count += 1

        if is_final:
            self.session.marcus.phase = NegotiationPhase.FINAL_OFFER

        return ToolResult(
            data={
                "offer_amount": amount,
                "signing_bonus": signing_bonus,
                "total_first_year": amount + signing_bonus,
                "is_final": is_final,
                "round_number": self.session.marcus.rounds_count
            },
            ui_event=UIEventData(
                type="offer_made",
                intensity="high" if is_final else "medium"
            )
        )

    async def _trigger_event(
        self,
        event_type: str,
        intensity: str = "medium"
    ) -> ToolResult:
        return ToolResult(
            data={"triggered": event_type, "intensity": intensity},
            ui_event=UIEventData(type=event_type, intensity=intensity)
        )

    async def _end_negotiation(
        self,
        outcome: str,
        final_message: str = ""
    ) -> ToolResult:
        self.session.marcus.phase = NegotiationPhase.CONCLUDED
        self.session.outcome = outcome

        if outcome == "accepted":
            self.session.final_salary = self.session.marcus.current_offer

        return ToolResult(
            data={
                "outcome": outcome,
                "final_salary": self.session.final_salary,
                "final_message": final_message
            },
            ui_event=UIEventData(
                type="hang_up" if outcome == "hung_up" else "negotiation_complete",
                intensity="high"
            )
        )

    def _update_emotional_state(self):
        """Derive emotional state from patience/stress"""
        marcus = self.session.marcus

        if marcus.patience < 20:
            marcus.emotional_state = EmotionalState.ANNOYED
        elif marcus.stress > 70:
            marcus.emotional_state = EmotionalState.STRESSED
        elif marcus.patience < 40:
            marcus.emotional_state = EmotionalState.IMPATIENT
        elif marcus.stress > 40:
            marcus.emotional_state = EmotionalState.SKEPTICAL
        elif marcus.stress < 20 and marcus.patience > 70:
            marcus.emotional_state = EmotionalState.NEUTRAL
        else:
            marcus.emotional_state = EmotionalState.NEUTRAL
```

### 3.4 Interruption System

```python
# core/interruption.py

class InterruptionManager:
    """
    Handles bidirectional interruption:
    1. User interrupting Marcus (stop TTS)
    2. Marcus interrupting user (too much silence/rambling)
    """

    def __init__(
        self,
        session: NegotiationSession,
        response_pipeline: 'ResponsePipeline',
        send_to_client: Callable[[dict], Awaitable[None]]
    ):
        self.session = session
        self.response = response_pipeline
        self.send = send_to_client

        self._silence_start: float = None
        self._user_speech_start: float = None
        self._marcus_speaking: bool = False
        self._silence_check_task: asyncio.Task = None

    async def on_marcus_start_speaking(self):
        """Called when Marcus starts TTS"""
        self._marcus_speaking = True

    async def on_marcus_stop_speaking(self):
        """Called when Marcus finishes TTS"""
        self._marcus_speaking = False
        self._silence_start = time.time()
        self._start_silence_monitor()

    async def on_user_speech_started(self):
        """Called when user starts speaking"""
        self._user_speech_start = time.time()
        self._silence_start = None

        # If Marcus was speaking, this is an interruption
        if self._marcus_speaking:
            await self._handle_user_interrupt()

    async def on_user_speech_ended(self):
        """Called when user stops speaking"""
        self._user_speech_start = None
        self._silence_start = time.time()
        self._start_silence_monitor()

    async def _handle_user_interrupt(self):
        """User interrupted Marcus mid-speech"""
        # Stop TTS
        await self.response.interrupt()

        # Small patience penalty
        self.session.marcus.patience = max(0,
            self.session.marcus.patience - 5
        )

        # Notify client
        await self.send({
            "type": "state_update",
            "patience": self.session.marcus.patience
        })

    def _start_silence_monitor(self):
        """Start monitoring for prolonged silence"""
        if self._silence_check_task:
            self._silence_check_task.cancel()
        self._silence_check_task = asyncio.create_task(
            self._monitor_silence()
        )

    async def _monitor_silence(self):
        """Check if user is silent too long"""
        while self._silence_start is not None:
            elapsed = (time.time() - self._silence_start) * 1000  # ms

            threshold = self._calculate_threshold()

            if elapsed > threshold:
                await self._marcus_should_interrupt()
                break

            await asyncio.sleep(0.1)

    def _calculate_threshold(self) -> int:
        """Dynamic threshold based on patience"""
        base_threshold = 3000  # 3 seconds

        # Impatient Marcus has lower threshold
        patience_factor = self.session.marcus.patience / 100
        adjusted = int(base_threshold * patience_factor)

        return max(adjusted, 800)  # Minimum 800ms

    async def _marcus_should_interrupt(self):
        """Marcus decides to interrupt due to silence"""
        # Only if patience is low enough
        if self.session.marcus.patience > 50:
            return

        phrases = [
            "Are you still there?",
            "Let me jump in here—",
            "I've got another call in five minutes—",
            "Look, I need an answer—",
        ]

        # Pick phrase based on patience
        idx = min(3, (100 - self.session.marcus.patience) // 25)
        phrase = phrases[idx]

        # Patience penalty
        self.session.marcus.patience = max(0,
            self.session.marcus.patience - 10
        )

        # Send interruption
        await self.send({
            "type": "marcus_interrupting",
            "patience": self.session.marcus.patience
        })

        # Return phrase for TTS
        return phrase
```

---

## 4. Message Protocol

### 4.1 WebSocket Message Types

#### Client → Server

| Type | Format | Description |
|------|--------|-------------|
| `audio` | Binary | Raw PCM audio chunk (16-bit, 16kHz, mono) |
| `control` | JSON | Session control messages |

```typescript
// Control message types
interface ControlMessage {
  type: 'start_session' | 'end_session' | 'mute' | 'unmute';
  payload?: any;
}
```

#### Server → Client

| Type | Format | Description |
|------|--------|-------------|
| `audio` | Binary | TTS audio chunk |
| `transcript` | JSON | Real-time transcription |
| `state_update` | JSON | State changes (patience, offers) |
| `event` | JSON | UI/haptic events |
| `control` | JSON | Session control |

```typescript
// Server message types
interface TranscriptMessage {
  type: 'transcript';
  speaker: 'user' | 'marcus';
  text: string;
  is_final: boolean;
}

interface StateUpdateMessage {
  type: 'state_update';
  patience?: number;
  stress?: number;
  current_offer?: number;
  phase?: string;
  emotional_state?: string;
}

interface EventMessage {
  type: 'event';
  event_type: 'offer_made' | 'patience_warning' | 'lie_detected' | 'impressed' | 'hang_up';
  intensity: 'low' | 'medium' | 'high';
  data?: any;
}

interface ControlMessage {
  type: 'control';
  action: 'stop_audio' | 'session_ended' | 'error';
  payload?: any;
}
```

### 4.2 Message Sequence: Complete Turn

```
Client                          Server                         External
  │                               │                               │
  │──── audio chunk ────────────►│                               │
  │──── audio chunk ────────────►│──── audio stream ───────────►│ Deepgram
  │──── audio chunk ────────────►│                               │
  │                               │◄─── interim transcript ──────│
  │◄─── transcript (interim) ────│                               │
  │                               │                               │
  │ (user stops speaking)         │                               │
  │                               │◄─── utterance_end ───────────│
  │                               │                               │
  │                               │──── chat + tools ───────────►│ LLM
  │                               │◄─── tool calls ──────────────│
  │                               │     (execute tools locally)   │
  │◄─── state_update ────────────│                               │
  │◄─── event ───────────────────│                               │
  │                               │◄─── response text ───────────│
  │                               │                               │
  │                               │──── text ───────────────────►│ Deepgram
  │◄─── audio chunk ─────────────│◄─── audio ───────────────────│ Aura
  │◄─── audio chunk ─────────────│◄─── audio ───────────────────│
  │◄─── transcript (marcus) ─────│                               │
  │                               │                               │
  │ (marcus finishes speaking)    │                               │
  │◄─── state_update ────────────│                               │
  │                               │                               │
```

---

## 5. Error Handling Architecture

### 5.1 Error Categories

```python
class ErrorCategory(Enum):
    CONNECTION = "connection"       # WebSocket, network issues
    EXTERNAL_SERVICE = "external"   # Deepgram, LLM API failures
    VALIDATION = "validation"       # Invalid input
    STATE = "state"                 # Invalid state transitions
    INTERNAL = "internal"           # Unexpected errors


@dataclass
class AppError:
    category: ErrorCategory
    code: str
    message: str
    recoverable: bool
    user_message: str  # Safe to show user


class ErrorHandler:
    async def handle(self, error: Exception, context: dict) -> AppError:
        if isinstance(error, ConnectionError):
            return AppError(
                category=ErrorCategory.CONNECTION,
                code="CONNECTION_LOST",
                message=str(error),
                recoverable=True,
                user_message="Connection lost. Reconnecting..."
            )
        elif isinstance(error, DeepgramError):
            return AppError(
                category=ErrorCategory.EXTERNAL_SERVICE,
                code="STT_ERROR",
                message=str(error),
                recoverable=True,
                user_message="Voice recognition temporarily unavailable."
            )
        # ... etc
```

### 5.2 Recovery Strategies

| Error Type | Strategy | User Impact |
|------------|----------|-------------|
| STT connection lost | Reconnect + replay buffer | Brief pause in transcription |
| LLM timeout | Retry once, then fallback response | Slightly delayed response |
| TTS failure | Skip audio, show text | User reads instead of hears |
| WebSocket disconnect | Auto-reconnect, restore session | Brief interruption |
| Session not found | Create new session | Start over |

---

## 6. Security Architecture

### 6.1 Input Validation

```python
class InputValidator:
    # Audio constraints
    MAX_CHUNK_SIZE = 64 * 1024      # 64KB per chunk
    MAX_CHUNKS_PER_SECOND = 15      # Rate limit
    ALLOWED_SAMPLE_RATE = 16000
    ALLOWED_CHANNELS = 1

    # Message constraints
    MAX_MESSAGE_SIZE = 1024
    ALLOWED_MESSAGE_TYPES = {'start_session', 'end_session', 'mute', 'unmute'}

    def validate_audio(self, chunk: bytes) -> bool:
        if len(chunk) > self.MAX_CHUNK_SIZE:
            raise ValidationError("Audio chunk too large")
        return True

    def validate_message(self, message: dict) -> bool:
        if len(json.dumps(message)) > self.MAX_MESSAGE_SIZE:
            raise ValidationError("Message too large")
        if message.get('type') not in self.ALLOWED_MESSAGE_TYPES:
            raise ValidationError("Invalid message type")
        return True
```

### 6.2 Rate Limiting

```python
class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    async def check(self, session_id: str, action: str) -> bool:
        key = f"{session_id}:{action}"
        bucket = self._buckets.setdefault(key, TokenBucket(
            capacity=self._get_capacity(action),
            refill_rate=self._get_refill_rate(action)
        ))
        return bucket.consume()

    def _get_capacity(self, action: str) -> int:
        capacities = {
            'audio_chunk': 20,      # 20 chunks burst
            'control_message': 10,  # 10 messages burst
            'session_create': 3,    # 3 sessions burst
        }
        return capacities.get(action, 10)
```

---

## 7. Testing Strategy

### 7.1 Test Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Full negotiation flows
                    │   (5% effort)   │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │  Integration Tests    │  ← Component interactions
                  │     (20% effort)      │
                  └───────────────────────┘
              ┌───────────────────────────────┐
              │        Unit Tests             │  ← Individual functions
              │       (75% effort)            │
              └───────────────────────────────┘
```

### 7.2 Critical Test Scenarios

```python
# For hackathon, focus on these scenarios

class TestScenarios:
    async def test_winning_negotiation(self):
        """User follows optimal path, gets max offer"""
        session = create_session()

        # Simulate optimal conversation
        turns = [
            "Hi Marcus, excited about the opportunity",
            "I have 5 years of experience at top tech companies",
            "I'm currently interviewing at Google and Meta",
            "Based on market data, I'm looking at $145k",
            "I can accept today at $142k",
        ]

        for turn in turns:
            await process_turn(session, turn)

        assert session.outcome == "accepted"
        assert session.final_salary >= 140000

    async def test_failing_negotiation(self):
        """User fumbles, Marcus hangs up"""
        session = create_session()

        # Simulate poor conversation
        turns = [
            "uh, hey, so like...",
            "I want $200k because my friend makes that",
            "whatever, just make me an offer",
            "that's insulting, I deserve more",
            "fine, I'll just go to Google",
        ]

        for turn in turns:
            await process_turn(session, turn)

        assert session.outcome == "hung_up"
        assert session.marcus.patience == 0

    async def test_interruption_handling(self):
        """Verify interruptions work both ways"""
        session = create_session()

        # Start Marcus speaking
        await start_marcus_response(session)
        assert session.response_pipeline.is_speaking

        # User interrupts
        await simulate_user_speech(session)
        assert not session.response_pipeline.is_speaking
        assert session.marcus.patience < 100  # Penalty applied
```

---

## 8. Deployment Considerations

### 8.1 Hackathon Setup

```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend:/app

  # Expo runs on host machine, connects to backend
```

### 8.2 Environment Variables

```bash
# .env.example
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
LOG_LEVEL=INFO
DEBUG=false
```

### 8.3 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Connection time | < 500ms | Time to WebSocket open |
| First transcript | < 1s | Audio start → first text |
| LLM first token | < 500ms | Request → first token |
| TTS first audio | < 300ms | Text → first audio byte |
| Total turn latency | < 1.5s | User stops → Marcus starts |
