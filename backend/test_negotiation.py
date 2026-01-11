"""Simple test script for the negotiation engine."""

import asyncio
import logging
from models.session import NegotiationSession
from core.negotiation_engine import NegotiationEngine


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


async def main():
    """Test the negotiation engine."""
    print("=" * 80)
    print("NEGOTIATION ENGINE TEST")
    print("=" * 80)
    
    # Create session and engine
    session = NegotiationSession(session_id="test-123")
    engine = NegotiationEngine(session)
    
    print(f"\nInitial state:")
    print(f"  Patience: {session.marcus_state.patience}")
    print(f"  Emotion: {session.marcus_state.emotional_state.value}")
    
    # Test 1: Competing offer
    print("\n" + "=" * 80)
    print("TEST 1: Competing Offer")
    print("=" * 80)
    user_msg = "Hi Marcus, I have an offer from Google at $200k."
    print(f"\nUser: {user_msg}")
    
    response = await engine.process_user_message(user_msg)
    print(f"Marcus: {response}")
    print(f"\nState: Patience={session.marcus_state.patience}, Emotion={session.marcus_state.emotional_state.value}")
    
    # Test 2: Professional response
    print("\n" + "=" * 80)
    print("TEST 2: Professional Response")
    print("=" * 80)
    user_msg = "I have distributed systems experience from my Google internship. I was hoping for $140k."
    print(f"\nUser: {user_msg}")
    
    response = await engine.process_user_message(user_msg)
    print(f"Marcus: {response}")
    print(f"\nState: Patience={session.marcus_state.patience}, Emotion={session.marcus_state.emotional_state.value}, Offer={session.marcus_state.current_offer}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
