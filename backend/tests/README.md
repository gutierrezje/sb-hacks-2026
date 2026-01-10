# Backend Tests

This directory contains integration and unit tests for The Salary Dojo backend.

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_deepgram.py -v
```

Run specific test:
```bash
pytest tests/test_deepgram.py::TestSpeechToText::test_prerecorded_transcription -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

## Test Structure

- `test_deepgram.py` - Deepgram API integration tests
- `conftest.py` - Shared pytest fixtures and configuration

## Requirements

Tests require:
- Valid `DEEPGRAM_API_KEY` in `.env` file
- Network connectivity to Deepgram API
