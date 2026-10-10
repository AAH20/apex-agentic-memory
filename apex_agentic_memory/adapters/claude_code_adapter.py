"""Apex_Agentic_Memory: Claude Code CLI Hook Adapter.

Connects Claude Code lifecycle events directly into the Apex_Agentic_Memory orchestrator.
"""

import sys
import json
from typing import Dict, Any, Optional
from apex_agentic_memory.orchestrator import ApexAgenticMemoryOrchestrator


class ClaudeCodeHookAdapter:
    """Dispatches Claude Code lifecycle hooks to the Apex_Agentic_Memory OS."""

    def __init__(self, orchestrator: Optional[ApexAgenticMemoryOrchestrator] = None):
        self.orchestrator = orchestrator or ApexAgenticMemoryOrchestrator()

    def handle_hook_event(self, hook_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Claude Code hook event and return formatted response."""
        session_id = payload.get("session_id", "DEFAULT_SESSION")

        if hook_name == "Setup":
            return self.orchestrator.claude_mem.hook_setup()

        elif hook_name == "SessionStart":
            project = payload.get("project_name", "UNKNOWN_PROJECT")
            return self.orchestrator.start_session(session_id, project)

        elif hook_name == "UserPromptSubmit":
            prompt = payload.get("prompt_text", "")
            return self.orchestrator.claude_mem.hook_user_prompt_submit(session_id, prompt)

        elif hook_name == "PreToolUse":
            tool_name = payload.get("tool_name", "")
            tool_input = payload.get("tool_input", {})
            reflex = self.orchestrator.intercept_tool(tool_name, tool_input)
            return {
                "verdict": reflex.verdict.value,
                "reason": reflex.reason,
                "cached_payload": reflex.cached_payload,
                "latency_us": reflex.latency_us,
            }

        elif hook_name == "PostToolUse":
            tool_name = payload.get("tool_name", "")
            tool_input = payload.get("tool_input", {})
            tool_output = payload.get("tool_output", "")
            obs = self.orchestrator.record_tool_execution(session_id, tool_name, tool_input, tool_output)
            return {
                "observation_id": obs.observation_id,
                "tokens_estimated": obs.tokens_estimated,
                "status": "RECORDED",
            }

        elif hook_name == "Stop":
            return self.orchestrator.claude_mem.hook_stop(
                session_id=session_id,
                investigated=payload.get("investigated", []),
                learned=payload.get("learned", []),
                completed=payload.get("completed", []),
                next_steps=payload.get("next_steps", []),
            )

        elif hook_name == "SessionEnd":
            return self.orchestrator.claude_mem.hook_session_end(session_id)

        return {"status": "UNKNOWN_HOOK", "hook_name": hook_name}
