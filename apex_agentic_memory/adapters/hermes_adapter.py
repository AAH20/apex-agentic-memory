"""Apex_Agentic_Memory: Nous Research Hermes Agent Middleware Adapter.

Provides turnkey memory, reflection, and reflex middleware for Nous Research Hermes Agent.
"""

from typing import Dict, Any, Optional, Tuple
from apex_agentic_memory.orchestrator import ApexAgenticMemoryOrchestrator
from apex_agentic_memory.core.primitives import ReflexVerdict


class HermesMemoryMiddleware:
    """Turnkey middleware connecting Nous Research Hermes Agent to Apex_Agentic_Memory."""

    def __init__(self, orchestrator: Optional[ApexAgenticMemoryOrchestrator] = None):
        self.orchestrator = orchestrator or ApexAgenticMemoryOrchestrator()
        self.current_session_id = "HERMES-DEFAULT"

    def on_agent_init(self, agent_id: str, project_name: str = "HERMES_PROJECT") -> Dict[str, Any]:
        """Invoked when Hermes initializes a new execution run."""
        self.current_session_id = f"HERMES-{agent_id}"
        return self.orchestrator.start_session(self.current_session_id, project_name)

    def before_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Intercept tool call via Nerve autonomic reflex loop (< 50 us).
        
        Returns:
            (should_proceed, synthetic_cached_response)
        """
        verdict = self.orchestrator.intercept_tool(tool_name, arguments)
        
        if verdict.verdict == ReflexVerdict.INTERCEPT_CACHE:
            return False, verdict.cached_payload
        elif verdict.verdict in (ReflexVerdict.INTERCEPT_LOOP, ReflexVerdict.INTERCEPT_SAFETY):
            return False, f"EXECUTION_BLOCKED: {verdict.reason}"
        
        return True, None

    def after_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: str) -> None:
        """Record completed tool execution across Claude-Mem and Cognee knowledge graph."""
        self.orchestrator.record_tool_execution(
            session_id=self.current_session_id,
            tool_name=tool_name,
            tool_input=arguments,
            tool_output=result,
        )

    def on_tool_error(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        error_message: str,
        suggested_fix: str,
    ) -> None:
        """Derive Hindsight counterfactual reflection and negative heuristic guardrail."""
        self.orchestrator.record_failure_reflection(
            session_id=self.current_session_id,
            failed_tool_action=tool_name,
            tool_input=arguments,
            tool_error_output=error_message,
            recommended_alternative=suggested_fix,
        )

    def get_system_prompt_extension(self, current_task: str, token_budget: int = 1200) -> str:
        """Generate formatted prompt extension containing budgeted memory and active guardrails."""
        ctx = self.orchestrator.get_budgeted_prompt_context(
            query=current_task,
            token_budget=token_budget,
        )
        return ctx["formatted_context"]
