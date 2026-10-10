"""Apex_Agentic_Memory: Hermes Cognee Bi-Temporal Semantic Knowledge Graph.

Implements an in-memory bi-temporal knowledge graph tracking Subject-Predicate-Object
triples across Valid-Time (when it happened in reality) and Transaction-Time (when observed).
Provides multi-hop GraphRAG traversal without external database dependencies.
"""

import time
from typing import Dict, List, Optional, Set, Tuple, Any
from apex_agentic_memory.core.primitives import BiTemporalTriple


class CogneeKnowledgeGraph:
    """Zero-dependency in-memory bi-temporal semantic knowledge graph."""

    def __init__(self):
        # Master list of all triples ever recorded
        self._triples: List[BiTemporalTriple] = []
        # Adjacency index: subject -> list of triple indices
        self._out_edges: Dict[str, List[int]] = {}
        # Inverted index: object_val -> list of triple indices
        self._in_edges: Dict[str, List[int]] = {}
        # Predicate index: predicate -> list of triple indices
        self._pred_index: Dict[str, List[int]] = {}

    def insert_fact(
        self,
        subject: str,
        predicate: str,
        object_val: str,
        valid_start: Optional[float] = None,
        valid_end: float = float("inf"),
        confidence: float = 1.0,
        source_session_id: str = "GLOBAL",
    ) -> BiTemporalTriple:
        """Insert or update a bi-temporal knowledge triple.
        
        If a conflicting unclosed fact exists (same subject & predicate with valid_end=inf),
        it is superseded by setting its valid_end to valid_start.
        """
        now = time.time()
        v_start = valid_start if valid_start is not None else now

        # Supersede previous active facts with same (subject, predicate)
        if subject in self._out_edges:
            for idx in self._out_edges[subject]:
                old_triple = self._triples[idx]
                if old_triple.predicate == predicate and old_triple.valid_end == float("inf"):
                    # Create closed copy of old triple
                    closed_old = BiTemporalTriple(
                        subject=old_triple.subject,
                        predicate=old_triple.predicate,
                        object_val=old_triple.object_val,
                        valid_start=old_triple.valid_start,
                        valid_end=v_start,  # Closed at new start
                        transaction_time=old_triple.transaction_time,
                        confidence=old_triple.confidence,
                        source_session_id=old_triple.source_session_id,
                    )
                    self._triples[idx] = closed_old

        new_triple = BiTemporalTriple(
            subject=subject,
            predicate=predicate,
            object_val=object_val,
            valid_start=v_start,
            valid_end=valid_end,
            transaction_time=now,
            confidence=confidence,
            source_session_id=source_session_id,
        )

        idx = len(self._triples)
        self._triples.append(new_triple)

        # Update indexes
        if subject not in self._out_edges:
            self._out_edges[subject] = []
        self._out_edges[subject].append(idx)

        if object_val not in self._in_edges:
            self._in_edges[object_val] = []
        self._in_edges[object_val].append(idx)

        if predicate not in self._pred_index:
            self._pred_index[predicate] = []
        self._pred_index[predicate].append(idx)

        return new_triple

    def query_as_of(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        as_of_valid_time: Optional[float] = None,
    ) -> List[BiTemporalTriple]:
        """Query knowledge graph with bi-temporal valid-time filtering."""
        query_time = as_of_valid_time if as_of_valid_time is not None else time.time()
        results = []

        candidate_indices = None
        if subject and subject in self._out_edges:
            candidate_indices = set(self._out_edges[subject])
        elif predicate and predicate in self._pred_index:
            candidate_indices = set(self._pred_index[predicate])
        else:
            candidate_indices = set(range(len(self._triples)))

        for idx in candidate_indices:
            triple = self._triples[idx]
            if subject and triple.subject != subject:
                continue
            if predicate and triple.predicate != predicate:
                continue
            if triple.is_valid_at(query_time):
                results.append(triple)

        return results

    def multi_hop_traversal(
        self,
        start_entity: str,
        max_hops: int = 2,
        as_of_valid_time: Optional[float] = None,
    ) -> List[BiTemporalTriple]:
        """Perform breadth-first graph traversal up to max_hops from start_entity."""
        query_time = as_of_valid_time if as_of_valid_time is not None else time.time()
        visited_entities: Set[str] = {start_entity}
        frontier: Set[str] = {start_entity}
        collected_triples: List[BiTemporalTriple] = []

        for _ in range(max_hops):
            next_frontier: Set[str] = set()
            for entity in frontier:
                if entity in self._out_edges:
                    for idx in self._out_edges[entity]:
                        triple = self._triples[idx]
                        if triple.is_valid_at(query_time):
                            collected_triples.append(triple)
                            if triple.object_val not in visited_entities:
                                next_frontier.add(triple.object_val)
                                visited_entities.add(triple.object_val)
            frontier = next_frontier
            if not frontier:
                break

        return collected_triples

    def extract_triples_from_observation(self, tool_name: str, tool_input: Dict[str, Any], tool_output: str) -> List[BiTemporalTriple]:
        """Auto-extract semantic entity relations from tool inputs and outputs."""
        extracted = []
        target_path = tool_input.get("path") or tool_input.get("TargetFile") or tool_input.get("AbsolutePath")
        
        if target_path:
            # Relationship: tool -> MODIFIES / READS -> path
            pred = "MODIFIES" if "write" in tool_name.lower() or "edit" in tool_name.lower() or "replace" in tool_name.lower() else "READS"
            extracted.append(self.insert_fact(
                subject=tool_name,
                predicate=pred,
                object_val=target_path,
            ))

            # If output mentions dependencies, link them
            if "import " in tool_output or "from " in tool_output:
                for line in tool_output.splitlines():
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            mod = parts[1].split(".")[0]
                            extracted.append(self.insert_fact(
                                subject=target_path,
                                predicate="DEPENDS_ON",
                                object_val=mod,
                            ))

        return extracted
