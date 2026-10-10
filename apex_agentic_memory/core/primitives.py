"""Apex_Agentic_Memory: Core Primitives and Data Contracts.

Defines foundational data structures for bi-temporal knowledge graphs,
Claude-Mem session hooks, Hindsight counterfactual reflections,
Nerve autonomic reflexes, and MiroFish submodular memory budgets.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import time
import hashlib
import json


class MemorySearchLayer(str, Enum):
    """Claude-Mem 3-layer progressive disclosure tiers."""
    SEARCH_INDEX = "SEARCH_INDEX"          # Layer 1: Compact tabular index (~50 tokens)
    TIMELINE_CONTEXT = "TIMELINE_CONTEXT"  # Layer 2: Chronological causal window (~150 tokens)
    DEEP_OBSERVATION = "DEEP_OBSERVATION"  # Layer 3: Full tool input/output & diffs (~500+ tokens)


class HookEventKind(str, Enum):
    """Claude-Mem 7-hook lifecycle events."""
    SETUP = "Setup"
    SESSION_START = "SessionStart"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    STOP = "Stop"
    SESSION_END = "SessionEnd"


class ReflexVerdict(str, Enum):
    """Nerve sub-millisecond reflex verdicts."""
    PASS = "PASS"                          # Safe, forward to LLM/tool execution
    INTERCEPT_CACHE = "INTERCEPT_CACHE"    # Deterministic read cached, return 0 tokens
    INTERCEPT_LOOP = "INTERCEPT_LOOP"      # Cyclic ping-pong detected, break recursion
    INTERCEPT_SAFETY = "INTERCEPT_SAFETY"  # Destructive unhedged action blocked


@dataclass(frozen=True)
class BiTemporalTriple:
    """Cognee Bi-Temporal Semantic Knowledge Triple.
    
    Distinguishes when a fact occurred in reality (Valid Time)
    from when the agent recorded/observed it (Transaction Time).
    """
    subject: str
    predicate: str
    object_val: str
    valid_start: float                       # UNIX timestamp when fact became valid
    valid_end: float = float("inf")          # UNIX timestamp when fact ceased to be valid
    transaction_time: float = field(default_factory=time.time) # When recorded by system
    confidence: float = 1.0                  # Confidence score [0.0, 1.0]
    source_session_id: str = "GLOBAL"

    @property
    def triple_hash(self) -> str:
        payload = f"{self.subject}:{self.predicate}:{self.object_val}:{self.valid_start}:{self.valid_end}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def is_valid_at(self, query_time: float) -> bool:
        """Determines if the fact holds true at a specific epoch time."""
        return self.valid_start <= query_time <= self.valid_end


@dataclass
class MemoryObservation:
    """Claude-Mem granular tool execution observation."""
    observation_id: str
    session_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: str
    timestamp: float = field(default_factory=time.time)
    title: str = ""
    narrative: str = ""
    file_paths: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    tokens_estimated: int = 0
    relevance_score: float = 0.0

    @property
    def observation_hash(self) -> str:
        raw = f"{self.session_id}:{self.tool_name}:{json.dumps(self.tool_input, sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class CounterfactualReflection:
    """Hermes Hindsight counterfactual reflection and experiential guardrail."""
    reflection_id: str
    session_id: str
    failed_tool_action: str
    recommended_alternative: str
    causal_root_cause: str
    regret_score: float                     # [0.0, 1.0] Regret penalty
    heuristic_rule: str                     # Synthesized negative guardrail for future prompts
    timestamp: float = field(default_factory=time.time)
    activation_count: int = 0


@dataclass
class ReflexDecision:
    """Hermes Nerve autonomic nervous system verdict."""
    verdict: ReflexVerdict
    reason: str
    cached_payload: Optional[str] = None
    latency_us: float = 0.0
    pattern_matched: str = "NONE"


@dataclass
class MemoryBudgetReport:
    """ApexGraphSwarm & MiroFish submodular context optimization report."""
    total_candidate_memories: int
    selected_memories_count: int
    token_budget: int
    consumed_tokens: int
    submodular_information_gain: float
    approximation_ratio: float = 0.63212    # Guaranteed (1 - 1/e)
    optimizer_latency_us: float = 0.0
    selected_ids: List[str] = field(default_factory=list)
