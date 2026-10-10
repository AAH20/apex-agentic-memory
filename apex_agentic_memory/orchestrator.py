"""Apex_Agentic_Memory: Unified Master Cognitive Memory Orchestrator.

Integrates Claude-Mem 7-hook lifecycle, Hermes Hindsight reflections,
Cognee bi-temporal knowledge graphs, Nerve sub-50us reflexes, Clef static arenas,
and MiroFish submodular context optimization into a sovereign agent OS.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from apex_agentic_memory.core.primitives import (
    MemoryObservation,
    BiTemporalTriple,
    CounterfactualReflection,
    ReflexDecision,
    ReflexVerdict,
    MemorySearchLayer,
    MemoryBudgetReport,
)
from apex_agentic_memory.core.claude_mem_hooks import ClaudeMemLifecycleEngine
from apex_agentic_memory.core.hindsight_engine import HindsightReflectionEngine
from apex_agentic_memory.core.cognee_graph import CogneeKnowledgeGraph
from apex_agentic_memory.core.nerve_reflex import NerveReflexEngine
from apex_agentic_memory.core.clef_runtime import ClefMemoryArena, ClefWatchdog
from apex_agentic_memory.core.mirofish_submodular import MiroFishSubmodularContextOptimizer


class ApexAgenticMemoryOrchestrator:
    """Master OS orchestrating cognitive memory, reflection, and reflexes for frontier AI."""

    def __init__(self, db_path: str = ":memory:", slot_capacity: int = 512, watchdog_budget_us: float = 350.0):
        # 1. Claude-Mem Lifecycle Engine
        self.claude_mem = ClaudeMemLifecycleEngine(db_path=db_path)
        # 2. Hermes Hindsight Reflection Engine
        self.hindsight = HindsightReflectionEngine()
        # 3. Hermes Cognee Bi-Temporal Knowledge Graph
        self.cognee = CogneeKnowledgeGraph()
        # 4. Hermes Nerve Autonomic Reflex Engine
        self.nerve = NerveReflexEngine()
        # 5. Cloudflare Clef Static Arena & Watchdog
        self.arena = ClefMemoryArena(slot_capacity=slot_capacity)
        self.watchdog = ClefWatchdog(max_budget_us=watchdog_budget_us)
        # 6. MiroFish Submodular Context Optimizer
        self.mirofish = MiroFishSubmodularContextOptimizer()

    def start_session(self, session_id: str, project_name: str) -> Dict[str, Any]:
        """Initialize session and inject prior project context."""
        return self.claude_mem.hook_session_start(session_id, project_name)

    def intercept_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> ReflexDecision:
        """Autonomic Nerve reflex evaluation (< 50 us latency)."""
        return self.nerve.intercept_and_evaluate(tool_name, tool_input)

    def record_tool_execution(
        self,
        session_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str,
        title: Optional[str] = None,
    ) -> MemoryObservation:
        """Process completed tool execution across Claude-Mem, Cognee, and Nerve cache."""
        # 1. Acquire pre-allocated slot in Clef static arena
        slot = self.arena.acquire_slot(session_id, tool_name, tool_input, tool_output, title or "")

        # 2. Record persistent observation in Claude-Mem SQLite/FTS5
        obs = self.claude_mem.hook_post_tool_use(session_id, tool_name, tool_input, tool_output, title)

        # 3. Extract semantic entity relationships into Cognee bi-temporal graph
        self.cognee.extract_triples_from_observation(tool_name, tool_input, tool_output)

        # 4. Update Nerve deterministic read cache
        self.nerve.cache_tool_result(tool_name, tool_input, tool_output)

        return obs

    def record_failure_reflection(
        self,
        session_id: str,
        failed_tool_action: str,
        tool_input: Dict[str, Any],
        tool_error_output: str,
        recommended_alternative: str,
    ) -> CounterfactualReflection:
        """Record experiential failure into Hindsight and derive heuristic guardrails."""
        return self.hindsight.analyze_session_failure(
            session_id=session_id,
            failed_tool_action=failed_tool_action,
            tool_input=tool_input,
            tool_error_output=tool_error_output,
            recommended_alternative=recommended_alternative,
        )

    def get_budgeted_prompt_context(
        self,
        query: str,
        token_budget: int = 1500,
        as_of_valid_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Assemble optimal cognitive prompt context under strict token budget."""
        # 1. Retrieve applicable negative heuristic guardrails from Hindsight
        guardrails = self.hindsight.retrieve_applicable_guardrails("", query)

        # 2. Retrieve bi-temporal knowledge triples from Cognee graph
        triples = self.cognee.query_as_of(as_of_valid_time=as_of_valid_time)
        query_words = [w.lower() for w in query.replace("_", " ").split() if len(w) > 2]
        relevant_triples = [
            t for t in triples
            if any(w in t.subject.lower() or w in t.object_val.lower() or w in t.predicate.lower() for w in query_words)
        ]

        # 3. Query candidate observations from Claude-Mem via FTS5
        search_results = self.claude_mem.search_progressive(query, layer=MemorySearchLayer.SEARCH_INDEX, limit=15)
        
        # Load candidate observations
        candidate_obs: List[MemoryObservation] = []
        for res in search_results:
            deep_res = self.claude_mem.search_progressive(query="", layer=MemorySearchLayer.DEEP_OBSERVATION, anchor_id=res["observation_id"])
            if deep_res:
                d = deep_res[0]
                candidate_obs.append(MemoryObservation(
                    observation_id=d["observation_id"],
                    session_id=d["session_id"],
                    tool_name=d["tool_name"],
                    tool_input=d["tool_input"],
                    tool_output=d["tool_output"],
                    timestamp=d["timestamp"],
                    title=d["title"],
                    narrative=d["narrative"],
                    file_paths=d["file_paths"],
                    tokens_estimated=max(1, len(d["tool_output"]) // 4),
                ))

        # 4. Run MiroFish submodular context optimizer under token budget
        selected_obs, budget_report = self.mirofish.optimize_context_selection(
            candidate_memories=candidate_obs,
            query=query,
            token_budget=token_budget,
        )

        # 5. Format prompt context block
        prompt_blocks = []
        if guardrails:
            prompt_blocks.append("### Active Hindsight Heuristic Guardrails:")
            for g in guardrails:
                prompt_blocks.append(f"- {g}")

        if relevant_triples:
            prompt_blocks.append("\n### Cognee Bi-Temporal Knowledge Grounding:")
            for t in relevant_triples[:8]:
                prompt_blocks.append(f"- ({t.subject}) --[{t.predicate}]--> ({t.object_val}) [Valid since: {t.valid_start:.0f}]")

        if selected_obs:
            prompt_blocks.append("\n### Claude-Mem Progressive Observations (MiroFish Budgeted):")
            for obs in selected_obs:
                prompt_blocks.append(f"[{obs.observation_id}] {obs.title}: {obs.narrative}")

        return {
            "formatted_context": "\n".join(prompt_blocks),
            "guardrails_count": len(guardrails),
            "triples_count": len(relevant_triples),
            "selected_observations_count": len(selected_obs),
            "budget_report": budget_report,
        }

    def benchmark_subsystem_latencies(self, iterations: int = 100) -> Dict[str, float]:
        """Profile microsecond latencies across all subsystems."""
        # 1. Nerve Reflex Interception Latency
        nerve_times = []
        for _ in range(iterations):
            start = time.perf_counter_ns()
            self.nerve.intercept_and_evaluate("view_file", {"path": "/workspace/main.py"})
            nerve_times.append((time.perf_counter_ns() - start) / 1000.0)

        # 2. Cognee Bi-Temporal Query Latency
        self.cognee.insert_fact("main.py", "IMPORTS", "os")
        cognee_times = []
        for _ in range(iterations):
            start = time.perf_counter_ns()
            self.cognee.query_as_of(subject="main.py")
            cognee_times.append((time.perf_counter_ns() - start) / 1000.0)

        # 3. Clef Arena Slot Acquisition Latency
        arena_times = []
        for i in range(iterations):
            start = time.perf_counter_ns()
            self.arena.acquire_slot("BENCH", "view_file", {}, "file contents")
            arena_times.append((time.perf_counter_ns() - start) / 1000.0)

        # 4. MiroFish Submodular Pruning Latency
        mock_candidates = [
            MemoryObservation(
                observation_id=f"MOCK-{i}",
                session_id="BENCH",
                tool_name="view_file",
                tool_input={},
                tool_output=f"Sample output line {i} referencing database and server configuration.",
                title=f"Sample Observation {i}",
                narrative=f"Observation details for index {i}",
                tokens_estimated=30 + i * 5,
            )
            for i in range(20)
        ]
        mirofish_times = []
        for _ in range(iterations):
            start = time.perf_counter_ns()
            self.mirofish.optimize_context_selection(mock_candidates, "database server config", token_budget=300)
            mirofish_times.append((time.perf_counter_ns() - start) / 1000.0)

        return {
            "nerve_reflex_avg_us": round(sum(nerve_times) / len(nerve_times), 2),
            "cognee_query_avg_us": round(sum(cognee_times) / len(cognee_times), 2),
            "clef_arena_alloc_avg_us": round(sum(arena_times) / len(arena_times), 2),
            "mirofish_optimizer_avg_us": round(sum(mirofish_times) / len(mirofish_times), 2),
        }

    def close(self) -> None:
        """Cleanly close underlying SQLite connection."""
        self.claude_mem.close()

