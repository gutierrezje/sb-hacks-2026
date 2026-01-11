"""Negotiation engine with proper Gemini 3 function calling and thought signature handling."""

import logging
from pathlib import Path

from models.session import NegotiationSession
from core.llm_client import LLMClient
from tools.executor import ToolExecutor
from tools import get_tool_schemas


logger = logging.getLogger(__name__)


class NegotiationEngine:
    """Orchestrates Marcus's negotiation with proper function calling."""

    def __init__(self, session: NegotiationSession):
        """Initialize engine with a negotiation session.
        
        Args:
            session: The active NegotiationSession
        """
        self.session = session
        self.llm = LLMClient()
        self.executor = ToolExecutor(session)
        self.system_prompt = self._load_system_prompt()
        self.tools = self.llm.build_tools(get_tool_schemas())
        
        # Conversation history in Gemini-compatible format
        self.conversation: list[dict] = []

    def _load_system_prompt(self) -> str:
        """Load Marcus's system prompt from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "marcus.txt"
        return prompt_path.read_text()

    async def process_user_message(self, user_message: str) -> str:
        """Process user input and generate Marcus's response.

        Single-turn processing:
        1. Add user message to conversation
        2. Call LLM with tools
        3. If function call → execute → call LLM again for response
        4. Return text response

        This allows Marcus to call ONE tool per turn and build his case
        naturally over the conversation instead of burning cycles in a loop.

        Args:
            user_message: The candidate's message

        Returns:
            Marcus's text response
        """
        # Add user message to conversation
        self.conversation.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

        logger.info(f"Processing: {user_message[:100]}...")

        # First LLM call - may return tool call or text
        response = await self.llm.generate_with_tools(
            contents=self.conversation,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        # Check response type
        response_type, data = self.llm.get_response_type(response)

        if response_type == "function_calls":
            # Execute the function call(s) and get a final response
            await self._handle_function_calls(response, data)

            # Get final text response after tool execution
            logger.info("Getting final response after tool execution")
            response = await self.llm.generate_with_tools(
                contents=self.conversation,
                tools=self.tools,
                system_prompt=self.system_prompt,
            )
            response_type, data = self.llm.get_response_type(response)

        if response_type == "text":
            logger.info(f"Marcus: {data}")

            # Add to conversation history
            self.conversation.append({
                "role": "model",
                "parts": [{"text": data}]
            })

            return data

        # Unexpected response type
        logger.warning(f"Unexpected response type after tool execution: {response_type}")
        return "I'm having trouble processing that. Could you repeat?"

    async def _handle_function_calls(self, response, function_call_parts: list) -> None:
        """Execute function calls and add results to conversation.
        
        This properly preserves thought_signature for Gemini 3.
        
        Args:
            response: The full Gemini response (needed for thought_signature)
            function_call_parts: List of parts containing function calls
        """
        # First, add the model's response (with function calls AND thought_signature)
        # This is CRITICAL - we must preserve the exact response including thought_signature
        model_turn = self.llm.build_model_turn_from_response(response)
        self.conversation.append(model_turn)
        
        # Now execute each function and add responses
        for part in function_call_parts:
            call_info = self.llm.extract_function_call_info(part)
            tool_name = call_info["name"]
            arguments = call_info["arguments"]
            
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            
            try:
                result = await self.executor.execute(tool_name, arguments)
                logger.info(f"Tool result: {result}")
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                result = {"error": str(e)}
            
            # Add function response
            function_response = self.llm.build_function_response_turn(tool_name, result)
            self.conversation.append(function_response)
