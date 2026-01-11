"""Tool definitions for Marcus's autonomous decision-making.

These tools allow Marcus to:
1. Fact-check market data
2. Adjust internal emotional state
3. Make salary offers
4. End the negotiation
"""

from typing import List, Dict, Any


# Tool schema format compatible with Gemini function calling
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "check_market_rate",
        "description": (
            "Look up market salary data for a specific role at a company. "
            "Use this when the candidate mentions competing offers or asks about market rates. "
            "This helps you validate claims and make informed counter-offers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Job role (e.g. 'Software Engineer', 'Product Manager', 'Data Scientist')",
                },
                "company": {
                    "type": "string",
                    "description": "Company name (e.g. 'Google', 'Meta', 'Amazon', 'Startup')",
                },
                "level": {
                    "type": "string",
                    "description": "Seniority level",
                    "enum": ["new_grad", "mid", "senior"],
                },
            },
            "required": ["role", "company"],
        },
    },
    {
        "name": "adjust_internal_state",
        "description": (
            "Update your internal emotional state based on the conversation. "
            "Call this when something significant happens to track how the negotiation affects you. "
            "This is PRIVATE - the candidate cannot see this, but it affects your behavior and the emoji avatar shown to them."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "respect_delta": {
                    "type": "number",
                    "description": (
                        "Change in respect (±1 normally, ±2 for strong reactions). "
                        "Positive for good arguments (data-driven, professional) - you gain respect for them. "
                        "Negative for poor behavior (rambling, unrealistic demands) - you lose respect for them. "
                        "Respect is 0-4 scale: starts at 2 (neutral), ends negotiation at 0."
                    ),
                },
                "emotional_state": {
                    "type": "string",
                    "enum": [
                        "neutral",
                        "impressed",
                        "very_impressed",
                        "skeptical",
                        "stressed",
                        "done",
                    ],
                    "description": (
                        "Your current emotional state (maps to respect level): "
                        "4=very_impressed (exceptional), 3=impressed (good arguments), 2=neutral/skeptical (routine), "
                        "1=stressed (problematic), 0=done (exhausted)"
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": "Brief internal note about why you're adjusting state (for your own reasoning)",
                },
            },
            "required": ["emotional_state", "reason"],
        },
    },
    {
        "name": "make_offer",
        "description": (
            "Make a salary offer or counter-offer to the candidate. "
            "Only call this when you're ready to put a specific number on the table. "
            "Start conservative and move up based on their justification."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Total compensation amount in USD (base + bonus + equity value)",
                },
                "is_final": {
                    "type": "boolean",
                    "description": (
                        "Whether this is your final offer (true) or there's room to negotiate (false). "
                        "Set to true when you're at your budget ceiling or patience is low."
                    ),
                },
                "components": {
                    "type": "object",
                    "description": "Optional breakdown of compensation components",
                    "properties": {
                        "base": {
                            "type": "number",
                            "description": "Base salary component",
                        },
                        "bonus": {
                            "type": "number",
                            "description": "Signing bonus or annual bonus",
                        },
                        "equity": {
                            "type": "number",
                            "description": "Equity value (RSU/options)",
                        },
                    },
                },
            },
            "required": ["amount", "is_final"],
        },
    },
    {
        "name": "end_negotiation",
        "description": (
            "End the negotiation session. Call this when: "
            "(1) you and candidate agree on terms, "
            "(2) you're politely rejecting them, or "
            "(3) you're hanging up due to frustration/lost patience."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "enum": ["accepted", "rejected", "hung_up"],
                    "description": (
                        "accepted: deal reached and candidate accepted your offer, "
                        "rejected: polite decline (candidate not a fit), "
                        "hung_up: frustrated ending (lost patience)"
                    ),
                },
                "final_offer": {
                    "type": "number",
                    "description": "The final offer amount in USD, if any",
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Brief explanation for ending "
                        "(e.g. 'Candidate accepted $145k', 'Unrealistic expectations', 'Lost patience with rambling')"
                    ),
                },
            },
            "required": ["outcome", "reason"],
        },
    },
]


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Return all tool schemas for LLM function calling."""
    return TOOL_SCHEMAS


def get_tool_names() -> List[str]:
    """Return list of available tool names."""
    return [tool["name"] for tool in TOOL_SCHEMAS]
