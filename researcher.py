"""
Researcher - Generates solution proposals
"""
import logging
import random
from typing import Dict, Any, List, Optional

from llm_interface import LLMInterface
from cognition_base import CognitionBase

logger = logging.getLogger("ASI-GO.Researcher")


def _compose_strategies(strategies: List[str]) -> List[str]:
    """Combine/curate strategies for the next attempt."""
    if not strategies:
        return []
    # Keep order but pick a small subset; prefer diversity
    uniq = []
    seen = set()
    for s in strategies:
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    k = min(len(uniq), 3)
    return uniq[:k]


def _mutate_hints(goal: str) -> List[str]:
    """Light mutation hints to nudge variety without breaking constraints."""
    hints = []
    gl = goal.lower()
    if "prime" in gl:
        hints.append("Prefer Sieve of Eratosthenes for N up to a few thousand")
        hints.append("Print the final list with print(primes) and nothing else")
        hints.append("Avoid off-by-one errors; ensure exactly N primes")
    else:
        hints.append("Return only the final answer in machine-readable form")
    # Dedup and sample a few
    uniq = []
    seen = set()
    for h in hints:
        if h not in seen:
            uniq.append(h)
            seen.add(h)
    return uniq[:3]


class Researcher:
    """Generates solution proposals based on the goal and known strategies."""

    def __init__(self, llm: LLMInterface, cognition_base: CognitionBase):
        self.llm = llm
        self.cognition_base = cognition_base
        self.proposals: List[Dict[str, Any]] = []

    def _build_prompt(self, goal: str, strategies: List[str]) -> str:
        composed = _compose_strategies(strategies)
        mutations = _mutate_hints(goal)

        # Strict output contract + stdlib only
        contract = (
            "You are writing a short Python program that solves the user's goal.\n"
            "REQUIREMENTS:\n"
            "1) Use ONLY the Python standard library.\n"
            "2) Return ONLY a Python fenced code block (```python ... ```). Do not include any prose.\n"
            "3) When run, the program must print ONLY the final answer in a single line or a Python list via print(...).\n"
            "4) No input() calls. No external packages. No network access.\n"
        )

        strategy_note = ""
        if composed:
            strategy_note = "Known helpful strategies: " + ", ".join(composed) + ".\n"

        mutate_note = ""
        if mutations:
            mutate_note = "Hints: " + " | ".join(mutations) + "\n"

        return (
            contract
            + strategy_note
            + mutate_note
            + "\nGOAL:\n"
            + goal.strip()
        )

    def propose_solution(self, goal: str, previous_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Produce a solution proposal (code) with strict output formatting.
        """
        logger.info(f"Proposing solution for goal: {goal}")

        # Retrieve strategies from cognition base
        strategies = self.cognition_base.get_relevant_strategies(goal, max_items=5)
        prompt = self._build_prompt(goal, strategies)

        if previous_feedback:
            system = (
                "Improve the prior attempt using the feedback. "
                "Maintain the output contract and standard-library-only rule."
            )
            prompt = previous_feedback.strip() + "\n\n" + prompt
        else:
            system = (
                "Follow the output contract strictly. "
                "Return only a Python code block that can be run as-is."
            )

        # Query LLM
        code_text = self.llm.query(prompt=prompt, system=system, max_tokens=800)

        proposal = {
            "goal": goal,
            "solution": code_text,
            "strategies_used": strategies or [],
            "notes": previous_feedback or "",
        }
        self.proposals.append(proposal)
        logger.info("Solution proposal generated successfully")
        return proposal
