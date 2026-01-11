"""Tool executor for Marcus's autonomous decision-making.

This module implements the ToolExecutor class which handles execution of
Marcus's tool calls and modifies session state accordingly.
"""

from typing import Dict, Any, Optional
from models.session import NegotiationSession, NegotiationOutcome
from models.state import EmotionalState
from tools.market_data import get_market_rate, format_market_rate_response


class ToolExecutor:
    """Executes Marcus's tool calls and modifies session state in-place."""

    def __init__(self, session: NegotiationSession):
        """Initialize executor with a negotiation session.
        
        Args:
            session: The active NegotiationSession to modify
        """
        self.session = session
        self._handlers = {
            "check_market_rate": self.check_market_rate,
            "adjust_internal_state": self.adjust_internal_state,
            "make_offer": self.make_offer,
            "end_negotiation": self.end_negotiation,
        }

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Dictionary containing the tool's result
            
        Raises:
            ValueError: If tool_name is not recognized
        """
        handler = self._handlers.get(tool_name)
        if not handler:
            raise ValueError(
                f"Unknown tool: {tool_name}. "
                f"Available tools: {list(self._handlers.keys())}"
            )
        
        return await handler(**arguments)

    async def check_market_rate(
        self,
        role: str,
        company: str,
        level: str = "new_grad"
    ) -> Dict[str, Any]:
        """Look up market salary data for a specific role/company/level.
        
        Args:
            role: Job role (e.g. 'Software Engineer')
            company: Company name (e.g. 'Google', 'Meta')
            level: Seniority level ('new_grad', 'mid', 'senior')
            
        Returns:
            Dictionary with market rate information
        """
        salary_range = get_market_rate(role, company, level)
        
        if salary_range is None:
            return {
                "found": False,
                "message": f"No market data available for {role} at {company} ({level})",
                "role": role,
                "company": company,
                "level": level,
            }
        
        return {
            "found": True,
            "role": salary_range.role,
            "company": salary_range.company,
            "level": salary_range.level,
            "min": salary_range.min,
            "max": salary_range.max,
            "typical": salary_range.typical,
            "message": format_market_rate_response(salary_range),
        }

    async def adjust_internal_state(
        self,
        respect_delta: int = 0,
        emotional_state: Optional[str] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Adjust Marcus's internal state (respect and emotion).
        
        Args:
            respect_delta: Change in respect (±1 normally, ±2 for strong reactions)
            emotional_state: New emotional state (must be valid EmotionalState)
            reason: Internal note about why state is being adjusted
            
        Returns:
            Dictionary with old and new state values
        """
        old_respect = self.session.marcus_state.respect
        old_emotion = self.session.marcus_state.emotional_state
        
        # Update respect with bounds checking (0-4 scale)
        new_respect = old_respect + respect_delta
        new_respect = max(0, min(4, new_respect))  # Clamp to 0-4
        self.session.marcus_state.respect = new_respect
        
        # Update emotional state if provided
        if emotional_state is not None:
            # Validate it's a valid emotional state
            try:
                new_emotion = EmotionalState(emotional_state)
                self.session.marcus_state.emotional_state = new_emotion
            except ValueError:
                valid_states = [e.value for e in EmotionalState]
                raise ValueError(
                    f"Invalid emotional_state: {emotional_state}. "
                    f"Must be one of: {valid_states}"
                )
        
        return {
            "old_respect": old_respect,
            "new_respect": new_respect,
            "respect_delta": respect_delta,
            "old_emotional_state": old_emotion.value,
            "new_emotional_state": self.session.marcus_state.emotional_state.value,
            "reason": reason,
        }

    async def make_offer(
        self,
        amount: int,
        is_final: bool,
        components: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Make a salary offer to the candidate.
        
        Args:
            amount: Total compensation amount in USD
            is_final: Whether this is the final offer
            components: Optional breakdown (base, bonus, equity)
            
        Returns:
            Dictionary with offer details
            
        Raises:
            ValueError: If amount exceeds budget ceiling
        """
        budget_ceiling = self.session.marcus_state.budget_ceiling
        
        # Validate offer doesn't exceed budget
        if amount > budget_ceiling:
            raise ValueError(
                f"Offer amount ${amount:,} exceeds budget ceiling ${budget_ceiling:,}"
            )
        
        old_offer = self.session.marcus_state.current_offer
        self.session.marcus_state.current_offer = amount
        
        result = {
            "amount": amount,
            "is_final": is_final,
            "old_offer": old_offer,
            "budget_ceiling": budget_ceiling,
            "budget_remaining": budget_ceiling - amount,
        }
        
        if components:
            result["components"] = components
        
        return result

    async def end_negotiation(
        self,
        outcome: str,
        final_offer: Optional[int] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """End the negotiation session.
        
        Args:
            outcome: Outcome type ('accepted', 'rejected', 'hung_up')
            final_offer: Final offer amount if applicable
            reason: Explanation for ending
            
        Returns:
            Dictionary with negotiation end details
            
        Raises:
            ValueError: If outcome is not valid
        """
        # Validate outcome
        try:
            outcome_enum = NegotiationOutcome(outcome)
        except ValueError:
            valid_outcomes = [o.value for o in NegotiationOutcome]
            raise ValueError(
                f"Invalid outcome: {outcome}. "
                f"Must be one of: {valid_outcomes}"
            )
        
        # Note: We only have ACCEPTED and REJECTED in the enum
        # "hung_up" should map to REJECTED for now
        if outcome == "hung_up":
            outcome_enum = NegotiationOutcome.REJECTED
        
        self.session.outcome = outcome_enum
        
        # Update final offer if provided
        if final_offer is not None:
            self.session.marcus_state.current_offer = final_offer
        
        return {
            "outcome": outcome,
            "final_offer": final_offer or self.session.marcus_state.current_offer,
            "reason": reason,
            "final_respect": self.session.marcus_state.respect,
            "final_emotional_state": self.session.marcus_state.emotional_state.value,
        }
