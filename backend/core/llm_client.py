"""LLM client with proper Gemini 3 function calling and thought signature handling.

IMPORTANT: Gemini 3 Thought Signature Gotcha
============================================
Gemini 3 requires a `thought_signature` to be preserved when sending function
results back to the model. Without it, you get:

    400 INVALID_ARGUMENT: "Function call is missing a thought_signature"

The documentation (https://ai.google.dev/gemini-api/docs/thought-signatures)
does NOT clearly explain that:

1. `thought_signature` is on the PART level, not the FunctionCall level:
   - WRONG: response.candidates[0].content.parts[0].function_call.thought_signature
   - RIGHT: response.candidates[0].content.parts[0].thought_signature

2. You must preserve the raw bytes and include them in subsequent requests

3. The field exists on `Part` objects that CONTAIN function calls, not on
   the `FunctionCall` object itself

This was discovered by runtime introspection of the response objects.
The SDK's automatic function calling feature should handle this, but
it has issues with async APIs, so we handle it manually here.
"""

import logging
from typing import Any
from google import genai
from google.genai.types import GenerateContentConfig, Tool, FunctionDeclaration

from config import get_settings


logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client using Gemini 3.0 Flash with function calling support."""

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-3-flash-preview"

    def build_tools(self, tool_schemas: list[dict[str, Any]]) -> list[Tool]:
        """Convert tool schemas to Gemini Tool objects."""
        function_declarations = []
        for schema in tool_schemas:
            function_declarations.append(
                FunctionDeclaration(
                    name=schema["name"],
                    description=schema["description"],
                    parameters=schema["parameters"],
                )
            )
        return [Tool(function_declarations=function_declarations)]

    async def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        tools: list[Tool],
        system_prompt: str,
    ) -> Any:
        """Generate content with tools optimized for low latency."""
        # Limit conversation history to last 10 turns to reduce prompt size
        # Keep first turn (greeting) and last 9 for context
        limited_contents = contents
        if len(contents) > 20:  # ~10 turns (user + model pairs)
            limited_contents = [contents[0]] + contents[-18:]

        config = GenerateContentConfig(
            temperature=0.5,         # Lower for faster, more deterministic responses
            max_output_tokens=150,   # Marcus keeps responses brief (1-2 sentences)
            system_instruction=system_prompt,
            tools=tools,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=limited_contents,
            config=config,
        )

        return response

    def get_response_type(self, response: Any) -> tuple[str, Any]:
        """Determine if response contains text or function calls."""
        if not response.candidates or not response.candidates[0].content.parts:
            return ("empty", None)
        
        parts = response.candidates[0].content.parts
        
        # Check for function calls
        function_calls = []
        for part in parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part)
        
        if function_calls:
            return ("function_calls", function_calls)
        
        # Check for text
        for part in parts:
            if hasattr(part, 'text') and part.text:
                return ("text", part.text)
        
        return ("empty", None)

    def build_model_turn_from_response(self, response: Any) -> dict[str, Any]:
        """Build a model turn from response, preserving thought_signature on Parts.
        
        CRITICAL: thought_signature is on the Part level, not FunctionCall level!
        """
        content = response.candidates[0].content
        
        parts = []
        for part in content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                part_dict = {
                    "function_call": {
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }
                }
                # CRITICAL: thought_signature is on the Part, not FunctionCall
                if hasattr(part, 'thought_signature') and part.thought_signature:
                    part_dict["thought_signature"] = part.thought_signature
                    logger.info(f"Preserved thought_signature for {fc.name}")
                parts.append(part_dict)
            elif hasattr(part, 'text') and part.text:
                parts.append({"text": part.text})
        
        return {"role": "model", "parts": parts}

    def build_function_response_turn(
        self,
        function_name: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a function response turn."""
        return {
            "role": "user",  # Function responses use "user" role in Gemini
            "parts": [{
                "function_response": {
                    "name": function_name,
                    "response": result,
                }
            }]
        }

    def extract_function_call_info(self, part: Any) -> dict[str, Any]:
        """Extract function call information from a part."""
        fc = part.function_call
        return {
            "name": fc.name,
            "arguments": dict(fc.args) if fc.args else {},
        }
