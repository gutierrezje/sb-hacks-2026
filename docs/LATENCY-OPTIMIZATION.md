# Latency Optimization Plan

## Overview

This document outlines the strategy for measuring and optimizing latency in the salary negotiation conversational AI pipeline. The pipeline consists of:

1. **STT (Speech-to-Text)**: Deepgram Flux v2
2. **LLM (Language Model)**: Gemini 3.0 Flash
3. **TTS (Text-to-Speech)**: Cartesia
4. **Network**: WebSocket communication

## Current Baseline Configuration

### Deepgram Configuration
- Model: `flux-general-en`
- EOT Threshold: `0.7` (default)
- EOT Timeout: `5000ms` (default)
- No eager end-of-turn enabled

### LLM Configuration
- Model: `gemini-3-flash-preview`
- Temperature: `0.7`
- Max Output Tokens: `500`
- Non-streaming mode

### Architecture
- Sequential pipeline: STT → LLM → TTS → Send
- No parallel processing
- No chunking or streaming

## Measurement Infrastructure

### Timing Module (`backend/core/timing.py`)

The timing module provides instrumentation for measuring latency:

```python
from core.timing import TimingManager, time_block

# Create timing manager for session
timing_manager = TimingManager()

# Track a turn
metrics = timing_manager.create_metrics(
    session_id=session_id,
    turn_id=turn_id,
    transcript_length=len(text),
)

# Time individual operations
async with time_block(metrics, "llm_generation"):
    response = await llm.generate_response(...)

# Log summary
metrics.log_summary()
```

### Measured Events

The WebSocket handler currently tracks:

1. **`llm_generation`**: Time to generate LLM response
2. **`tts_synthesis`**: Time to synthesize speech
3. **`network_send`**: Time to send audio bytes over WebSocket
4. **`pipeline_total`**: End-to-end time for the turn

### Metadata Collected

- `transcript_length`: Characters in user input
- `response_length`: Characters in LLM output
- `audio_bytes`: Size of TTS output

## Latency Targets

Based on conversational AI best practices:

| Metric | Target | Stretch Goal |
|--------|--------|--------------|
| Time to First Audio | < 1000ms | < 500ms |
| Total Response Time | < 2000ms | < 1500ms |
| LLM Generation | < 800ms | < 400ms |
| TTS Synthesis | < 500ms | < 200ms |

## Optimization Roadmap

### Phase 1: Measure Baseline (Current)

**Status**: ✅ Implemented

- [x] Add timing instrumentation
- [x] Log all pipeline stages
- [x] Collect metadata on response sizes

**Next Steps**:
1. Run real conversations with the UI
2. Collect 20+ turns of timing data
3. Identify bottlenecks (which stage is slowest)
4. Analyze variance (are times consistent or spiky?)

### Phase 2: Quick Wins

**Implement after baseline measurement**

#### A. Deepgram Eager End-of-Turn
- Enable `eager_eot_threshold` to start LLM generation early
- Handle `EagerEndOfTurn` and `TurnResumed` events
- Trade-off: Reduced latency vs. false starts

**Configuration to test**:
```python
eager_eot_threshold="0.5"  # Start LLM at 50% confidence
eot_threshold="0.7"        # Finalize at 70%
eot_timeout_ms="2000"      # Faster timeout for responsive feel
```

#### B. LLM Streaming
- Switch from `generate_response` to `stream_response`
- Start TTS as soon as first sentence is complete
- Reduces time-to-first-audio significantly

#### C. Parallel TTS Chunks
- Split LLM response into sentences
- Synthesize and send sentences in parallel
- Pipeline multiple TTS requests

### Phase 3: Advanced Optimizations

**Implement if Phase 2 doesn't hit targets**

#### A. Model Optimizations
- Test faster LLM models (e.g., Gemini Flash 1.5 vs 3.0)
- Reduce `max_output_tokens` (shorter responses = faster)
- Fine-tune temperature for faster generation

#### B. TTS Optimizations
- Pre-generate common phrases
- Use streaming TTS if Cartesia supports it
- Adjust quality settings for speed

#### C. Network Optimizations
- Send audio chunks as they're generated
- Use binary compression
- WebSocket frame size tuning

#### D. Speculative Execution
- Pre-generate likely responses based on transcript
- Cancel if user continues speaking
- High complexity, moderate gain

### Phase 4: Infrastructure

**Long-term improvements**

- Add metrics export (Prometheus/Grafana)
- Percentile analysis (p50, p95, p99)
- A/B testing framework for configurations
- Session replay for debugging slow turns

## How to Use This Plan

### 1. Baseline Measurement

Run the conversational UI and examine logs:

```bash
# Look for timing summaries in logs
=== Timing Summary [session_id:turn_1] ===
  llm_generation: 1234.56ms
  tts_synthesis: 567.89ms
  network_send: 12.34ms
  TOTAL: 1814.79ms
  Metadata: {'transcript_length': 42, 'response_length': 156, 'audio_bytes': 89472}
```

### 2. Identify Bottlenecks

Answer these questions:
- Which stage takes the longest?
- Is latency consistent or variable?
- Does response length correlate with latency?

### 3. Implement Optimizations

Based on bottlenecks:
- If **LLM is slow**: Enable streaming (Phase 2B)
- If **TTS is slow**: Parallel synthesis (Phase 2C)
- If **STT EOT is slow**: Enable eager EOT (Phase 2A)

### 4. Measure Impact

After each optimization:
- Collect new timing data
- Compare to baseline
- Document trade-offs (accuracy vs speed)

## Success Criteria

The optimization effort is successful when:

1. **Measurements exist**: We have 20+ turns of baseline data
2. **Bottlenecks identified**: We know which stage is slowest
3. **Target met**: Total response time < 2000ms
4. **Quality maintained**: No significant degradation in conversation quality

## Notes

- **Don't optimize prematurely**: Measure first, then optimize
- **One change at a time**: Test optimizations individually
- **User feedback matters**: Speed is useless if quality suffers
- **Document everything**: Track what works and what doesn't

## References

- [Deepgram Flux Configuration](https://developers.deepgram.com/docs/flux/configuration)
- [Gemini API Streaming](https://ai.google.dev/gemini-api/docs/text-generation#stream-text)
- [Conversational AI Latency Best Practices](https://www.twilio.com/blog/optimizing-latency-voice-ai)
