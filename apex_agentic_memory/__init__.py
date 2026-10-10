"""Apex_Agentic_Memory: Sovereign Cognitive Memory, Reflection & Fast-Reflex OS.

Uniting Claude-Mem 7-hook lifecycle, Hermes Hindsight counterfactual reflection,
Cognee bi-temporal knowledge graphs, Nerve sub-50us reflexes, Clef static arenas,
and MiroFish submodular NP-hard context optimization.
"""

from apex_agentic_memory.core.primitives import (
    BiTemporalTriple,
    MemoryObservation,
    CounterfactualReflection,
    ReflexDecision,
    ReflexVerdict,
    MemorySearchLayer,
    MemoryBudgetReport,
    HookEventKind,
)
from apex_agentic_memory.core.claude_mem_hooks import ClaudeMemLifecycleEngine
from apex_agentic_memory.core.hindsight_engine import HindsightReflectionEngine
from apex_agentic_memory.core.cognee_graph import CogneeKnowledgeGraph
from apex_agentic_memory.core.nerve_reflex import NerveReflexEngine
from apex_agentic_memory.core.clef_runtime import ClefMemoryArena, ClefWatchdog, export_clef_schema
from apex_agentic_memory.core.mirofish_submodular import MiroFishSubmodularContextOptimizer
from apex_agentic_memory.orchestrator import ApexAgenticMemoryOrchestrator
from apex_agentic_memory.adapters.claude_code_adapter import ClaudeCodeHookAdapter
from apex_agentic_memory.adapters.hermes_adapter import HermesMemoryMiddleware
from apex_agentic_memory.adapters.mcp_server import ApexMemoryMCPServer

__version__ = "1.0.0"

__all__ = [
    "ApexAgenticMemoryOrchestrator",
    "ClaudeMemLifecycleEngine",
    "HindsightReflectionEngine",
    "CogneeKnowledgeGraph",
    "NerveReflexEngine",
    "ClefMemoryArena",
    "ClefWatchdog",
    "MiroFishSubmodularContextOptimizer",
    "BiTemporalTriple",
    "MemoryObservation",
    "CounterfactualReflection",
    "ReflexDecision",
    "ReflexVerdict",
    "MemorySearchLayer",
    "MemoryBudgetReport",
    "HookEventKind",
    "ClaudeCodeHookAdapter",
    "HermesMemoryMiddleware",
    "ApexMemoryMCPServer",
    "export_clef_schema",
]
