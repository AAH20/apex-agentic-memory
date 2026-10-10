"""Unit and Benchmark Test Suite for Apex_Agentic_Memory.

Comprehensive tests verifying all 6 pillars: Claude-Mem 7 hooks,
Hindsight counterfactual reflections, Cognee bi-temporal knowledge graphs,
Nerve sub-50us reflexes, Clef static arenas, and MiroFish submodular context optimization.
"""

import unittest
import time
import json
from apex_agentic_memory.core.primitives import (
    MemorySearchLayer,
    ReflexVerdict,
    HookEventKind,
)
from apex_agentic_memory.core.claude_mem_hooks import ClaudeMemLifecycleEngine
from apex_agentic_memory.core.hindsight_engine import HindsightReflectionEngine
from apex_agentic_memory.core.cognee_graph import CogneeKnowledgeGraph
from apex_agentic_memory.core.nerve_reflex import NerveReflexEngine
from apex_agentic_memory.core.clef_runtime import ClefMemoryArena, ClefWatchdog
from apex_agentic_memory.core.mirofish_submodular import MiroFishSubmodularContextOptimizer
from apex_agentic_memory.orchestrator import ApexAgenticMemoryOrchestrator
from apex_agentic_memory.adapters.claude_code_adapter import ClaudeCodeHookAdapter
from apex_agentic_memory.adapters.hermes_adapter import HermesMemoryMiddleware
from apex_agentic_memory.adapters.mcp_server import ApexMemoryMCPServer


class TestApexAgenticMemory(unittest.TestCase):

    def setUp(self):
        self.orchestrator = ApexAgenticMemoryOrchestrator(db_path=":memory:")

    def tearDown(self):
        self.orchestrator.close()

    # --- 1. Claude-Mem Lifecycle & Progressive Disclosure ---

    def test_claude_mem_all_seven_hooks(self):
        engine = ClaudeMemLifecycleEngine(db_path=":memory:")
        
        # 1. Setup
        res_setup = engine.hook_setup()
        self.assertEqual(res_setup["status"], "HEALTHY")

        # 2. SessionStart
        res_start = engine.hook_session_start("SESS-001", "PROJ-ALPHA")
        self.assertEqual(res_start["session_id"], "SESS-001")

        # 3. UserPromptSubmit
        res_prompt = engine.hook_user_prompt_submit("SESS-001", "Refactor the authentication middleware")
        self.assertIn("refactor", res_prompt["extracted_concepts"])

        # 4. PreToolUse
        res_pre = engine.hook_pre_tool_use("SESS-001", "view_file", {"path": "auth.py"})
        self.assertFalse(res_pre["is_cached_in_memory"])

        # 5. PostToolUse
        obs = engine.hook_post_tool_use(
            session_id="SESS-001",
            tool_name="view_file",
            tool_input={"path": "auth.py"},
            tool_output="def authenticate(user): pass",
            title="Read auth.py",
        )
        self.assertTrue(obs.observation_id.startswith("OBS-"))
        self.assertIn("auth.py", obs.file_paths)

        # Re-check PreToolUse for caching
        res_pre_again = engine.hook_pre_tool_use("SESS-001", "view_file", {"path": "auth.py"})
        self.assertTrue(res_pre_again["is_cached_in_memory"])

        # 6. Stop
        summary = engine.hook_stop(
            session_id="SESS-001",
            investigated=["auth.py"],
            learned=["Authentication needs token validation"],
            completed=["Read auth handler"],
            next_steps=["Implement JWT check"],
        )
        self.assertEqual(summary["learned"][0], "Authentication needs token validation")

        # 7. SessionEnd
        res_end = engine.hook_session_end("SESS-001")
        self.assertEqual(res_end["status"], "COMPLETED")
        self.assertEqual(res_end["total_observations"], 1)
        engine.close()

    def test_claude_mem_progressive_disclosure_layers(self):
        engine = ClaudeMemLifecycleEngine(db_path=":memory:")
        engine.hook_session_start("SESS-TEST", "PROJ")
        
        obs1 = engine.hook_post_tool_use("SESS-TEST", "run_test", {}, "AssertionError: expected 200 got 500", title="Test failure")
        obs2 = engine.hook_post_tool_use("SESS-TEST", "edit_file", {}, "Modified status code to 200", title="Fix handler")

        # Layer 1: Search Index
        idx_res = engine.search_progressive("failure", layer=MemorySearchLayer.SEARCH_INDEX)
        self.assertGreaterEqual(len(idx_res), 1)
        self.assertEqual(idx_res[0]["layer"], MemorySearchLayer.SEARCH_INDEX.value)
        self.assertIn("Test failure", idx_res[0]["title"])

        # Layer 2: Timeline Context
        time_res = engine.search_progressive("", layer=MemorySearchLayer.TIMELINE_CONTEXT, anchor_id=obs1.observation_id, limit=2)
        self.assertGreaterEqual(len(time_res), 1)
        self.assertEqual(time_res[0]["layer"], MemorySearchLayer.TIMELINE_CONTEXT.value)

        # Layer 3: Deep Observation
        deep_res = engine.search_progressive("", layer=MemorySearchLayer.DEEP_OBSERVATION, anchor_id=obs2.observation_id)
        self.assertEqual(len(deep_res), 1)
        self.assertEqual(deep_res[0]["layer"], MemorySearchLayer.DEEP_OBSERVATION.value)
        self.assertIn("Modified status code", deep_res[0]["tool_output"])
        engine.close()

    # --- 2. Hermes Hindsight Reflection & Guardrails ---

    def test_hindsight_reflection_and_guardrail_derivation(self):
        hindsight = HindsightReflectionEngine()
        
        reflection = hindsight.analyze_session_failure(
            session_id="SESS-01",
            failed_tool_action="delete_directory",
            tool_input={"path": "/var/data"},
            tool_error_output="PermissionError: Permission denied inside root directory",
            recommended_alternative="use_safe_staging_directory",
            utility_deficit=0.9,
        )

        self.assertIn("PERMISSION_OR_SANDBOX_RESTRICTION", reflection.causal_root_cause)
        self.assertTrue(reflection.heuristic_rule.startswith("GUARDRAIL:"))
        self.assertIn("use_safe_staging_directory", reflection.heuristic_rule)

        # Retrieve guardrails
        rules = hindsight.retrieve_applicable_guardrails("delete_directory", "cleaning up /var/data files")
        self.assertGreaterEqual(len(rules), 1)
        self.assertIn("use_safe_staging_directory", rules[0])

    # --- 3. Hermes Cognee Bi-Temporal Knowledge Graph ---

    def test_cognee_bitemporal_graph_and_superseding(self):
        cognee = CogneeKnowledgeGraph()
        t0 = time.time() - 100
        t1 = time.time()

        # Insert initial fact: DB_HOST was 10.0.0.1
        fact1 = cognee.insert_fact("Database", "HOST", "10.0.0.1", valid_start=t0)
        self.assertEqual(fact1.valid_end, float("inf"))

        # Query at t0 + 10: DB_HOST should be 10.0.0.1
        active_t0 = cognee.query_as_of("Database", "HOST", as_of_valid_time=t0 + 10)
        self.assertEqual(len(active_t0), 1)
        self.assertEqual(active_t0[0].object_val, "10.0.0.1")

        # Supersede fact: DB_HOST changed to 10.0.0.2 at t1
        fact2 = cognee.insert_fact("Database", "HOST", "10.0.0.2", valid_start=t1)
        
        # Query at t0 + 10 (Time-Travel historical query): Still 10.0.0.1
        historic = cognee.query_as_of("Database", "HOST", as_of_valid_time=t0 + 10)
        self.assertEqual(len(historic), 1)
        self.assertEqual(historic[0].object_val, "10.0.0.1")

        # Query at t1 + 10 (Current query): Now 10.0.0.2
        current = cognee.query_as_of("Database", "HOST", as_of_valid_time=t1 + 10)
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0].object_val, "10.0.0.2")

    def test_cognee_multi_hop_traversal(self):
        cognee = CogneeKnowledgeGraph()
        cognee.insert_fact("UserService", "CALLS", "AuthService")
        cognee.insert_fact("AuthService", "CONNECTS_TO", "PostgresCluster")
        cognee.insert_fact("PostgresCluster", "LOCATED_IN", "US-East-1")

        triples = cognee.multi_hop_traversal("UserService", max_hops=2)
        objects = {t.object_val for t in triples}
        self.assertIn("AuthService", objects)
        self.assertIn("PostgresCluster", objects)
        self.assertNotIn("US-East-1", objects)  # 3 hops away

    # --- 4. Hermes Nerve Sub-50us Reflexes ---

    def test_nerve_reflex_safety_shield(self):
        nerve = NerveReflexEngine()
        dec = nerve.intercept_and_evaluate("bash", {"command": "rm -rf / --no-preserve-root"})
        self.assertEqual(dec.verdict, ReflexVerdict.INTERCEPT_SAFETY)
        self.assertLessEqual(dec.latency_us, 500.0)

    def test_nerve_reflex_cyclic_loop_detection(self):
        nerve = NerveReflexEngine(loop_threshold=3)
        for _ in range(2):
            d = nerve.intercept_and_evaluate("view_file", {"path": "failing_test.py"})
            self.assertEqual(d.verdict, ReflexVerdict.PASS)

        # 3rd time in window should trigger loop interceptor
        d3 = nerve.intercept_and_evaluate("view_file", {"path": "failing_test.py"})
        self.assertEqual(d3.verdict, ReflexVerdict.INTERCEPT_LOOP)

    def test_nerve_deterministic_read_cache(self):
        nerve = NerveReflexEngine()
        nerve.cache_tool_result("read_file", {"path": "static_config.yaml"}, "port: 8080")
        
        dec = nerve.intercept_and_evaluate("read_file", {"path": "static_config.yaml"})
        self.assertEqual(dec.verdict, ReflexVerdict.INTERCEPT_CACHE)
        self.assertEqual(dec.cached_payload, "port: 8080")

    # --- 5. Cloudflare Clef Runtime & Arenas ---

    def test_clef_arena_static_allocation(self):
        arena = ClefMemoryArena(slot_capacity=4)
        for i in range(10):
            slot = arena.acquire_slot("SESSION", "tool", {}, f"output {i}")
            self.assertEqual(slot.tool_output, f"output {i}")
        self.assertEqual(arena.total_allocations, 10)

    def test_clef_watchdog_sla_enforcement(self):
        watchdog = ClefWatchdog(max_budget_us=1000.0)
        res, latency, within_sla = watchdog.execute_bounded("fast_op", lambda: 42)
        self.assertEqual(res, 42)
        self.assertTrue(within_sla)

    # --- 6. MiroFish Submodular Context Optimization ---

    def test_mirofish_submodular_token_budget_guarantee(self):
        optimizer = MiroFishSubmodularContextOptimizer()
        from apex_agentic_memory.core.primitives import MemoryObservation
        
        candidates = [
            MemoryObservation(f"OBS-{i}", "S", "tool", {}, f"Content {i} regarding machine learning and data pipelines", tokens_estimated=50)
            for i in range(15)
        ]

        selected, report = optimizer.optimize_context_selection(
            candidate_memories=candidates,
            query="machine learning data",
            token_budget=160,
        )

        self.assertLessEqual(report.consumed_tokens, 160)
        self.assertGreaterEqual(len(selected), 1)
        self.assertEqual(report.approximation_ratio, 0.63212)
        self.assertLessEqual(report.optimizer_latency_us, 5000.0)

    # --- 7. Master Orchestrator End-to-End ---

    def test_orchestrator_integration(self):
        self.orchestrator.start_session("INT-01", "INTEGRATION_TEST")
        
        obs = self.orchestrator.record_tool_execution(
            session_id="INT-01",
            tool_name="view_file",
            tool_input={"path": "backend/app.py"},
            tool_output="import fastapi\napp = fastapi.FastAPI()",
            title="FastAPI app inspection",
        )
        self.assertTrue(obs.observation_id.startswith("OBS-"))

        # Test failure reflection
        self.orchestrator.record_failure_reflection(
            session_id="INT-01",
            failed_tool_action="start_server",
            tool_input={"port": 80},
            tool_error_output="PermissionError: binding to port 80 requires root",
            recommended_alternative="use port 8000 instead",
        )

        # Test context assembly
        ctx = self.orchestrator.get_budgeted_prompt_context(
            query="backend app server setup",
            token_budget=500,
        )
        self.assertIn("Hindsight Heuristic Guardrails", ctx["formatted_context"])
        self.assertIn("use port 8000 instead", ctx["formatted_context"])

    # --- 8. Adapters & CLI ---

    def test_claude_code_adapter(self):
        adapter = ClaudeCodeHookAdapter(self.orchestrator)
        res = adapter.handle_hook_event("PreToolUse", {"tool_name": "bash", "tool_input": {"cmd": "rm -rf /"}})
        self.assertEqual(res["verdict"], ReflexVerdict.INTERCEPT_SAFETY.value)

    def test_hermes_middleware_adapter(self):
        middleware = HermesMemoryMiddleware(self.orchestrator)
        middleware.on_agent_init("HERMES-01")
        
        should_run, cached = middleware.before_tool_call("cat", {"path": "missing.txt"})
        self.assertTrue(should_run)
        self.assertIsNone(cached)

    def test_mcp_server_schemas_and_dispatch(self):
        server = ApexMemoryMCPServer(self.orchestrator)
        tools = server.get_tool_definitions()
        tool_names = [t["name"] for t in tools]
        self.assertIn("mem_search", tool_names)
        self.assertIn("mem_reflect", tool_names)
        self.assertIn("mem_graph_query", tool_names)
        self.assertIn("mem_budget_context", tool_names)

        # Dispatch reflect
        res = server.handle_tool_call("mem_reflect", {
            "session_id": "MCP-01",
            "failed_tool_action": "git_push",
            "error_message": "fatal: remote origin not found",
            "recommended_alternative": "git remote add origin URL",
        })
        self.assertIn("GUARDRAIL", res["heuristic_rule"])

    def test_cli_execution_benchmark_and_simulate(self):
        from apex_agentic_memory.cli import cmd_benchmark, cmd_simulate
        class MockArgs:
            iterations = 10
        self.assertEqual(cmd_benchmark(MockArgs()), 0)
        self.assertEqual(cmd_simulate(MockArgs()), 0)


if __name__ == "__main__":
    unittest.main()
