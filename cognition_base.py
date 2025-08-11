"""
Cognition Base - lightweight, file-backed knowledge and pattern store
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ASI-GO.CognitionBase")


class CognitionBase:
    """
    Stores cross-run insights and reusable patterns/strategies.
    Backed by JSON files under a folder (default: ./cognition_base).
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getenv("COGNITION_BASE_DIR", "cognition_base")
        os.makedirs(self.base_dir, exist_ok=True)

        self.knowledge_path = os.path.join(self.base_dir, "knowledge.json")
        self.patterns_path = os.path.join(self.base_dir, "patterns.json")

        # In-memory structures
        self.knowledge: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []

        self._load()

    # ---------- File IO ----------
    def _load(self):
        # knowledge.json
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, "r", encoding="utf-8") as f:
                    self.knowledge = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load knowledge: {e}")
                self.knowledge = []
        else:
            self.knowledge = []

        # patterns.json
        if os.path.exists(self.patterns_path):
            try:
                with open(self.patterns_path, "r", encoding="utf-8") as f:
                    self.patterns = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
                self.patterns = []
        else:
            self.patterns = []

        logger.info("Knowledge base loaded")

    def _save(self):
        try:
            with open(self.knowledge_path, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
            with open(self.patterns_path, "w", encoding="utf-8") as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
            logger.info("Knowledge base saved successfully")
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    # ---------- Public API ----------
    def add_insight(self, insight: Dict[str, Any]) -> None:
        """
        Add an analysis insight. Expected keys:
          - goal: str
          - strategy: tuple|list|str
          - success: bool
          - key_learning: str
          - significance: float
          - metrics: dict
        """
        try:
            # Normalize strategy to a list of strings for storage
            strat = insight.get("strategy", [])
            if isinstance(strat, tuple):
                strat_list = list(strat)
            elif isinstance(strat, list):
                strat_list = [str(x) for x in strat]
            elif strat is None:
                strat_list = []
            else:
                strat_list = [str(strat)]

            record = dict(insight)
            record["strategy"] = strat_list
            self.knowledge.append(record)
            self._save()
        except Exception as e:
            logger.warning(f"Failed to add insight: {e}")

    def add_pattern(
        self,
        name: str,
        description: str,
        tags: Optional[List[str]] = None,
        template: Optional[str] = None,
    ) -> None:
        """
        Store a reusable pattern/strategy with optional template text.
        """
        try:
            entry = {
                "name": name,
                "description": description,
                "tags": tags or [],
                "template": template or "",
            }
            self.patterns.append(entry)
            self._save()
        except Exception as e:
            logger.warning(f"Failed to add pattern: {e}")

    def get_relevant_strategies(self, goal: str, max_items: int = 5) -> List[str]:
        """
        Simple keyword-based retrieval from patterns + knowledge strategies.
        (Left lightweight by design; you can swap for embeddings later.)
        """
        g = (goal or "").lower()
        pool: List[str] = []

        # From patterns
        for p in self.patterns:
            name = p.get("name", "")
            tags = p.get("tags", []) or []
            if any(t.lower() in g for t in [name] + tags):
                pool.append(name)

        # From past knowledge
        for k in self.knowledge:
            for s in k.get("strategy", []) or []:
                if isinstance(s, str) and (s.lower() in g or any(t in g for t in s.lower().split())):
                    pool.append(s)

        # Dedup preserve order
        seen = set()
        out = []
        for s in pool:
            if s not in seen:
                out.append(s)
                seen.add(s)
        return out[:max_items]

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Compact summary helping the Analyst or UI.
        """
        successes = sum(1 for k in self.knowledge if k.get("success"))
        failures = sum(1 for k in self.knowledge if not k.get("success"))
        strategies_flat: List[str] = []
        for k in self.knowledge:
            for s in k.get("strategy", []) or []:
                if isinstance(s, str):
                    strategies_flat.append(s)
        top_strats = {}
        for s in strategies_flat:
            top_strats[s] = top_strats.get(s, 0) + 1

        return {
            "total": len(self.knowledge),
            "successes": successes,
            "failures": failures,
            "top_strategies": sorted(top_strats.items(), key=lambda x: -x[1])[:5],
        }
