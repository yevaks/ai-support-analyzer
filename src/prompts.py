"""Prompt templates for generation and analysis."""

from __future__ import annotations

import random

# A curated pool of realistic support scenarios to sample from.
SCENARIO_POOL = [
    "Customer cannot reset their account password after multiple attempts.",
    "Customer was charged twice for the same subscription renewal.",
    "Customer's order was delivered to the wrong address.",
    "Customer wants to cancel their subscription before the next billing cycle.",
    "Customer's promotional discount code is not being applied at checkout.",
    "Customer received a damaged product and wants a replacement.",
    "Customer cannot access premium features after a successful payment.",
    "Customer's account was locked out after too many failed login attempts.",
    "Customer wants to change the email address associated with their account.",
    "Customer reports that an item is missing from their delivered package.",
    "Customer received the wrong item in their order.",
    "Customer is unable to download the product they purchased.",
    "Customer is requesting a refund for a purchase made over 30 days ago.",
    "Customer's scheduled delivery is significantly delayed with no updates.",
    "Customer wants to transfer their subscription to a different email.",
    "Customer is experiencing intermittent crashes in the mobile application.",
    "Customer was auto-renewed despite attempting to cancel their subscription.",
    "Customer cannot connect their third-party app to the platform via API.",
    "Customer's gift card balance is showing as zero after a recent purchase.",
    "Customer wants to upgrade their plan but the upgrade button is not working.",
]


def pick_scenario(rng: random.Random) -> str:
    """Pick a random scenario using the provided RNG instance."""
    return rng.choice(SCENARIO_POOL)


def generate_dialog_prompt(scenario: str) -> str:
    """Prompt for generating a single customer support dialog."""
    return (
        f"You are simulating a customer support conversation.\n\n"
        f"Scenario: {scenario}\n\n"
        "Generate a realistic customer support dialog between a 'customer' and an 'agent'.\n"
        "Requirements:\n"
        "- 4 to 8 message exchanges total (alternating roles)\n"
        "- Start with the customer describing the problem\n"
        "- The agent should be professional, empathetic, and attempt to resolve the issue\n"
        "- The conversation should reach a natural conclusion (resolved, pending follow-up, or escalated)\n"
        "- Provide a short 'scenario' field (5–10 words) summarising the issue\n"
        "- Output must conform to the provided JSON schema EXACTLY\n"
    )


def analyze_dialog_prompt(dialog_text: str) -> str:
    """Prompt for analysing a single dialog and extracting structured insights."""
    return (
        "You are a customer support quality analyst.\n\n"
        "Analyse the following customer support dialog and return a structured JSON result.\n\n"
        f"Dialog:\n{dialog_text}\n\n"
        "Instructions:\n"
        "- intent: a concise phrase (≤10 words) describing what the customer wanted\n"
        "- satisfaction: one of 'satisfied', 'neutral', or 'unsatisfied' based on the customer's final tone\n"
        "- quality_score: integer 1–5 rating the agent's performance (5 = excellent)\n"
        "- mistake_codes: a list of short error codes for any agent mistakes observed, or null if none\n"
        "  Common codes: WRONG_INFO, NO_EMPATHY, UNRESOLVED, POLICY_VIOLATION, SLOW_RESPONSE\n"
        "- Do NOT include dialog_id in your output; it will be added programmatically\n"
        "- Output must conform to the provided JSON schema EXACTLY\n"
    )


def format_dialog_for_analysis(dialog: dict) -> str:
    """Convert a dialog dict to a plain-text representation for the LLM."""
    lines = [f"Scenario: {dialog['scenario']}", ""]
    for msg in dialog["messages"]:
        role = msg["role"].capitalize()
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)
