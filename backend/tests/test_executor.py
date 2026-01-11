"""Tests for the ToolExecutor class."""

import pytest
from models.session import NegotiationSession, NegotiationOutcome
from models.state import EmotionalState
from tools.executor import ToolExecutor


@pytest.fixture
def session():
    """Create a fresh negotiation session for testing."""
    return NegotiationSession(session_id="test-session-123")


@pytest.fixture
def executor(session):
    """Create a ToolExecutor with a test session."""
    return ToolExecutor(session)


class TestCheckMarketRate:
    """Tests for check_market_rate tool."""

    @pytest.mark.asyncio
    async def test_check_market_rate_google_new_grad(self, executor):
        """Test looking up Google new grad SWE salary."""
        result = await executor.check_market_rate(
            role="Software Engineer",
            company="Google",
            level="new_grad"
        )
        
        assert result["found"] is True
        assert result["company"] == "Google"
        assert result["role"] == "Software Engineer"
        assert result["level"] == "new_grad"
        assert result["min"] == 120000
        assert result["max"] == 150000
        assert result["typical"] == 135000
        assert "message" in result

    @pytest.mark.asyncio
    async def test_check_market_rate_meta_mid(self, executor):
        """Test looking up Meta mid-level SWE salary."""
        result = await executor.check_market_rate(
            role="Software Engineer",
            company="Meta",
            level="mid"
        )
        
        assert result["found"] is True
        assert result["typical"] == 195000

    @pytest.mark.asyncio
    async def test_check_market_rate_unknown_company(self, executor):
        """Test looking up salary for unknown company."""
        result = await executor.check_market_rate(
            role="Software Engineer",
            company="UnknownStartup",
            level="new_grad"
        )
        
        assert result["found"] is False
        assert "No market data available" in result["message"]

    @pytest.mark.asyncio
    async def test_check_market_rate_case_insensitive(self, executor):
        """Test that company lookup is case-insensitive."""
        result = await executor.check_market_rate(
            role="Software Engineer",
            company="google",  # lowercase
            level="new_grad"
        )
        
        assert result["found"] is True
        assert result["company"] == "Google"


class TestAdjustInternalState:
    """Tests for adjust_internal_state tool."""

    @pytest.mark.asyncio
    async def test_adjust_respect_decrease(self, executor, session):
        """Test decreasing respect."""
        initial_respect = session.marcus_state.respect
        
        result = await executor.adjust_internal_state(
            respect_delta=-1,
            emotional_state="skeptical",
            reason="Candidate made unrealistic claim"
        )
        
        assert result["old_respect"] == initial_respect
        assert result["new_respect"] == initial_respect - 1
        assert result["respect_delta"] == -1
        assert session.marcus_state.respect == 1

    @pytest.mark.asyncio
    async def test_adjust_respect_increase(self, executor, session):
        """Test increasing respect."""
        session.marcus_state.respect = 1
        
        result = await executor.adjust_internal_state(
            respect_delta=1,
            emotional_state="impressed",
            reason="Candidate provided good data"
        )
        
        assert result["new_respect"] == 2
        assert session.marcus_state.respect == 2

    @pytest.mark.asyncio
    async def test_adjust_respect_lower_bound(self, executor, session):
        """Test that respect can't go below 0."""
        session.marcus_state.respect = 1
        
        result = await executor.adjust_internal_state(
            respect_delta=-5,  # Would go to -4 without clamping
            emotional_state="done",
            reason="Lost all respect"
        )
        
        assert result["new_respect"] == 0
        assert session.marcus_state.respect == 0

    @pytest.mark.asyncio
    async def test_adjust_respect_upper_bound(self, executor, session):
        """Test that respect can't go above 4."""
        session.marcus_state.respect = 3
        
        result = await executor.adjust_internal_state(
            respect_delta=5,  # Would go to 8 without clamping
            emotional_state="very_impressed",
            reason="Excellent negotiation"
        )
        
        assert result["new_respect"] == 4
        assert session.marcus_state.respect == 4

    @pytest.mark.asyncio
    async def test_adjust_emotional_state(self, executor, session):
        """Test changing emotional state."""
        assert session.marcus_state.emotional_state == EmotionalState.NEUTRAL
        
        result = await executor.adjust_internal_state(
            respect_delta=0,
            emotional_state="stressed",
            reason="Candidate being aggressive"
        )
        
        assert result["old_emotional_state"] == "neutral"
        assert result["new_emotional_state"] == "stressed"
        assert session.marcus_state.emotional_state == EmotionalState.STRESSED

    @pytest.mark.asyncio
    async def test_adjust_invalid_emotional_state(self, executor):
        """Test that invalid emotional state raises error."""
        with pytest.raises(ValueError, match="Invalid emotional_state"):
            await executor.adjust_internal_state(
                respect_delta=0,
                emotional_state="happy",  # Not a valid state
                reason="Test"
            )

    @pytest.mark.asyncio
    async def test_adjust_respect_only(self, executor, session):
        """Test adjusting respect without changing emotion."""
        initial_emotion = session.marcus_state.emotional_state
        
        result = await executor.adjust_internal_state(
            respect_delta=-1,
            reason="Minor annoyance"
        )
        
        assert result["new_respect"] == 1
        assert session.marcus_state.emotional_state == initial_emotion


class TestMakeOffer:
    """Tests for make_offer tool."""

    @pytest.mark.asyncio
    async def test_make_offer_within_budget(self, executor, session):
        """Test making an offer within budget ceiling."""
        result = await executor.make_offer(
            amount=125000,
            is_final=False
        )
        
        assert result["amount"] == 125000
        assert result["is_final"] is False
        assert result["old_offer"] is None
        assert result["budget_ceiling"] == 150000
        assert result["budget_remaining"] == 25000
        assert session.marcus_state.current_offer == 125000

    @pytest.mark.asyncio
    async def test_make_offer_at_ceiling(self, executor, session):
        """Test making an offer at the budget ceiling."""
        result = await executor.make_offer(
            amount=150000,
            is_final=True
        )
        
        assert result["amount"] == 150000
        assert result["budget_remaining"] == 0
        assert session.marcus_state.current_offer == 150000

    @pytest.mark.asyncio
    async def test_make_offer_exceeds_budget(self, executor):
        """Test that offer exceeding budget raises error."""
        with pytest.raises(ValueError, match="exceeds budget ceiling"):
            await executor.make_offer(
                amount=160000,  # Over the $150k ceiling
                is_final=True
            )

    @pytest.mark.asyncio
    async def test_make_offer_with_components(self, executor, session):
        """Test making an offer with component breakdown."""
        result = await executor.make_offer(
            amount=140000,
            is_final=False,
            components={
                "base": 120000,
                "bonus": 10000,
                "equity": 10000
            }
        )
        
        assert result["amount"] == 140000
        assert result["components"]["base"] == 120000
        assert result["components"]["bonus"] == 10000
        assert result["components"]["equity"] == 10000

    @pytest.mark.asyncio
    async def test_make_offer_updates_previous(self, executor, session):
        """Test that new offer updates previous offer."""
        # First offer
        await executor.make_offer(amount=115000, is_final=False)
        assert session.marcus_state.current_offer == 115000
        
        # Second offer
        result = await executor.make_offer(amount=130000, is_final=False)
        
        assert result["old_offer"] == 115000
        assert result["amount"] == 130000
        assert session.marcus_state.current_offer == 130000


class TestEndNegotiation:
    """Tests for end_negotiation tool."""

    @pytest.mark.asyncio
    async def test_end_negotiation_accepted(self, executor, session):
        """Test ending negotiation with accepted outcome."""
        session.marcus_state.current_offer = 140000
        
        result = await executor.end_negotiation(
            outcome="accepted",
            final_offer=140000,
            reason="Candidate accepted $140k offer"
        )
        
        assert result["outcome"] == "accepted"
        assert result["final_offer"] == 140000
        assert result["reason"] == "Candidate accepted $140k offer"
        assert session.outcome == NegotiationOutcome.ACCEPTED

    @pytest.mark.asyncio
    async def test_end_negotiation_rejected(self, executor, session):
        """Test ending negotiation with rejected outcome."""
        result = await executor.end_negotiation(
            outcome="rejected",
            reason="Candidate expectations too high"
        )
        
        assert result["outcome"] == "rejected"
        assert session.outcome == NegotiationOutcome.REJECTED

    @pytest.mark.asyncio
    async def test_end_negotiation_hung_up(self, executor, session):
        """Test ending negotiation with hung_up outcome."""
        session.marcus_state.respect = 0
        
        result = await executor.end_negotiation(
            outcome="hung_up",
            reason="Lost respect with rambling"
        )
        
        assert result["outcome"] == "hung_up"
        assert result["final_respect"] == 0
        # hung_up maps to REJECTED in the enum
        assert session.outcome == NegotiationOutcome.REJECTED

    @pytest.mark.asyncio
    async def test_end_negotiation_invalid_outcome(self, executor):
        """Test that invalid outcome raises error."""
        with pytest.raises(ValueError, match="Invalid outcome"):
            await executor.end_negotiation(
                outcome="maybe",  # Not a valid outcome
                reason="Test"
            )

    @pytest.mark.asyncio
    async def test_end_negotiation_includes_final_state(self, executor, session):
        """Test that end result includes final emotional state."""
        session.marcus_state.emotional_state = EmotionalState.STRESSED
        session.marcus_state.respect = 1
        
        result = await executor.end_negotiation(
            outcome="accepted",
            final_offer=145000,
            reason="Close call but accepted"
        )
        
        assert result["final_respect"] == 1
        assert result["final_emotional_state"] == "stressed"


class TestExecuteDispatch:
    """Tests for the execute() dispatcher method."""

    @pytest.mark.asyncio
    async def test_execute_dispatches_correctly(self, executor):
        """Test that execute() routes to correct handler."""
        result = await executor.execute(
            "check_market_rate",
            {
                "role": "Software Engineer",
                "company": "Google",
                "level": "new_grad"
            }
        )
        
        assert result["found"] is True
        assert result["company"] == "Google"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, executor):
        """Test that unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await executor.execute(
                "unknown_tool",
                {}
            )
