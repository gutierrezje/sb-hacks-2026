"""LLM client for Gemini 3.0 Flash."""

import logging
from google import genai
from google.genai.types import GenerateContentConfig

from config import get_settings


logger = logging.getLogger(__name__)


class LLMClient:
    """Simple LLM client using Gemini 3.0 Flash."""

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-3-flash-preview"

    async def generate_response(self, user_message: str, system_prompt: str | None = None) -> str:
        """Generate a response from the LLM.
        
        Args:
            user_message: The user's message
            system_prompt: Optional system prompt for context
            
        Returns:
            The LLM's response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "user", "parts": [{"text": system_prompt}]})
            messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        
        messages.append({"role": "user", "parts": [{"text": user_message}]})
        
        config = GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=500,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=messages,
            config=config,
        )
        
        return response.text
