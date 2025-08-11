"""
Analyst - Analyzes results and extracts insights
"""
import logging
import re
from collections import Counter
from typing import Dict, Any, List, Optional

from llm_interface import LLMInterface
from cognition_base import CognitionBase

logger = logging.getLogger("ASI-GO.Analyst")


class Analyst:
    """Analyzes execution results and provides insights"""

    def __init__(self, llm: LLMInterface, cognition_base: CognitionBase):
        self.llm = llm
        self.cognition_base = cognition_base
        self.analyses: List[Dict[str, Any]] = []

    # ----------------------------
    # Public API used by main.py
    # ----------------------------
    def analyze_results(
        self,
        proposal: Dict[str, Any],
        test_result: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Summarize the run, extract patterns or diagnoses, and feed insights back to the Cognition Base.
        """
        success = bool(test_result.get("success")) and bool(validation.get("meets_goal"))
        error_text = test_result.get("error") or ""
        output_text = test_result.get("output") or ""
        exec_time = test_result.get("execution_time")

        if success:
            patterns = self.extract_success_patterns(proposal, test_result)
            n_numbers = len(re.findall(r"\d+", output_text))
            analysis_text = (
                "Execution succeeded. "
                + ("Validation confirms goal met. " if validation.get("meets_goal") else "Validation uncertain. ")
                + f"Found {n_numbers} numbers in output. "
                + f"Strategies used: {', '.join(map(str, proposal.get('strategies_used', []))) or 'n/a'}."
            )
        else:
            diag = self.diagnose_failure(error_text, output_text)
            patterns = []
            analysis_text = (
                f"Execution failed. Diagnosis: {diag}. "
                f"Issues: {', '.join(test_result.get('issues', []) or []) or 'none'}. "
                f"Output length: {len(output_text)} chars."
            )

        analysis: Dict[str, Any] = {
            "success": success,
            "validation": validation,
            "issues": test_result.get("issues", []),
            "execution_time": exec_time,
            "analysis": analysis_text,
            "metrics": {
                "output_chars": len(output_text),
                "n_numbers": len(re.findall(r"\d+", output_text)),
            },
        }

        self.analyses.append(analysis)
        self._extract_insights(analysis, proposal)
        return analysis

    # ----------------------------
    # Pattern extraction & diagnosis
    # ----------------------------
    def extract_success_patterns(
        self,
        proposal: Dict[str, Any],
        test_result: Dict[str, Any],
    ) -> List[str]:
        """
        Simple heuristics to distill useful patterns from a successful attempt.
        """
        sol = proposal.get("solution", "") or ""
        patterns: List[str] = []

        if "sieve" in sol.lower():
            patterns.append("Sieve of Eratosthenes")
        if "def " in sol:
            patterns.append("Function Decomposition")
        if "try:" in sol and "except" in sol:
            patterns.append("Exception Handling")
        if "time" in sol.lower():
            patterns.append("Timing/Benchmarking")

        # Include any explicit strategy labels from the proposal
        strategies = proposal.get("strategies_used", []) or []
        for s in strategies:
            if isinstance(s, str):
                patterns.append(s)

        # Deduplicate while preserving order
        seen = set()
        uniq: List[str] = []
        for p in patterns:
            if p not in seen:
                uniq.append(p)
                seen.add(p)
        return uniq

    def diagnose_failure(self, error_text: str, output_text: str) -> str:
        """
        Classify failures to guide the next iteration.
        """
        e = (error_text or "").lower()
        if "timeout" in e or "timed out" in e:
            return "Timeout/Slow algorithm"
        if "module not found" in e or "no module named" in e:
            return "Missing dependency (constrain to stdlib or install)"
        if "syntaxerror" in e:
            return "Syntax error"
        if "typeerror" in e or "valueerror" in e:
            return "Type/value error"
        if "unboundlocalerror" in e:
            return "Variable scope issue"
        return "Runtime error"

    # ----------------------------
    # Insight persistence
    # ----------------------------
    def _extract_insights(self, analysis: Dict[str, Any], proposal: Dict[str, Any]):
        """
        Persist a compact insight to the Cognition Base.
        Store strategies as tuples to keep them hashable in sets.
        """
        try:
            strategies = proposal.get("strategies_used", [])
            # Normalize to tuple[str]
            if isinstance(strategies, (list, tuple)):
                norm_strats = tuple(str(s) for s in strategies)
            elif strategies is None:
                norm_strats = tuple()
            else:
                norm_strats = (str(strategies),)

            insight = {
                "goal": proposal.get("goal", ""),
                "strategy": norm_strats,  # tuple for hashability
                "success": bool(analysis.get("success")),
                "key_learning": (analysis.get("analysis") or "")[:280],
                "significance": 0.8 if analysis.get("success") else 0.3,
                "metrics": {
                    "execution_time": analysis.get("execution_time"),
                    **(analysis.get("metrics") or {}),
                },
            }
            self.cognition_base.add_insight(insight)
        except Exception as e:
            logger.warning(f"Failed to persist insight: {e}")

    def recommend_next_action(self) -> str:
        if not self.analyses:
            return "No data yet—generate an initial proposal."
        last = self.analyses[-1]
        if last.get("success") and last.get("validation", {}).get("meets_goal"):
            return "Goal met. Optimize performance or tackle a harder variant."
        if last.get("success"):
            return "Runs but validation is weak—tighten the algorithm and outputs."
        if len(self.analyses) >= 3:
            return "Multiple failures—consider revising approach or simplifying the goal."
        return "Refine based on the latest diagnosis."

    # ----------------------------
    # Final report for main.py
    # ----------------------------
    def generate_summary_report(self) -> str:
        """
        Build a concise final report from collected analyses.
        """
        if not self.analyses:
            return "No analyses available."

        total_iters = len(self.analyses)
        successes = sum(1 for a in self.analyses if a.get("success"))
        last = self.analyses[-1]
        goal_met = bool(last.get("validation", {}).get("meets_goal")) or bool(last.get("success"))

        # Execution time stats
        times = [t for t in (a.get("execution_time") for a in self.analyses) if isinstance(t, (int, float))]
        total_time = sum(times) if times else None
        avg_time = (total_time / len(times)) if times else None

        # Issues histogram
        issue_list: List[str] = []
        for a in self.analyses:
            issue_list.extend(a.get("issues", []) or [])
        issue_counts = Counter(issue_list)
        common_issues = ", ".join(f"{k}×{v}" for k, v in issue_counts.most_common(5)) if issue_counts else "none"

        # Provider/model info (best effort)
        try:
            prov = self.llm.get_provider_info()
            provider_str = f"{prov.get('provider','')} - {prov.get('model','')}"
        except Exception:
            provider_str = ""

        # Validation notes
        val = last.get("validation", {}) or {}
        val_notes = "; ".join(val.get("notes", [])[:3]) if isinstance(val.get("notes"), list) else ""

        lines = []
        lines.append(f"Provider/Model: {provider_str}".strip())
        lines.append(f"Iterations: {total_iters} | Successes: {successes}")
        if total_time is not None:
            lines.append(f"Execution time: total {total_time:.3f}s | avg {avg_time:.3f}s")
        else:
            lines.append("Execution time: n/a")
        lines.append(f"Goal status: {'SUCCESS' if goal_met else 'NOT MET'}")
        if val_notes:
            lines.append(f"Validation: {val_notes}")
        lines.append(f"Issues observed: {common_issues}")
        lines.append("")
        lines.append("Analysis summary:")
        lines.append((last.get("analysis") or "").strip() or "(no analysis text)")

        return "\n".join(lines)
