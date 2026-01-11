"""Test LLM client."""

import pytest
from core.llm_client import LLMClient
from tools import get_tool_schemas


@pytest.mark.asyncio
async def test_llm_with_tools():
    """Test LLM with tools (current API)."""
    llm = LLMClient()
    
    # Build tools
    tool_schemas = get_tool_schemas()
    tools = llm.build_tools(tool_schemas)
    
    # Create a simple conversation
    contents = [
        {"role": "user", "parts": [{"text": "Hello, I'm interested in the software engineer position."}]}
    ]
    
    response = await llm.generate_with_tools(
        contents=contents,
        tools=tools,
        system_prompt="You are Marcus, a recruiter. Be brief.",
    )
    
    assert response is not None
    # Check that we got a response with candidates
    assert hasattr(response, 'candidates')
    assert len(response.candidates) > 0


@pytest.mark.asyncio
async def test_llm_response_type():
    """Test LLM response type detection."""
    llm = LLMClient()
    
    tool_schemas = get_tool_schemas()
    tools = llm.build_tools(tool_schemas)
    
    contents = [
        {"role": "user", "parts": [{"text": "What's 2+2?"}]}
    ]
    
    response = await llm.generate_with_tools(
        contents=contents,
        tools=tools,
        system_prompt="You are a helpful assistant.",
    )
    
    response_type, data = llm.get_response_type(response)
    
    # Should get either text or function_calls
    assert response_type in ["text", "function_calls", "empty"]
