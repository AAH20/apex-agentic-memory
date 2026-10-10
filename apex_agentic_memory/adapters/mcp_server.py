"""Apex_Agentic_Memory: Model Context Protocol (MCP) Server Adapter.

Pure Python standard library JSON-RPC 2.0 stdio server exposing memory tools to
Cursor, Claude Desktop, Windsurf, and any MCP-compatible agent environment.
"""

import sys
import json
from typing import Dict, Any, List, Optional
from apex_agentic_memory.orchestrator import ApexAgenticMemoryOrchestrator
from apex_agentic_memory.core.primitives import MemorySearchLayer


class ApexMemoryMCPServer:
    """Zero-dependency MCP JSON-RPC 2.0 server for Apex_Agentic_Memory."""

    def __init__(self, orchestrator: Optional[ApexAgenticMemoryOrchestrator] = None):
        self.orchestrator = orchestrator or ApexAgenticMemoryOrchestrator()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool schemas."""
        return [
            {
                "name": "mem_search",
                "description": "Progressive disclosure search across agent memory (Index, Timeline, or Deep Detail).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or keyword"},
                        "layer": {"type": "string", "enum": ["SEARCH_INDEX", "TIMELINE_CONTEXT", "DEEP_OBSERVATION"], "default": "SEARCH_INDEX"},
                        "anchor_id": {"type": "string", "description": "Optional observation ID for timeline anchoring"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "mem_record",
                "description": "Record a tool execution observation or learned fact into memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "tool_name": {"type": "string"},
                        "tool_input": {"type": "object"},
                        "tool_output": {"type": "string"},
                        "title": {"type": "string"},
                    },
                    "required": ["session_id", "tool_name", "tool_output"],
                },
            },
            {
                "name": "mem_reflect",
                "description": "Submit a failed action to Hermes Hindsight to synthesize negative heuristic guardrails.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "failed_tool_action": {"type": "string"},
                        "error_message": {"type": "string"},
                        "recommended_alternative": {"type": "string"},
                    },
                    "required": ["session_id", "failed_tool_action", "error_message", "recommended_alternative"],
                },
            },
            {
                "name": "mem_graph_query",
                "description": "Query Cognee bi-temporal knowledge graph for semantic entity relationships.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "predicate": {"type": "string"},
                        "as_of_valid_time": {"type": "number"},
                    },
                },
            },
            {
                "name": "mem_budget_context",
                "description": "Retrieve optimal prompt context using MiroFish submodular NP-hard optimization.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "token_budget": {"type": "integer", "default": 1500},
                    },
                    "required": ["query"],
                },
            },
        ]

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Route and execute tool invocation."""
        if name == "mem_search":
            layer_str = arguments.get("layer", "SEARCH_INDEX")
            layer = MemorySearchLayer(layer_str)
            return self.orchestrator.claude_mem.search_progressive(
                query=arguments.get("query", ""),
                layer=layer,
                anchor_id=arguments.get("anchor_id"),
                limit=arguments.get("limit", 5),
            )

        elif name == "mem_record":
            obs = self.orchestrator.record_tool_execution(
                session_id=arguments.get("session_id", "MCP_SESSION"),
                tool_name=arguments.get("tool_name", "CUSTOM"),
                tool_input=arguments.get("tool_input", {}),
                tool_output=arguments.get("tool_output", ""),
                title=arguments.get("title"),
            )
            return {"observation_id": obs.observation_id, "status": "RECORDED"}

        elif name == "mem_reflect":
            ref = self.orchestrator.record_failure_reflection(
                session_id=arguments.get("session_id", "MCP_SESSION"),
                failed_tool_action=arguments.get("failed_tool_action", ""),
                tool_input={},
                tool_error_output=arguments.get("error_message", ""),
                recommended_alternative=arguments.get("recommended_alternative", ""),
            )
            return {
                "reflection_id": ref.reflection_id,
                "heuristic_rule": ref.heuristic_rule,
                "regret_score": ref.regret_score,
            }

        elif name == "mem_graph_query":
            triples = self.orchestrator.cognee.query_as_of(
                subject=arguments.get("subject"),
                predicate=arguments.get("predicate"),
                as_of_valid_time=arguments.get("as_of_valid_time"),
            )
            return [
                {
                    "subject": t.subject,
                    "predicate": t.predicate,
                    "object_val": t.object_val,
                    "valid_start": t.valid_start,
                    "valid_end": t.valid_end,
                }
                for t in triples
            ]

        elif name == "mem_budget_context":
            return self.orchestrator.get_budgeted_prompt_context(
                query=arguments.get("query", ""),
                token_budget=arguments.get("token_budget", 1500),
            )

        raise ValueError(f"Unknown MCP tool: {name}")

    def run_stdio(self) -> None:
        """Run standard I/O JSON-RPC loop."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id")
                method = req.get("method")

                if method == "tools/list":
                    res = {"tools": self.get_tool_definitions()}
                    out = {"jsonrpc": "2.0", "id": req_id, "result": res}
                elif method == "tools/call":
                    params = req.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    res = self.handle_tool_call(name, arguments)
                    out = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}
                else:
                    out = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

                sys.stdout.write(json.dumps(out) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
