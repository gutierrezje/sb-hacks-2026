"""Test LLM client."""

import pytest
from core.llm_client import LLMClient


@pytest.mark.asyncio
async def test_llm_basic_response():
    """Test basic LLM response generation."""
    llm = LLMClient()
    
    response = await llm.generate_response(
        user_message="Hello, I'm interested in the software engineer position.",
        system_prompt="You are Marcus, a recruiter. Be brief.",
    )
    
    assert response is not None
    assert len(response) > 0
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_llm_without_system_prompt():
    """Test LLM response without system prompt."""
    llm = LLMClient()
    
    response = await llm.generate_response(
        user_message="What's 2+2?",
    )
    
    assert response is not None
    assert len(response) > 0
