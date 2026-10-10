"""Apex_Agentic_Memory: Hermes Hindsight Counterfactual Reflection Engine.

Implements experiential post-mortem learning, causal regret calculation,
and negative heuristic guardrail synthesis so agents never repeat past mistakes.
"""

import time
import hashlib
from typing import Dict, List, Optional, Any
from apex_agentic_memory.core.primitives import CounterfactualReflection


class HindsightReflectionEngine:
    """Zero-dependency counterfactual reflection & experiential guardrail synthesizer."""

    def __init__(self):
        # In-memory store of learned reflections: reflection_id -> CounterfactualReflection
        self._reflections: Dict[str, CounterfactualReflection] = {}
        # Inverted index from keywords/triggers to reflection IDs
        self._trigger_index: Dict[str, List[str]] = {}

    def analyze_session_failure(
        self,
        session_id: str,
        failed_tool_action: str,
        tool_input: Dict[str, Any],
        tool_error_output: str,
        recommended_alternative: str,
        utility_deficit: float = 0.85,
    ) -> CounterfactualReflection:
        """Construct counterfactual reflection and extract negative heuristic guardrail."""
        now = time.time()
        
        # Determine causal root cause from error output
        root_cause = "GENERAL_TOOL_EXECUTION_FAILURE"
        lower_err = tool_error_output.lower()
        if "not found" in lower_err or "no such file" in lower_err:
            root_cause = "PATH_OR_RESOURCE_NOT_FOUND"
        elif "permission denied" in lower_err or "unauthorized" in lower_err:
            root_cause = "PERMISSION_OR_SANDBOX_RESTRICTION"
        elif "syntaxerror" in lower_err or "invalid syntax" in lower_err:
            root_cause = "SYNTAX_VIOLATION_IN_CODE"
        elif "timeout" in lower_err or "timed out" in lower_err:
            root_cause = "EXECUTION_DEADLOCK_OR_TIMEOUT"
        elif "keyerror" in lower_err or "typeerror" in lower_err:
            root_cause = "SCHEMA_OR_TYPE_MISMATCH"

        # Synthesize negative heuristic guardrail
        heuristic_rule = (
            f"GUARDRAIL: When executing '{failed_tool_action}', AVOID inputs triggering {root_cause}. "
            f"Instead, perform: '{recommended_alternative}'."
        )

        ref_id = f"HINDSIGHT-{hash(f'{session_id}:{failed_tool_action}:{now}') & 0xFFFFFFFF:08x}"
        
        reflection = CounterfactualReflection(
            reflection_id=ref_id,
            session_id=session_id,
            failed_tool_action=failed_tool_action,
            recommended_alternative=recommended_alternative,
            causal_root_cause=root_cause,
            regret_score=min(1.0, max(0.1, utility_deficit)),
            heuristic_rule=heuristic_rule,
            timestamp=now,
        )

        self._reflections[ref_id] = reflection

        # Index triggers (tool name, root cause, keywords)
        triggers = [failed_tool_action.lower(), root_cause.lower()]
        for part in failed_tool_action.replace("_", " ").replace("-", " ").split():
            if len(part) > 2:
                triggers.append(part.lower())
        for part in root_cause.replace("_", " ").split():
            if len(part) > 2:
                triggers.append(part.lower())
        for k, v in tool_input.items():
            if isinstance(v, str):
                triggers.extend([w.lower() for w in v.split() if len(w) > 2])
            else:
                triggers.append(str(v).lower())

        for trigger in set(triggers):
            if trigger not in self._trigger_index:
                self._trigger_index[trigger] = []
            self._trigger_index[trigger].append(ref_id)

        return reflection

    def retrieve_applicable_guardrails(self, target_tool_name: str, query_context: str) -> List[str]:
        """Query reflections and return active heuristic guardrails matching the task context."""
        matched_ids = set()
        low_tool = target_tool_name.lower()
        if low_tool and low_tool in self._trigger_index:
            matched_ids.update(self._trigger_index[low_tool])

        for token in query_context.lower().replace("_", " ").replace("-", " ").split():
            clean = token.strip(".,;:?!()")
            if len(clean) > 2:
                if clean in self._trigger_index:
                    matched_ids.update(self._trigger_index[clean])
                for trig, rids in self._trigger_index.items():
                    if clean in trig or trig in clean:
                        matched_ids.update(rids)

        guardrails = []
        for rid in matched_ids:
            ref = self._reflections.get(rid)
            if ref:
                ref.activation_count += 1
                guardrails.append(ref.heuristic_rule)

        return guardrails

    def get_all_reflections(self) -> List[CounterfactualReflection]:
        """Return all stored reflections sorted by regret score descending."""
        return sorted(self._reflections.values(), key=lambda r: r.regret_score, reverse=True)
