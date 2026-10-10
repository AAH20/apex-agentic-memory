# Integration Guide: Nous Research Hermes, Claude Code, & Cursor MCP

---

### 1. Nous Research Hermes Agent Integration

`Apex_Agentic_Memory` provides a first-class middleware adapter for the **Nous Research Hermes Agent** runtime:

```python
from apex_agentic_memory import ApexAgenticMemoryOrchestrator, HermesMemoryMiddleware

# 1. Initialize persistent memory orchestrator
orchestrator = ApexAgenticMemoryOrchestrator(db_path="~/.hermes/agent_memory.db")
middleware = HermesMemoryMiddleware(orchestrator=orchestrator)

# 2. Register agent session
middleware.on_agent_init(agent_id="HERMES-PROD-01", project_name="FINTECH_GATEWAY")

# 3. Fast-Reflex Tool Interception (Sub-50us Nerve Check)
tool_name = "view_file"
tool_args = {"path": "src/api/auth.py"}

should_run, cached_result = middleware.before_tool_call(tool_name, tool_args)
if not should_run:
    # Nerve intercepted: served from cache or blocked by loop/safety shield
    print(f"Nerve Reflex Output (0 LLM Tokens): {cached_result}")
else:
    # Execute actual tool
    tool_output = "def authenticate(): pass"
    middleware.after_tool_call(tool_name, tool_args, tool_output)

# 4. Inject Budgeted Memory & Active Guardrails into System Prompt
prompt_addon = middleware.get_system_prompt_extension(
    current_task="Fix auth token expiration bug",
    token_budget=1200
)
print("Injected Memory Context:\n", prompt_addon)
```

---

### 2. Claude Code CLI Hook Dispatcher

Claude Code communicates with external plugins via standard hook events. `Apex_Agentic_Memory` implements all 7 lifecycle hooks:

```python
from apex_agentic_memory import ClaudeCodeHookAdapter

adapter = ClaudeCodeHookAdapter()

# Dispatches directly from Claude Code lifecycle JSON events
response = adapter.handle_hook_event("PreToolUse", {
    "session_id": "CLAUDE-SESSION-42",
    "tool_name": "bash",
    "tool_input": {"command": "git status"}
})
print("Hook Response:", response)
```

---

### 3. Cursor & Claude Desktop MCP Configuration

To register `Apex_Agentic_Memory` as a Model Context Protocol (MCP) server in Cursor or Claude Desktop, add the following to your `mcp.json` / `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentic-memory": {
      "command": "agentic-memory",
      "args": ["mcp"]
    }
  }
}
```

#### Exposed MCP Tools:
- `mem_search`: Progressive search across Search Index, Timeline Context, and Deep Detail layers.
- `mem_record`: Ingest manual observation or learned fact into memory.
- `mem_reflect`: Submit execution errors to Hindsight to synthesize negative heuristic guardrails.
- `mem_graph_query`: Query Cognee bi-temporal knowledge triples with valid-time filtering.
- `mem_budget_context`: Fetch MiroFish submodular-budgeted prompt context.
