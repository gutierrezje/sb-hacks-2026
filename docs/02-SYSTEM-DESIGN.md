# The Salary Dojo - System Design Document

## 1. System Overview

### 1.1 Purpose

The Salary Dojo is a real-time voice-based negotiation training application where users practice salary negotiation against an AI recruiter named "Marcus." The system must handle bidirectional audio streaming, natural language understanding, autonomous decision-making, and dynamic state management—all with sub-second latency.

### 1.2 Key Requirements

| Requirement | Target | Priority |
|-------------|--------|----------|
| End-to-end latency | < 1.5 seconds | Critical |
| Interruption response | < 300ms | Critical |
| Concurrent sessions | 10+ | Medium |
| Session duration | 5-10 minutes | High |
| State consistency | 100% | Critical |

### 1.3 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                 │
│                        React + Vite Web App                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │ Audio       │  │ WebSocket   │  │ AI Avatar   │  │ UI State     │   │
│  │ Capture     │  │ Manager     │  │ (Marcus)    │  │ Manager      │   │
│  │ (Web Audio) │  │             │  │             │  │              │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          │ PCM Audio      │ Binary/JSON    │ State Updates  │ Events
          │                │                │                │
          ▼                ▼                ▼                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         TRANSPORT LAYER                                │
│                    WebSocket (wss://api.salarydojo.com)                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Message Types:                                                  │  │
│  │  • audio_chunk (binary) - Raw PCM audio from client              │  │
│  │  • transcript (json) - Real-time transcription updates           │  │
│  │  • marcus_audio (binary) - TTS audio chunks                      │  │
│  │  • state_update (json) - UI state changes                        │  │
│  │  • event (json) - Visual/avatar triggers                         │  │
│  │  • control (json) - Session management                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVER LAYER                                   │
│                     Python FastAPI Application                          │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    CONNECTION HANDLER                              │ │
│  │  • Session creation/destruction                                    │ │
│  │  • Message routing                                                 │ │
│  │  • Error handling                                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│           │                    │                      │                 │
│           ▼                    ▼                      ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐      │
│  │ Audio        │    │ Negotiation  │    │ Response              │      │
│  │ Pipeline     │    │ Engine       │    │ Pipeline              │      │
│  │              │    │              │    │                       │      │
│  │ • STT        │───▶│ • State Mgmt │───▶│ • TTS                 │      │
│  │ • VAD        │    │ • LLM        │    │ • Audio Streaming     │      │
│  │ • Buffering  │    │ • Tools      │    │ • Interruption        │      │
│  └──────────────┘    └──────────────┘    └───────────────────────┘      │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                      SESSION STORE                             │    │
│  │  In-Memory (dict[session_id, NegotiationSession])              │    │
│  │  • Marcus state (budget, patience, stress, offers)             │    │
│  │  • Conversation history                                        │    │
│  │  • Candidate claims & verified facts                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│    EXTERNAL SERVICES    │    │    EXTERNAL SERVICES    │
│                         │    │                         │
│  ┌───────────────────┐  │    │  ┌───────────────────┐  │
│  │ Deepgram Flux     │  │    │  │ OpenAI / Anthropic│  │
│  │ (Streaming STT)   │  │    │  │ (LLM + Tools)     │  │
│  └───────────────────┘  │    │  └───────────────────┘  │
│                         │    │                         │
│  ┌───────────────────┐  │    │                         │
│  │ Deepgram Aura     │  │    │                         │
│  │ (Streaming TTS)   │  │    │                         │
│  └───────────────────┘  │    │                         │
└─────────────────────────┘    └─────────────────────────┘
```

---

## 2. Component Design

### 2.1 Client Application (React + Vite)

#### 2.1.1 Audio Capture Module

```typescript
interface AudioCaptureConfig {
  sampleRate: 16000;           // Deepgram requirement
  channels: 1;                  // Mono
  encoding: 'pcm_s16le';       // 16-bit signed little-endian
  chunkDuration: 100;          // ms - balance latency vs overhead
}

interface AudioCaptureState {
  isRecording: boolean;
  isMuted: boolean;
  audioLevel: number;          // For visual feedback
  error: Error | null;
}
```

**Responsibilities:**
- Capture microphone audio using Web Audio API (AudioWorklet)
- Convert to PCM format compatible with Deepgram
- Chunk audio into 100ms segments
- Stream chunks to WebSocket
- Monitor audio levels for visual feedback (drives avatar mouth movement)

#### 2.1.2 WebSocket Manager

```typescript
interface WebSocketMessage {
  type: 'audio' | 'transcript' | 'state' | 'event' | 'control';
  payload: any;
  timestamp: number;
}

interface WebSocketState {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  latency: number;             // Measured round-trip time
  lastHeartbeat: number;
}
```

**Responsibilities:**
- Maintain persistent WebSocket connection
- Handle binary (audio) and JSON (control) messages
- Implement reconnection with exponential backoff
- Measure and report latency
- Route messages to appropriate handlers

#### 2.1.3 UI State Manager

```typescript
interface NegotiationUIState {
  phase: 'waiting' | 'listening' | 'thinking' | 'speaking';
  patience: number;            // 0-100, drives patience meter
  currentOffer: number | null;
  transcript: TranscriptEntry[];
  marcusEmotion: 'neutral' | 'impressed' | 'skeptical' | 'stressed';
}

interface TranscriptEntry {
  speaker: 'user' | 'marcus';
  text: string;
  timestamp: number;
  isFinal: boolean;
}
```

**Responsibilities:**
- Maintain UI state synchronized with server
- Handle optimistic updates for responsiveness
- Manage transcript display with real-time updates
- Animate state transitions smoothly

#### 2.1.4 Emoji Avatar Component

```typescript
interface EmojiAvatarProps {
  emotion: 'neutral' | 'impressed' | 'skeptical' | 'stressed';
  isSpeaking: boolean;           // Drives pulsing animation
}

const EMOTION_EMOJIS = {
  neutral: '😐',
  impressed: '😊',
  very_impressed: '😄',
  skeptical: '🤨',
  stressed: '😰',
  done: '😑'
};
```

**Responsibilities:**
- Display emoji based on Marcus's emotional state
- Animate transitions between emotions (fade/scale)
- Pulse or glow when Marcus is speaking
- Simple CSS animations for visual feedback

**Expression Mapping:**
| Emotion | Emoji | Animation |
|---------|-------|----------|
| Neutral | 😐 | None |
| Impressed | 😊 | Warm glow |
| Very Impressed | 😄 | Bounce + glow |
| Skeptical | 🤨 | Slight tilt |
| Stressed | 😰 | Shake + red tint |
| Done | 😑 | Fade to gray |

---

### 2.2 Server Application (FastAPI)

#### 2.2.1 Connection Handler

```python
class ConnectionHandler:
    """
    Manages WebSocket lifecycle and message routing.
    One instance per active connection.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.session_id: str = None
        self.session: NegotiationSession = None
        self.audio_pipeline: AudioPipeline = None
        self.negotiation_engine: NegotiationEngine = None
        self.response_pipeline: ResponsePipeline = None

    async def handle_connection(self):
        """Main connection loop"""
        await self.websocket.accept()
        self.session_id = str(uuid4())
        self.session = NegotiationSession(session_id=self.session_id)

        # Initialize pipelines
        self.audio_pipeline = AudioPipeline(
            on_transcript=self._handle_transcript,
            on_utterance_end=self._handle_turn_complete
        )
        self.negotiation_engine = NegotiationEngine(self.session)
        self.response_pipeline = ResponsePipeline(
            websocket=self.websocket,
            on_interrupted=self._handle_interruption
        )

        try:
            await self._message_loop()
        finally:
            await self._cleanup()

    async def _message_loop(self):
        """Process incoming messages"""
        async for message in self.websocket.iter_bytes():
            if isinstance(message, bytes):
                await self.audio_pipeline.process_audio(message)
            else:
                await self._handle_control_message(json.loads(message))
```

#### 2.2.2 Audio Pipeline

```python
class AudioPipeline:
    """
    Handles incoming audio: buffering, STT, VAD.
    Produces transcripts and turn-completion signals.
    """

    def __init__(self, on_transcript: Callable, on_utterance_end: Callable):
        self.on_transcript = on_transcript
        self.on_utterance_end = on_utterance_end
        self.deepgram: DeepgramFluxHandler = None
        self.audio_buffer: bytes = b""
        self.transcript_buffer: str = ""
        self.last_audio_time: float = 0
        self.is_user_speaking: bool = False

    async def start(self):
        """Initialize Deepgram connection"""
        self.deepgram = DeepgramFluxHandler(
            on_transcript=self._process_transcript,
            on_utterance_end=self._process_utterance_end
        )
        await self.deepgram.start()

    async def process_audio(self, chunk: bytes):
        """Process incoming audio chunk"""
        self.last_audio_time = time.time()
        self.is_user_speaking = True
        await self.deepgram.send_audio(chunk)

    async def _process_transcript(self, text: str, is_final: bool):
        """Handle transcript from Deepgram"""
        if is_final:
            self.transcript_buffer += text + " "
        await self.on_transcript(text, is_final)

    async def _process_utterance_end(self):
        """User finished speaking - trigger response"""
        if self.transcript_buffer.strip():
            await self.on_utterance_end(self.transcript_buffer.strip())
            self.transcript_buffer = ""
        self.is_user_speaking = False
```

#### 2.2.3 Negotiation Engine

```python
class NegotiationEngine:
    """
    The brain: LLM integration, tool execution, state management.
    """

    def __init__(self, session: NegotiationSession):
        self.session = session
        self.llm_client = LLMClient()
        self.tool_executor = ToolExecutor(session)
        self.conversation_manager = ConversationManager(session)

    async def process_user_input(self, transcript: str) -> AsyncIterator[str]:
        """
        Process user speech and generate Marcus's response.
        Yields response chunks for streaming TTS.
        """
        # Add user turn to conversation
        self.conversation_manager.add_user_turn(transcript)

        # Build messages for LLM
        messages = self.conversation_manager.get_messages()

        # Get LLM response with tool calls
        async for chunk in self._llm_loop(messages):
            yield chunk

    async def _llm_loop(self, messages: list[dict]) -> AsyncIterator[str]:
        """
        LLM loop with tool execution.
        Continues until LLM produces final response without tool calls.
        """
        while True:
            response = await self.llm_client.chat(
                messages=messages,
                tools=MARCUS_TOOLS,
                stream=True
            )

            tool_calls = []
            response_text = ""

            async for chunk in response:
                if chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)
                if chunk.content:
                    response_text += chunk.content
                    yield chunk.content

            if not tool_calls:
                # No more tool calls - we're done
                self.conversation_manager.add_assistant_turn(response_text)
                break

            # Execute tools and continue loop
            for tool_call in tool_calls:
                result = await self.tool_executor.execute(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
```

#### 2.2.4 Response Pipeline

```python
class ResponsePipeline:
    """
    Handles outgoing responses: TTS streaming, interruption handling.
    """

    def __init__(self, websocket: WebSocket, on_interrupted: Callable):
        self.websocket = websocket
        self.on_interrupted = on_interrupted
        self.tts = TTSController()
        self.is_speaking = False
        self._cancel_event = asyncio.Event()

    async def speak(self, text_stream: AsyncIterator[str]):
        """
        Stream text to TTS to client.
        Can be interrupted by calling interrupt().
        """
        self.is_speaking = True
        self._cancel_event.clear()

        try:
            # Buffer text until we have enough for natural speech
            text_buffer = ""
            async for chunk in text_stream:
                text_buffer += chunk

                # Send to TTS when we have a sentence or pause
                if self._should_flush(text_buffer):
                    await self._tts_and_stream(text_buffer)
                    text_buffer = ""

                    if self._cancel_event.is_set():
                        break

            # Flush remaining text
            if text_buffer and not self._cancel_event.is_set():
                await self._tts_and_stream(text_buffer)

        finally:
            self.is_speaking = False

    async def interrupt(self):
        """Stop current speech immediately"""
        self._cancel_event.set()
        await self.websocket.send_json({"type": "stop_audio"})
        await self.on_interrupted()

    async def _tts_and_stream(self, text: str):
        """Convert text to speech and stream to client"""
        async for audio_chunk in self.tts.synthesize(text):
            if self._cancel_event.is_set():
                break
            await self.websocket.send_bytes(audio_chunk)

    def _should_flush(self, text: str) -> bool:
        """Determine if we should send text to TTS"""
        # Flush on sentence boundaries or after enough text
        return (
            text.endswith(('.', '!', '?', ',')) or
            len(text) > 100
        )
```

---

### 2.3 External Service Integrations

#### 2.3.1 Deepgram Flux (STT)

```python
class DeepgramFluxHandler:
    """Real-time streaming speech-to-text"""

    LIVE_OPTIONS = {
        "model": "nova-2",
        "language": "en-US",
        "smart_format": True,
        "interim_results": True,
        "utterance_end_ms": 1000,    # Key for turn detection
        "vad_events": True,          # Voice activity detection
        "punctuate": True,
        "diarize": False,            # Single speaker
    }

    async def start(self):
        """Establish streaming connection"""
        self.connection = self.client.listen.asynclive.v("1")
        self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
        self.connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
        self.connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
        await self.connection.start(LiveOptions(**self.LIVE_OPTIONS))
```

**Key Configuration Choices:**
- `utterance_end_ms: 1000` - 1 second of silence triggers turn end
- `interim_results: True` - Enables real-time transcript display
- `vad_events: True` - Detect when user starts/stops speaking

#### 2.3.2 Deepgram Aura (TTS)

```python
class TTSController:
    """Text-to-speech with streaming output"""

    VOICE_CONFIGS = {
        "neutral": "aura-asteria-en",
        "stressed": "aura-luna-en",      # Different voice for emotion
        "impatient": "aura-stella-en",
    }

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral"
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks for text"""
        voice = self.VOICE_CONFIGS.get(emotion, "aura-asteria-en")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepgram.com/v1/speak",
                headers={"Authorization": f"Token {API_KEY}"},
                json={"text": text},
                params={
                    "model": voice,
                    "encoding": "linear16",
                    "sample_rate": 16000,
                    "container": "none",
                }
            ) as response:
                async for chunk in response.content.iter_chunked(4096):
                    yield chunk
```

#### 2.3.3 LLM Client (OpenAI/Anthropic)

```python
class LLMClient:
    """Unified interface for LLM with function calling"""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "openai":
            self.client = AsyncOpenAI()
            self.model = "gpt-4-turbo-preview"
        else:
            self.client = AsyncAnthropic()
            self.model = "claude-3-sonnet-20240229"

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict],
        stream: bool = True
    ) -> AsyncIterator[ChatChunk]:
        """Stream chat completion with tool support"""
        if self.provider == "openai":
            return self._openai_chat(messages, tools, stream)
        else:
            return self._anthropic_chat(messages, tools, stream)

    async def _openai_chat(self, messages, tools, stream):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=stream,
            max_tokens=500,        # Keep responses concise
            temperature=0.8,      # Some personality variation
        )
        async for chunk in response:
            yield self._normalize_chunk(chunk)
```

---

## 3. Data Flow

### 3.1 Happy Path: User Turn

```
1. User speaks into phone microphone
   ↓
2. Audio captured in 100ms PCM chunks
   ↓
3. Chunks sent via WebSocket (binary)
   ↓
4. Server buffers and streams to Deepgram Flux
   ↓
5. Deepgram returns interim transcripts → sent to client for display
   ↓
6. User stops speaking (1s silence)
   ↓
7. Deepgram fires utterance_end event
   ↓
8. Final transcript sent to Negotiation Engine
   ↓
9. LLM processes with tools (may loop multiple times)
   ↓
10. Response text streamed to TTS
    ↓
11. TTS audio chunks streamed to client
    ↓
12. Client plays audio through speaker
    ↓
13. State updates sent alongside audio (patience, offers, etc.)
    ↓
14. Client updates UI (patience meter, offer display, haptics)
```

### 3.2 Interruption Flow: User Interrupts Marcus

```
1. Marcus is speaking (TTS streaming to client)
   ↓
2. User starts speaking (audio chunks received)
   ↓
3. Server detects sustained speech (300ms+ of audio)
   ↓
4. InterruptionManager.interrupt() called
   ↓
5. TTS streaming cancelled
   ↓
6. "stop_audio" message sent to client
   ↓
7. Client stops playback immediately
   ↓
8. Patience reduced by 5 points
   ↓
9. State update sent to client
   ↓
10. System waits for user to finish speaking
    ↓
11. Normal turn flow resumes at step 7 of happy path
```

### 3.3 Interruption Flow: Marcus Interrupts User

```
1. User is speaking (audio chunks being processed)
   ↓
2. Silence detected for threshold duration
   (threshold = base 3s, reduced by low patience)
   ↓
3. If patience < 50: Marcus decides to interrupt
   ↓
4. Interruption phrase selected based on patience level
   ↓
5. "marcus_interrupting" event sent to client
   ↓
6. Client shows visual indicator
   ↓
7. Interruption phrase sent to TTS → client
   ↓
8. Normal response flow continues
   ↓
9. Patience reduced by 10 points
```

---

## 4. State Management

### 4.1 Session State Structure

```python
@dataclass
class NegotiationSession:
    """Complete state for one negotiation session"""

    # Identity
    session_id: str
    started_at: datetime

    # Marcus's hidden state
    marcus: MarcusState

    # Conversation
    conversation: list[ConversationTurn]

    # Outcome
    outcome: Optional[str] = None       # "accepted", "rejected", "hung_up"
    final_salary: Optional[int] = None


@dataclass
class MarcusState:
    """Marcus's internal state - hidden from user"""

    # Budget constraints
    budget_ceiling: int = 150_000       # Absolute maximum
    budget_comfortable: int = 120_000   # Happy to pay
    current_offer: int = 95_000         # Starting point

    # Emotional state
    patience: int = 100                 # 0-100, 0 = hang up
    stress: int = 0                     # 0-100, high = candidate winning
    emotional_state: EmotionalState = EmotionalState.NEUTRAL

    # Conversation tracking
    phase: NegotiationPhase = NegotiationPhase.INTRODUCTION
    candidate_claims: dict = field(default_factory=dict)
    verified_facts: dict = field(default_factory=dict)
    lies_detected: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)

    # Turn management
    user_speaking: bool = False
    silence_duration_ms: int = 0

    # Negotiation progress
    offers_made: list[int] = field(default_factory=list)
    counteroffers_received: list[int] = field(default_factory=list)
    rounds_count: int = 0
```

### 4.2 State Transitions

```
INTRODUCTION ──────────────────────────────────────────────┐
│                                                          │
│ User introduces themselves                               │
│ Marcus asks about background                             │
▼                                                          │
DISCOVERY ─────────────────────────────────────────────────┤
│                                                          │
│ Marcus learns about candidate                            │
│ Claims are recorded and verified                         │
│ Tools: record_candidate_claim, check_market_rate         │
▼                                                          │
INITIAL_OFFER ─────────────────────────────────────────────┤
│                                                          │
│ Marcus makes first offer ($95k)                          │
│ Tool: make_offer(is_final=false)                         │
▼                                                          │
NEGOTIATION ───────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Loop:                                                 │ │
│ │ • User makes counter-offer                           │ │
│ │ • Marcus evaluates (check_market_rate, adjust_state) │ │
│ │ • Marcus responds (make_offer or pushback)           │ │
│ │ • Exit conditions:                                   │ │
│ │   - patience <= 0 → CONCLUDED (hung_up)             │ │
│ │   - rounds > 5 → FINAL_OFFER                        │ │
│ │   - agreement reached → CONCLUDED (accepted)        │ │
│ └──────────────────────────────────────────────────────┘ │
▼                                                          │
FINAL_OFFER ───────────────────────────────────────────────┤
│                                                          │
│ Marcus: "This is my final offer"                         │
│ Tool: make_offer(is_final=true)                          │
│ User must accept or reject                               │
▼                                                          │
CONCLUDED ─────────────────────────────────────────────────┘
│
│ Outcomes:
│ • accepted: Deal reached, final_salary set
│ • rejected: User declined final offer
│ • hung_up: Marcus ended call (patience = 0)
│
▼
Results screen displayed
```

### 4.3 Patience Decay Rules

| Event | Patience Change |
|-------|-----------------|
| User rambles (>20s without substance) | -10 |
| User makes unreasonable demand (>$160k) | -15 |
| User caught in lie | -20 |
| User interrupts Marcus | -5 |
| User is well-prepared | +5 |
| User has competing offer (verified) | +0 (but stress +15) |
| Silence too long (Marcus interrupts) | -10 |
| Each negotiation round | -5 |

### 4.4 Stress Accumulation Rules

| Event | Stress Change |
|-------|---------------|
| User cites accurate market data | +10 |
| User has verified competing offer | +15 |
| User demonstrates unique skills | +10 |
| User asks good questions about role | +5 |
| User accepts lower offer | -20 |
| User seems desperate | -15 |

---

## 5. Error Handling

### 5.1 Connection Errors

```python
class ConnectionErrorHandler:
    MAX_RECONNECT_ATTEMPTS = 3
    BACKOFF_BASE = 1.5  # seconds

    async def handle_disconnect(self, session_id: str):
        """Handle unexpected disconnect"""
        session = sessions.get(session_id)
        if session:
            # Preserve state for potential reconnect
            session.disconnected_at = datetime.utcnow()

            # Allow 30s window for reconnect
            await asyncio.sleep(30)

            if session.disconnected_at:  # Still disconnected
                await self._cleanup_session(session_id)
```

### 5.2 Audio Pipeline Errors

```python
class AudioPipelineErrorHandler:
    async def handle_stt_error(self, error: Exception):
        """Handle Deepgram STT errors"""
        if isinstance(error, ConnectionError):
            # Attempt reconnect
            await self.audio_pipeline.restart()
        elif isinstance(error, RateLimitError):
            # Back off and retry
            await asyncio.sleep(1)
            await self.audio_pipeline.restart()
        else:
            # Log and notify client
            logger.error(f"STT error: {error}")
            await self.websocket.send_json({
                "type": "error",
                "message": "Voice recognition temporarily unavailable"
            })
```

### 5.3 LLM Errors

```python
class LLMErrorHandler:
    async def handle_llm_error(self, error: Exception):
        """Handle LLM API errors"""
        if isinstance(error, RateLimitError):
            # Use cached response or simplified logic
            return self._get_fallback_response()
        elif isinstance(error, TimeoutError):
            # Retry once
            return await self.llm_client.chat(messages, tools, retry=True)
        else:
            # Marcus says something generic
            return "Let me think about that for a moment..."

    def _get_fallback_response(self) -> str:
        """Generic responses when LLM unavailable"""
        fallbacks = [
            "That's an interesting point. Can you tell me more?",
            "I see. And what are your salary expectations?",
            "Let me consider that. What else should I know?",
        ]
        return random.choice(fallbacks)
```

---

## 6. Performance Considerations

### 6.1 Latency Budget

| Component | Target | Maximum |
|-----------|--------|---------|
| Audio capture + send | 100ms | 150ms |
| Deepgram STT | 200ms | 400ms |
| LLM response (first token) | 300ms | 500ms |
| TTS synthesis (first chunk) | 200ms | 300ms |
| **Total end-to-end** | **800ms** | **1350ms** |

### 6.2 Optimization Strategies

1. **Streaming everywhere**: Never wait for complete responses
2. **Sentence-level TTS**: Start speaking as soon as we have a sentence
3. **Parallel tool execution**: Run independent tools concurrently
4. **Connection pooling**: Reuse HTTP connections to external services
5. **Warm connections**: Keep Deepgram connection alive during session

### 6.3 Memory Management

```python
class SessionMemoryManager:
    MAX_CONVERSATION_TURNS = 20
    MAX_SESSION_AGE = timedelta(minutes=15)

    def cleanup_old_turns(self, session: NegotiationSession):
        """Keep conversation history manageable"""
        if len(session.conversation) > self.MAX_CONVERSATION_TURNS:
            # Keep first 2 turns (intro) and last 15
            session.conversation = (
                session.conversation[:2] +
                session.conversation[-15:]
            )

    async def cleanup_stale_sessions(self):
        """Remove abandoned sessions"""
        cutoff = datetime.utcnow() - self.MAX_SESSION_AGE
        stale = [
            sid for sid, session in sessions.items()
            if session.last_activity < cutoff
        ]
        for sid in stale:
            del sessions[sid]
```

---

## 7. Security Considerations

### 7.1 Input Validation

```python
class InputValidator:
    MAX_AUDIO_CHUNK_SIZE = 64 * 1024  # 64KB
    MAX_MESSAGE_SIZE = 1024           # 1KB for JSON messages

    def validate_audio_chunk(self, data: bytes) -> bool:
        """Validate incoming audio data"""
        if len(data) > self.MAX_AUDIO_CHUNK_SIZE:
            raise ValueError("Audio chunk too large")
        return True

    def validate_control_message(self, message: dict) -> bool:
        """Validate JSON control messages"""
        if len(json.dumps(message)) > self.MAX_MESSAGE_SIZE:
            raise ValueError("Message too large")
        if message.get("type") not in ALLOWED_MESSAGE_TYPES:
            raise ValueError("Invalid message type")
        return True
```

### 7.2 Rate Limiting

```python
class RateLimiter:
    def __init__(self):
        self.audio_rate = 10  # Max 10 chunks per second
        self.message_rate = 5  # Max 5 control messages per second

    async def check_audio_rate(self, session_id: str) -> bool:
        """Limit audio chunk frequency"""
        # Implement token bucket or sliding window
        pass
```

### 7.3 API Key Protection

- All API keys stored in environment variables
- Never logged or sent to client
- Rotated regularly in production

---

## 8. Monitoring & Observability

### 8.1 Key Metrics

```python
# Prometheus metrics
session_count = Gauge("salarydojo_active_sessions", "Active negotiation sessions")
turn_latency = Histogram("salarydojo_turn_latency_seconds", "Time from user speech end to Marcus response start")
tool_calls = Counter("salarydojo_tool_calls", "Tool invocations", ["tool_name"])
negotiation_outcomes = Counter("salarydojo_outcomes", "Negotiation outcomes", ["outcome"])
```

### 8.2 Logging Strategy

```python
# Structured logging for each turn
logger.info("turn_complete", extra={
    "session_id": session.session_id,
    "turn_number": len(session.conversation),
    "user_input_length": len(transcript),
    "tools_used": [t.name for t in tool_calls],
    "response_length": len(response),
    "latency_ms": latency,
    "patience": session.marcus.patience,
    "current_offer": session.marcus.current_offer,
})
```

---

## 9. Deployment Architecture

### 9.1 Hackathon Setup (Single Server)

```
┌─────────────────────────────────────────┐
│              Cloud VM                    │
│  ┌─────────────────────────────────┐    │
│  │          FastAPI                 │    │
│  │     (uvicorn, 4 workers)        │    │
│  └─────────────────────────────────┘    │
│                  │                       │
│                  ▼                       │
│  ┌─────────────────────────────────┐    │
│  │     In-Memory Session Store      │    │
│  │      (shared via manager)        │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 9.2 Production Setup (Future)

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │  (sticky sessions)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  API Server  │    │  API Server  │    │  API Server  │
│   (FastAPI)  │    │   (FastAPI)  │    │   (FastAPI)  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │     Redis       │
                    │ (Session Store) │
                    └─────────────────┘
```
