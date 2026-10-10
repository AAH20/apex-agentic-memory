"""Apex_Agentic_Memory: Hermes Nerve Sub-50 μs Autonomic Nervous Reflex Loop.

Implements an ultra-low-latency reflex engine intercepting cyclic loops,
blocking destructive unhedged actions, and serving cached deterministic reads
in under 50 microseconds before waking up frontier reasoning models.
"""

import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from apex_agentic_memory.core.primitives import (
    ReflexVerdict,
    ReflexDecision,
)


class NerveReflexEngine:
    """Sub-50 microsecond autonomic nervous reflex loop and safety shield."""

    # High-risk destructive command patterns
    DANGEROUS_PATTERNS = [
        re.compile(r"\brm\s+-(?:r|f|rf|fr)\s+(?:/|\.\.|~|\*)", re.IGNORECASE),
        re.compile(r"\bmkfs\b", re.IGNORECASE),
        re.compile(r"\bdd\s+if=/dev/zero\b", re.IGNORECASE),
        re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
        re.compile(r"\bDROP\s+TABLE\s+production\b", re.IGNORECASE),
        re.compile(r"\bchmod\s+-R\s+777\s+/", re.IGNORECASE),
    ]

    def __init__(self, loop_threshold: int = 3, cache_ttl_seconds: float = 60.0):
        self.loop_threshold = loop_threshold
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # Recent call history: List of (tool_call_hash, timestamp)
        self._history: List[Tuple[str, float]] = []
        
        # Deterministic read cache: hash -> (output, timestamp)
        self._read_cache: Dict[str, Tuple[str, float]] = {}

    def intercept_and_evaluate(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> ReflexDecision:
        """Evaluate invocation in < 50 microseconds and return reflex decision."""
        start_ns = time.perf_counter_ns()
        now = time.time()

        # 1. Destructive Safety Shield Check
        input_str = str(tool_input)
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(input_str):
                elapsed_us = (time.perf_counter_ns() - start_ns) / 1000.0
                return ReflexDecision(
                    verdict=ReflexVerdict.INTERCEPT_SAFETY,
                    reason=f"Action blocked by Nerve Safety Shield matching forbidden regex pattern: {pattern.pattern}",
                    latency_us=round(elapsed_us, 2),
                    pattern_matched=pattern.pattern,
                )

        # 2. Hash Current Tool Invocation
        raw_sig = f"{tool_name}:{sorted(str(tool_input.items()))}"
        call_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]

        # 3. Cyclic Loop / Ping-Pong Detection
        recent_matches = sum(1 for h, _ in self._history[-10:] if h == call_hash)
        if recent_matches + 1 >= self.loop_threshold:
            elapsed_us = (time.perf_counter_ns() - start_ns) / 1000.0
            return ReflexDecision(
                verdict=ReflexVerdict.INTERCEPT_LOOP,
                reason=f"Cyclic tool loop detected: identical action invoked {recent_matches + 1} times in window",
                latency_us=round(elapsed_us, 2),
                pattern_matched=f"LOOP_THRESHOLD_{self.loop_threshold}",
            )

        # Record into history
        self._history.append((call_hash, now))
        if len(self._history) > 50:
            self._history.pop(0)

        # 4. Deterministic Read Cache
        is_read_op = any(r in tool_name.lower() for r in ["read", "view", "get", "fetch", "cat", "search"])
        if is_read_op and call_hash in self._read_cache:
            cached_output, cache_time = self._read_cache[call_hash]
            if now - cache_time <= self.cache_ttl_seconds:
                elapsed_us = (time.perf_counter_ns() - start_ns) / 1000.0
                return ReflexDecision(
                    verdict=ReflexVerdict.INTERCEPT_CACHE,
                    reason="Deterministic read served from sub-50us Nerve memory cache",
                    cached_payload=cached_output,
                    latency_us=round(elapsed_us, 2),
                    pattern_matched="CACHE_HIT",
                )

        # 5. Passed All Reflex Checks
        elapsed_us = (time.perf_counter_ns() - start_ns) / 1000.0
        return ReflexDecision(
            verdict=ReflexVerdict.PASS,
            reason="Passed autonomic nervous safety and loop checks",
            latency_us=round(elapsed_us, 2),
        )

    def cache_tool_result(self, tool_name: str, tool_input: Dict[str, Any], tool_output: str) -> None:
        """Cache deterministic read result for subsequent reflex hits."""
        is_read_op = any(r in tool_name.lower() for r in ["read", "view", "get", "fetch", "cat", "search"])
        if is_read_op:
            raw_sig = f"{tool_name}:{sorted(str(tool_input.items()))}"
            call_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]
            self._read_cache[call_hash] = (tool_output, time.time())
