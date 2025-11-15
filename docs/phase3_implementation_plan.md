# Phase 3 Implementation Plan: Graph Structure for Dialectical Debate System

**Created:** 2025-11-15
**Author:** Claude (Sonnet 4.5)
**Context:** Building on Phase 0 (working debate generation) and Phase 2 (observer generation)

---

## Executive Summary

Phase 3 transforms the dialectical debate system from a linear transcript generator into a **semantic graph** that can:
- Capture resolved sub-debates as ArgumentNodes
- Link nodes with typed relationships (Supports, Contradicts, etc.)
- Query similar nodes via embedding-based similarity
- Linearize the graph for readable narrative output

**Key Challenge:** Determining when a sequence of DebateTurns becomes a complete ArgumentNode (the "semantic completion" problem).

**MVP Goal:** A working DAG that can accumulate nodes across multiple passages and surface relevant prior debates when processing new text.

---

## 1. Data Structures

### 1.1 ArgumentNode Class

An ArgumentNode represents a "semantic completion unit" - a resolved sub-debate or coherent argument thread.

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from datetime import datetime
from enum import Enum
import hashlib

class NodeType(Enum):
    """Types of semantic completion"""
    SYNTHESIS = "synthesis"           # Converged to agreement
    IMPASSE = "impasse"               # Reached irreconcilable disagreement
    LEMMA = "lemma"                   # Established sub-argument
    QUESTION = "question"             # Posed question with explorations
    EXPLORATION = "exploration"       # Open-ended investigation
    CLARIFICATION = "clarification"   # Definitional resolution

@dataclass
class ArgumentNode:
    """A semantically complete unit of dialectical debate"""

    # Core identity
    node_id: str = field(default_factory=lambda: hashlib.md5(
        str(datetime.now()).encode()).hexdigest()[:12])
    node_type: NodeType = NodeType.EXPLORATION

    # Content
    topic: str                        # What this node is about (1-2 sentences)
    turns: List['DebateTurn']         # The actual debate transcript
    resolution: str                   # What got resolved/concluded (paragraph)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source_passage: Optional[str] = None  # Original text that spawned this
    agent_names: List[str] = field(default_factory=list)

    # Semantic content (for similarity search)
    theme_tags: Set[str] = field(default_factory=set)  # e.g., {"free-will", "determinism"}
    key_claims: List[str] = field(default_factory=list)  # Main assertions made

    # Graph connections (managed by DAG)
    parent_nodes: Set[str] = field(default_factory=set)  # Node IDs this branches from
    child_nodes: Set[str] = field(default_factory=set)   # Node IDs that branch from this

    # Embedding for similarity (computed lazily)
    _embedding: Optional[List[float]] = field(default=None, repr=False)

    def __str__(self):
        """Human-readable summary"""
        return f"[{self.node_type.value}] {self.topic[:50]}..."

    def get_text_for_embedding(self) -> str:
        """Text representation for computing embeddings"""
        turns_text = "\n".join(f"{t.agent_name}: {t.content}" for t in self.turns[-5:])
        return f"{self.topic}\n\n{self.resolution}\n\nKey discussion:\n{turns_text}"

    def to_dict(self) -> dict:
        """Serialize for JSON persistence"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "topic": self.topic,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat(),
            "source_passage": self.source_passage,
            "agent_names": self.agent_names,
            "theme_tags": list(self.theme_tags),
            "key_claims": self.key_claims,
            "parent_nodes": list(self.parent_nodes),
            "child_nodes": list(self.child_nodes),
            # Store turns separately for size
            "turn_count": len(self.turns)
        }

    @staticmethod
    def from_dict(data: dict, turns: List['DebateTurn']) -> 'ArgumentNode':
        """Deserialize from JSON"""
        node = ArgumentNode(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            topic=data["topic"],
            turns=turns,
            resolution=data["resolution"],
            created_at=datetime.fromisoformat(data["created_at"]),
            source_passage=data.get("source_passage"),
            agent_names=data.get("agent_names", []),
            theme_tags=set(data.get("theme_tags", [])),
            key_claims=data.get("key_claims", []),
        )
        node.parent_nodes = set(data.get("parent_nodes", []))
        node.child_nodes = set(data.get("child_nodes", []))
        return node
```

### 1.2 Edge Class

Edges represent typed relationships between ArgumentNodes.

```python
class EdgeType(Enum):
    """Types of relationships between argument nodes"""
    SUPPORTS = "supports"           # Node A provides evidence for Node B
    CONTRADICTS = "contradicts"     # Node A conflicts with Node B
    ELABORATES = "elaborates"       # Node A expands on Node B
    REQUIRES = "requires"           # Node A depends on Node B
    APPLIES_TO = "applies_to"       # Node A is instance of Node B
    ANALOGY = "analogy"             # Node A is analogous to Node B
    BRANCHES_FROM = "branches_from" # Node A emerged as branch of Node B

@dataclass
class Edge:
    """Directed edge between ArgumentNodes"""

    from_node_id: str
    to_node_id: str
    edge_type: EdgeType

    # Optional justification
    description: Optional[str] = None  # Why this relationship exists
    confidence: float = 1.0            # 0-1, how certain is this relationship

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    detected_by: str = "manual"        # "manual", "automatic", or observer name

    def __str__(self):
        arrow = {
            EdgeType.SUPPORTS: "→",
            EdgeType.CONTRADICTS: "⊥",
            EdgeType.ELABORATES: "⇢",
            EdgeType.REQUIRES: "⇐",
            EdgeType.APPLIES_TO: "∈",
            EdgeType.ANALOGY: "≈",
            EdgeType.BRANCHES_FROM: "↗"
        }.get(self.edge_type, "→")

        return f"{self.from_node_id} {arrow} {self.to_node_id}"

    def to_dict(self) -> dict:
        return {
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "edge_type": self.edge_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "detected_by": self.detected_by
        }

    @staticmethod
    def from_dict(data: dict) -> 'Edge':
        return Edge(
            from_node_id=data["from_node_id"],
            to_node_id=data["to_node_id"],
            edge_type=EdgeType(data["edge_type"]),
            description=data.get("description"),
            confidence=data.get("confidence", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            detected_by=data.get("detected_by", "manual")
        )
```

### 1.3 DAG Class

The core graph structure with operations for building and querying.

```python
from typing import Tuple, Callable
import json
from pathlib import Path

class DebateDAG:
    """Directed Acyclic Graph of ArgumentNodes"""

    def __init__(self):
        self.nodes: Dict[str, ArgumentNode] = {}
        self.edges: List[Edge] = []
        self._embedding_cache: Dict[str, List[float]] = {}

    # === Core Operations ===

    def add_node(self, node: ArgumentNode) -> str:
        """Add a node to the graph. Returns node_id."""
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists")

        self.nodes[node.node_id] = node
        return node.node_id

    def add_edge(self, edge: Edge) -> None:
        """Add an edge between nodes"""
        # Validate nodes exist
        if edge.from_node_id not in self.nodes:
            raise ValueError(f"Source node {edge.from_node_id} not found")
        if edge.to_node_id not in self.nodes:
            raise ValueError(f"Target node {edge.to_node_id} not found")

        # Check for cycles (simplified - just check direct reversal)
        if any(e.from_node_id == edge.to_node_id and
               e.to_node_id == edge.from_node_id for e in self.edges):
            # Allow contradictory edges in opposite directions
            if edge.edge_type != EdgeType.CONTRADICTS:
                raise ValueError(f"Edge would create cycle: {edge}")

        # Update node connections for BRANCHES_FROM
        if edge.edge_type == EdgeType.BRANCHES_FROM:
            self.nodes[edge.from_node_id].parent_nodes.add(edge.to_node_id)
            self.nodes[edge.to_node_id].child_nodes.add(edge.from_node_id)

        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[ArgumentNode]:
        """Retrieve a node by ID"""
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str,
                          edge_type: Optional[EdgeType] = None) -> List[Edge]:
        """Get edges originating from this node"""
        edges = [e for e in self.edges if e.from_node_id == node_id]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_incoming_edges(self, node_id: str,
                          edge_type: Optional[EdgeType] = None) -> List[Edge]:
        """Get edges pointing to this node"""
        edges = [e for e in self.edges if e.to_node_id == node_id]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    # === Querying ===

    def find_nodes_by_topic(self, query: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Simple keyword-based topic search (pre-embedding MVP)"""
        query_words = set(query.lower().split())
        results = []

        for node_id, node in self.nodes.items():
            topic_words = set(node.topic.lower().split())
            # Simple Jaccard similarity
            intersection = query_words & topic_words
            union = query_words | topic_words
            similarity = len(intersection) / len(union) if union else 0

            if similarity >= threshold:
                results.append((node_id, similarity))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def find_nodes_by_tag(self, tag: str) -> List[str]:
        """Find nodes with a specific theme tag"""
        return [node_id for node_id, node in self.nodes.items()
                if tag.lower() in {t.lower() for t in node.theme_tags}]

    # === Persistence ===

    def save(self, filepath: Path) -> None:
        """Save graph to JSON"""
        data = {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "edge_count": len(self.edges)
            }
        }

        # Save turns separately (can be large)
        turns_data = {
            nid: [{"agent": t.agent_name, "content": t.content, "round": t.round_num}
                  for t in node.turns]
            for nid, node in self.nodes.items()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        turns_file = filepath.parent / f"{filepath.stem}_turns.json"
        with open(turns_file, 'w') as f:
            json.dump(turns_data, f, indent=2)

    @staticmethod
    def load(filepath: Path) -> 'DebateDAG':
        """Load graph from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        turns_file = filepath.parent / f"{filepath.stem}_turns.json"
        with open(turns_file, 'r') as f:
            turns_data = json.load(f)

        dag = DebateDAG()

        # Reconstruct nodes
        for node_id, node_dict in data["nodes"].items():
            from dialectic_poc import DebateTurn  # Import existing class
            turns = [DebateTurn(t["agent"], t["content"], t["round"])
                    for t in turns_data[node_id]]
            node = ArgumentNode.from_dict(node_dict, turns)
            dag.nodes[node_id] = node

        # Reconstruct edges
        for edge_dict in data["edges"]:
            dag.edges.append(Edge.from_dict(edge_dict))

        return dag

    def __len__(self):
        return len(self.nodes)

    def __str__(self):
        return f"DebateDAG({len(self.nodes)} nodes, {len(self.edges)} edges)"
```

---

## 2. Node Creation Strategy

### 2.1 Detecting Semantic Completion

**The Hard Problem:** When does a sequence of DebateTurns become an ArgumentNode?

**Start Simple, MVP Approach:**

```python
class NodeCreationDetector:
    """Detects when a debate segment is complete enough to become a node"""

    def __init__(self):
        self.min_turns = 4           # At least 2 rounds
        self.max_turns = 12          # Cap before forcing completion

    def should_create_node(self,
                          turns: List['DebateTurn'],
                          branch_question: Optional[str] = None) -> Tuple[bool, NodeType, str]:
        """
        Returns: (should_create, node_type, reason)

        MVP Strategy: Use explicit markers first
        """

        if len(turns) < self.min_turns:
            return False, None, "Too few turns"

        if len(turns) >= self.max_turns:
            return True, NodeType.EXPLORATION, "Max turns reached"

        # Strategy 1: Explicit completion markers
        completion = self._check_explicit_completion(turns)
        if completion[0]:
            return completion

        # Strategy 2: Question-answer detection (for branch debates)
        if branch_question:
            qa_result = self._check_question_answered(turns, branch_question)
            if qa_result[0]:
                return qa_result

        # Strategy 3: Repetition detection (circular arguments)
        if self._detect_repetition(turns):
            return True, NodeType.IMPASSE, "Circular arguments detected"

        # Default: not yet complete
        return False, None, "Still developing"

    def _check_explicit_completion(self, turns: List['DebateTurn']) -> Tuple[bool, Optional[NodeType], str]:
        """Look for explicit synthesis/agreement/impasse language"""

        # Get last 2 turns
        recent = [t.content.lower() for t in turns[-2:]]

        # Synthesis markers
        synthesis_markers = [
            "we agree that", "common ground", "synthesis",
            "both perspectives", "reconcile", "integrated view"
        ]
        if any(marker in turn for turn in recent for marker in synthesis_markers):
            return True, NodeType.SYNTHESIS, "Explicit synthesis language"

        # Impasse markers
        impasse_markers = [
            "fundamental disagreement", "cannot reconcile",
            "irreconcilable", "agree to disagree", "core tension"
        ]
        if any(marker in turn for turn in recent for marker in impasse_markers):
            return True, NodeType.IMPASSE, "Explicit impasse language"

        # Clarification markers
        clarify_markers = [
            "to clarify", "what we mean is", "defining terms",
            "precisely speaking", "in other words"
        ]
        if any(marker in turn for turn in recent for marker in clarify_markers):
            if len(turns) >= 6:  # Need sufficient discussion
                return True, NodeType.CLARIFICATION, "Definitional resolution"

        return False, None, ""

    def _check_question_answered(self, turns: List['DebateTurn'],
                                question: str) -> Tuple[bool, Optional[NodeType], str]:
        """For branch debates: Has the question been adequately addressed?"""

        # Use LLM to judge if question is answered
        last_turns = "\n".join(f"{t.agent_name}: {t.content}" for t in turns[-4:])

        from dialectic_poc import llm_call

        system_prompt = """You judge whether a question has been adequately addressed.

        Answer YES if:
        - Multiple perspectives have been offered
        - Core aspects of the question explored
        - Some provisional answer attempted (even if partial)

        Answer NO if:
        - Question is being ignored
        - Discussion is tangential
        - Just started engaging with it

        Output only: YES or NO"""

        user_prompt = f"""Question: {question}

Recent discussion:
{last_turns}

Has the question been adequately addressed?"""

        response = llm_call(system_prompt, user_prompt, temperature=0.3)

        if "YES" in response.upper():
            return True, NodeType.QUESTION, "Question adequately addressed"

        return False, None, ""

    def _detect_repetition(self, turns: List['DebateTurn']) -> bool:
        """Detect if agents are repeating themselves (circular argument)"""

        if len(turns) < 6:
            return False

        # Simple heuristic: compare recent turns to earlier ones
        # Look for high word overlap suggesting repetition

        def get_content_words(text: str) -> Set[str]:
            # Remove common words
            common = {"the", "a", "is", "are", "in", "to", "of", "and", "that", "this"}
            words = set(text.lower().split())
            return words - common

        # Check if last 2 turns overlap significantly with turns 4-6 back
        recent_words = set()
        for turn in turns[-2:]:
            recent_words.update(get_content_words(turn.content))

        earlier_words = set()
        for turn in turns[-6:-4] if len(turns) >= 6 else turns[:2]:
            earlier_words.update(get_content_words(turn.content))

        if not recent_words or not earlier_words:
            return False

        overlap = len(recent_words & earlier_words) / min(len(recent_words), len(earlier_words))

        return overlap > 0.6  # 60% word overlap suggests repetition
```

### 2.2 Creating Nodes from Transcripts

```python
class NodeFactory:
    """Creates ArgumentNodes from debate transcripts"""

    def __init__(self):
        self.detector = NodeCreationDetector()

    def create_node_from_debate(self,
                               turns: List['DebateTurn'],
                               source_passage: str,
                               branch_question: Optional[str] = None) -> ArgumentNode:
        """
        Create an ArgumentNode from a completed debate

        Args:
            turns: The debate transcript
            source_passage: Original text that spawned this debate
            branch_question: If this is a branch debate, the question being explored
        """

        # Determine node type
        _, node_type, _ = self.detector.should_create_node(turns, branch_question)
        if node_type is None:
            node_type = NodeType.EXPLORATION  # Default

        # Generate topic summary
        topic = self._generate_topic(turns, branch_question)

        # Generate resolution summary
        resolution = self._generate_resolution(turns, node_type, branch_question)

        # Extract theme tags and key claims
        theme_tags = self._extract_theme_tags(turns, source_passage)
        key_claims = self._extract_key_claims(turns)

        # Create node
        node = ArgumentNode(
            node_type=node_type,
            topic=topic,
            turns=turns,
            resolution=resolution,
            source_passage=source_passage,
            agent_names=list(set(t.agent_name for t in turns)),
            theme_tags=theme_tags,
            key_claims=key_claims
        )

        return node

    def _generate_topic(self, turns: List['DebateTurn'],
                       branch_question: Optional[str] = None) -> str:
        """Generate 1-2 sentence topic summary"""

        from dialectic_poc import llm_call

        if branch_question:
            return f"Branch: {branch_question}"

        debate_text = "\n".join(f"{t.agent_name}: {t.content}" for t in turns[:4])

        system_prompt = """Generate a concise topic statement (1-2 sentences) summarizing what this debate is about.

        Focus on the QUESTION or ISSUE being explored, not the positions taken."""

        user_prompt = f"""Debate excerpt:
{debate_text}

Topic:"""

        return llm_call(system_prompt, user_prompt, temperature=0.4).strip()

    def _generate_resolution(self, turns: List['DebateTurn'],
                            node_type: NodeType,
                            branch_question: Optional[str] = None) -> str:
        """Generate resolution summary (paragraph)"""

        from dialectic_poc import llm_call

        debate_text = "\n".join(f"{t.agent_name}: {t.content}" for t in turns)

        system_prompt = f"""Summarize how this debate resolved (3-4 sentences).

This is a {node_type.value.upper()} node, so:
- SYNTHESIS: Describe the common ground reached
- IMPASSE: Describe the irreconcilable tension
- LEMMA: Describe the sub-argument established
- QUESTION: Describe the range of answers explored
- EXPLORATION: Describe the territory covered
- CLARIFICATION: Describe the definition/distinction made"""

        user_prompt = f"""Debate:
{debate_text}

Resolution:"""

        return llm_call(system_prompt, user_prompt, temperature=0.5).strip()

    def _extract_theme_tags(self, turns: List['DebateTurn'],
                           source_passage: str) -> Set[str]:
        """Extract 3-5 theme tags for this node"""

        from dialectic_poc import llm_call

        debate_snippet = "\n".join(f"{t.agent_name}: {t.content}"
                                  for t in turns[:3] + turns[-2:])

        system_prompt = """Extract 3-5 theme tags (single words or short phrases) that categorize this debate.

Examples: "free-will", "causation", "identity", "metaphor", "literal-vs-symbolic"

Output as comma-separated list."""

        user_prompt = f"""Passage: {source_passage[:200]}

Debate snippet:
{debate_snippet}

Tags:"""

        tags_text = llm_call(system_prompt, user_prompt, temperature=0.3)
        tags = {tag.strip().lower() for tag in tags_text.split(',')}

        return tags

    def _extract_key_claims(self, turns: List['DebateTurn']) -> List[str]:
        """Extract 2-4 key claims made in this debate"""

        from dialectic_poc import llm_call

        debate_text = "\n".join(f"{t.agent_name}: {t.content}" for t in turns)

        system_prompt = """Extract 2-4 key claims made in this debate.

        A claim is an assertion that could be true or false, not a question.

        Format as numbered list."""

        user_prompt = f"""Debate:
{debate_text}

Key claims:"""

        claims_text = llm_call(system_prompt, user_prompt, temperature=0.4)

        # Parse numbered list
        claims = []
        for line in claims_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                claim = line.lstrip('0123456789.-) ').strip()
                if claim:
                    claims.append(claim)

        return claims[:4]  # Cap at 4
```

---

## 3. Edge Detection

### 3.1 Automatic Edge Creation

For MVP, focus on **BRANCHES_FROM** edges (created automatically during debate flow) and simple **CONTRADICTS** detection.

```python
class EdgeDetector:
    """Detects relationships between ArgumentNodes"""

    def detect_edges_for_new_node(self,
                                 new_node: ArgumentNode,
                                 dag: DebateDAG) -> List[Edge]:
        """
        When a new node is added, detect edges to existing nodes

        MVP: Focus on simple, high-confidence relationships
        """

        edges = []

        # 1. BRANCHES_FROM edges (already known from debate flow)
        # These are handled externally during branch creation

        # 2. CONTRADICTS edges (look for nodes with opposing claims)
        contradicting = self._find_contradictions(new_node, dag)
        edges.extend(contradicting)

        # 3. ELABORATES edges (look for nodes on same topic)
        elaborations = self._find_elaborations(new_node, dag)
        edges.extend(elaborations)

        return edges

    def _find_contradictions(self, new_node: ArgumentNode,
                            dag: DebateDAG) -> List[Edge]:
        """Find nodes that contradict this one"""

        edges = []

        # Simple heuristic: look for overlapping tags but IMPASSE node type
        if new_node.node_type != NodeType.IMPASSE:
            return edges

        for node_id, node in dag.nodes.items():
            if node_id == new_node.node_id:
                continue

            # Check for tag overlap
            tag_overlap = new_node.theme_tags & node.theme_tags
            if len(tag_overlap) >= 2:  # At least 2 shared tags
                # Check if both are impasse or synthesis
                if node.node_type in [NodeType.IMPASSE, NodeType.SYNTHESIS]:
                    edge = Edge(
                        from_node_id=new_node.node_id,
                        to_node_id=node_id,
                        edge_type=EdgeType.CONTRADICTS,
                        description=f"Irreconcilable positions on: {', '.join(tag_overlap)}",
                        confidence=0.6,
                        detected_by="automatic"
                    )
                    edges.append(edge)

        return edges

    def _find_elaborations(self, new_node: ArgumentNode,
                          dag: DebateDAG) -> List[Edge]:
        """Find nodes that this elaborates on"""

        edges = []

        # Simple heuristic: same tags, sequential creation
        for node_id, node in dag.nodes.items():
            if node_id == new_node.node_id:
                continue

            # Check for high tag overlap
            tag_overlap = new_node.theme_tags & node.theme_tags
            if len(tag_overlap) >= 3:  # Very similar topics
                # Check if created later (elaboration adds detail)
                if new_node.created_at > node.created_at:
                    edge = Edge(
                        from_node_id=new_node.node_id,
                        to_node_id=node_id,
                        edge_type=EdgeType.ELABORATES,
                        description=f"Further explores: {', '.join(tag_overlap)}",
                        confidence=0.5,
                        detected_by="automatic"
                    )
                    edges.append(edge)
                    break  # Only one elaboration edge per node

        return edges

    def suggest_manual_edges(self, node_id: str, dag: DebateDAG) -> List[Tuple[str, EdgeType, str]]:
        """
        Suggest edges for manual review

        Returns: List of (target_node_id, edge_type, reasoning)
        """

        suggestions = []
        node = dag.get_node(node_id)
        if not node:
            return suggestions

        # Use LLM to suggest relationships
        from dialectic_poc import llm_call

        # Get candidate nodes (same tags or recent)
        candidates = []
        for other_id, other in dag.nodes.items():
            if other_id == node_id:
                continue

            overlap = node.theme_tags & other.theme_tags
            if overlap or (node.created_at - other.created_at).days < 7:
                candidates.append((other_id, other))

        if not candidates:
            return suggestions

        # For each candidate, ask LLM about relationship
        for other_id, other in candidates[:5]:  # Limit to 5
            system_prompt = """You identify relationships between debate nodes.

Possible relationships:
- SUPPORTS: Node A provides evidence for Node B
- CONTRADICTS: Node A conflicts with Node B
- ELABORATES: Node A expands on Node B
- REQUIRES: Node A depends on Node B
- APPLIES_TO: Node A is instance of Node B
- ANALOGY: Node A is analogous to Node B

Output format:
RELATIONSHIP: [type or NONE]
REASONING: [one sentence]"""

            user_prompt = f"""Node A Topic: {node.topic}
Node A Resolution: {node.resolution[:200]}

Node B Topic: {other.topic}
Node B Resolution: {other.resolution[:200]}

Does Node A have a relationship to Node B?"""

            response = llm_call(system_prompt, user_prompt, temperature=0.4)

            # Parse response
            if "NONE" not in response and "RELATIONSHIP:" in response:
                lines = response.strip().split('\n')
                rel_line = [l for l in lines if l.startswith("RELATIONSHIP:")][0]
                reason_line = [l for l in lines if l.startswith("REASONING:")]

                rel_type = rel_line.split(":", 1)[1].strip().upper()
                reasoning = reason_line[0].split(":", 1)[1].strip() if reason_line else ""

                try:
                    edge_type = EdgeType[rel_type]
                    suggestions.append((other_id, edge_type, reasoning))
                except KeyError:
                    pass

        return suggestions
```

### 3.2 Which Edge Types to Implement First

**MVP Priority:**

1. **BRANCHES_FROM** - Essential for tracking debate structure (automatic)
2. **CONTRADICTS** - Captures tension (semi-automatic)
3. **ELABORATES** - Shows deepening understanding (semi-automatic)

**Defer to Later:**

4. SUPPORTS - Requires careful logical analysis
5. REQUIRES - Needs dependency tracking
6. APPLIES_TO - Needs abstraction hierarchy
7. ANALOGY - Complex to detect reliably

---

## 4. Node Similarity

### 4.1 MVP: Simple Text-Based Similarity

Before implementing embeddings, use simple text overlap:

```python
class SimpleSimilarity:
    """Text-based similarity for MVP"""

    def find_similar_nodes(self,
                          query_text: str,
                          dag: DebateDAG,
                          top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find nodes similar to query text

        Returns: List of (node_id, similarity_score)
        """

        query_words = self._get_content_words(query_text)
        scores = []

        for node_id, node in dag.nodes.items():
            node_text = f"{node.topic} {node.resolution} {' '.join(node.theme_tags)}"
            node_words = self._get_content_words(node_text)

            # Jaccard similarity
            intersection = query_words & node_words
            union = query_words | node_words
            similarity = len(intersection) / len(union) if union else 0

            scores.append((node_id, similarity))

        # Sort and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _get_content_words(self, text: str) -> Set[str]:
        """Extract content words (remove stop words)"""
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "this",
            "that", "these", "those", "it", "its", "you", "your", "we", "our"
        }

        words = text.lower().split()
        # Simple tokenization
        words = [w.strip('.,;:!?"()[]{}') for w in words]
        return {w for w in words if w and len(w) > 2 and w not in stop_words}
```

### 4.2 Future: Embedding-Based Similarity

```python
class EmbeddingSimilarity:
    """
    Embedding-based similarity using llm CLI

    NOTE: This is for Phase 3.5 or Phase 4, not MVP
    """

    def __init__(self):
        self.embedding_cache: Dict[str, List[float]] = {}

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text via llm CLI"""

        # Cache check
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]

        # Call llm CLI with embedding model
        import subprocess

        result = subprocess.run(
            ['llm', 'embed', '-m', 'text-embedding-3-small'],
            input=text,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output (should be JSON array)
        embedding = json.loads(result.stdout)
        self.embedding_cache[text_hash] = embedding

        return embedding

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        return dot_product / (mag1 * mag2) if mag1 and mag2 else 0

    def find_similar_nodes(self,
                          query_text: str,
                          dag: DebateDAG,
                          top_k: int = 5) -> List[Tuple[str, float]]:
        """Find nodes similar to query using embeddings"""

        query_embedding = self.get_embedding(query_text)
        scores = []

        for node_id, node in dag.nodes.items():
            # Get or compute node embedding
            if node._embedding is None:
                node_text = node.get_text_for_embedding()
                node._embedding = self.get_embedding(node_text)

            similarity = self.cosine_similarity(query_embedding, node._embedding)
            scores.append((node_id, similarity))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
```

### 4.3 Surfacing Related Nodes During Debates

```python
class ContextRetriever:
    """Retrieve relevant past nodes for current debate"""

    def __init__(self, dag: DebateDAG):
        self.dag = dag
        self.similarity = SimpleSimilarity()  # Or EmbeddingSimilarity

    def get_relevant_context(self,
                            passage: str,
                            current_turns: List['DebateTurn'],
                            max_nodes: int = 3) -> List[ArgumentNode]:
        """
        Get relevant nodes from the DAG for current debate

        Returns: List of ArgumentNodes to include in context
        """

        # Combine passage and recent turns for query
        recent_text = "\n".join(t.content for t in current_turns[-3:])
        query_text = f"{passage}\n\n{recent_text}"

        # Find similar nodes
        similar = self.similarity.find_similar_nodes(query_text, self.dag, top_k=max_nodes)

        # Return actual nodes
        return [self.dag.get_node(node_id) for node_id, score in similar
                if score > 0.3]  # Threshold

    def format_context_for_debate(self, nodes: List[ArgumentNode]) -> str:
        """Format relevant nodes as context for debate agents"""

        if not nodes:
            return ""

        context = "\n\nRELEVANT PAST DISCUSSIONS:\n"
        for node in nodes:
            context += f"\n- {node.topic}\n  → {node.resolution[:150]}...\n"

        return context
```

---

## 5. Linearization

### 5.1 Topological Sort

```python
class LinearizationEngine:
    """Convert DAG to readable linear narrative"""

    def __init__(self, dag: DebateDAG):
        self.dag = dag

    def topological_sort(self) -> List[str]:
        """
        Basic topological sort of nodes

        Returns: List of node_ids in sorted order
        """

        # Kahn's algorithm
        in_degree = {node_id: 0 for node_id in self.dag.nodes}

        # Count incoming edges (considering BRANCHES_FROM and other dependencies)
        for edge in self.dag.edges:
            if edge.edge_type in [EdgeType.BRANCHES_FROM, EdgeType.REQUIRES]:
                in_degree[edge.from_node_id] += 1

        # Queue of nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort by creation time for stable order
            queue.sort(key=lambda nid: self.dag.nodes[nid].created_at)
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for neighbors
            for edge in self.dag.get_outgoing_edges(current):
                if edge.edge_type in [EdgeType.BRANCHES_FROM, EdgeType.REQUIRES]:
                    in_degree[edge.to_node_id] -= 1
                    if in_degree[edge.to_node_id] == 0:
                        queue.append(edge.to_node_id)

        # If we didn't visit all nodes, there's a cycle (shouldn't happen in DAG)
        if len(result) != len(self.dag.nodes):
            # Fall back to chronological order
            return sorted(self.dag.nodes.keys(),
                         key=lambda nid: self.dag.nodes[nid].created_at)

        return result

    def render_as_markdown(self,
                          node_order: Optional[List[str]] = None) -> str:
        """
        Render the DAG as readable markdown document

        Args:
            node_order: Optional specific order, otherwise uses topological sort
        """

        if node_order is None:
            node_order = self.topological_sort()

        md = "# Dialectical Debate Graph\n\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        md += f"**Nodes:** {len(self.dag.nodes)}\n"
        md += f"**Edges:** {len(self.dag.edges)}\n\n"
        md += "---\n\n"

        for i, node_id in enumerate(node_order, 1):
            node = self.dag.get_node(node_id)
            if not node:
                continue

            # Node header
            md += f"## {i}. {node.topic}\n\n"
            md += f"*Type: {node.node_type.value} | "
            md += f"Created: {node.created_at.strftime('%Y-%m-%d %H:%M')}*\n\n"

            # Theme tags
            if node.theme_tags:
                md += f"**Tags:** {', '.join(sorted(node.theme_tags))}\n\n"

            # Source passage
            if node.source_passage:
                md += f"> {node.source_passage}\n\n"

            # Resolution
            md += f"**Resolution:**\n\n{node.resolution}\n\n"

            # Key claims
            if node.key_claims:
                md += "**Key Claims:**\n\n"
                for claim in node.key_claims:
                    md += f"- {claim}\n"
                md += "\n"

            # Relationships
            outgoing = self.dag.get_outgoing_edges(node_id)
            incoming = self.dag.get_incoming_edges(node_id)

            if outgoing or incoming:
                md += "**Relationships:**\n\n"

                if incoming:
                    md += "*Builds on:*\n"
                    for edge in incoming:
                        from_node = self.dag.get_node(edge.from_node_id)
                        md += f"- [{edge.edge_type.value}] {from_node.topic[:60]}...\n"
                    md += "\n"

                if outgoing:
                    md += "*Leads to:*\n"
                    for edge in outgoing:
                        to_node = self.dag.get_node(edge.to_node_id)
                        md += f"- [{edge.edge_type.value}] {to_node.topic[:60]}...\n"
                    md += "\n"

            # Optional: full transcript (collapsible)
            md += "<details>\n"
            md += f"<summary>Full Debate Transcript ({len(node.turns)} turns)</summary>\n\n"
            for turn in node.turns:
                md += f"**{turn.agent_name}** (Round {turn.round_num}):\n"
                md += f"{turn.content}\n\n"
            md += "</details>\n\n"

            md += "---\n\n"

        return md

    def render_chronological(self) -> str:
        """Render in chronological order (simpler, for debugging)"""

        node_order = sorted(self.dag.nodes.keys(),
                          key=lambda nid: self.dag.nodes[nid].created_at)
        return self.render_as_markdown(node_order)
```

---

## 6. Implementation Sequence

### Step-by-Step Build Order

**Week 1: Core Data Structures**

1. **Day 1-2:** Implement ArgumentNode, Edge, and DebateDAG classes
   - Write unit tests for basic operations
   - Test save/load functionality
   - Ensure integration with existing DebateTurn class

2. **Day 3:** Implement NodeCreationDetector
   - Test explicit completion markers
   - Test repetition detection
   - Test question-answer detection

3. **Day 4:** Implement NodeFactory
   - Test node creation from sample debates
   - Validate topic/resolution generation
   - Test tag extraction

**Week 2: Graph Building**

4. **Day 5:** Integrate with existing dialectic_poc.py
   - Modify main() to create DAG
   - Add nodes after main debate and branch debates
   - Create BRANCHES_FROM edges automatically

5. **Day 6:** Implement SimpleSimilarity
   - Test similarity scoring
   - Implement ContextRetriever
   - Test context injection into debates

6. **Day 7:** Implement EdgeDetector (basic)
   - Auto-detect CONTRADICTS edges
   - Auto-detect ELABORATES edges
   - Test edge suggestions

**Week 3: Linearization and Testing**

7. **Day 8:** Implement LinearizationEngine
   - Test topological sort
   - Test markdown rendering
   - Generate first full DAG document

8. **Day 9-10:** End-to-end testing
   - Run on multiple passages
   - Build DAG with 10+ nodes
   - Verify cross-references work

### MVP Deliverable

After 10 days, you should have:

```python
# Example usage:
from dialectic_poc import run_debate, identify_branch_point, run_branch_debate
from phase3_dag import DebateDAG, NodeFactory, EdgeDetector, LinearizationEngine

# Initialize
dag = DebateDAG()
factory = NodeFactory()
detector = EdgeDetector()

# Process first passage
passage1 = "When Zarathustra was thirty years old..."
main_transcript = run_debate(passage1, agents, rounds=3)

# Create node from main debate
main_node = factory.create_node_from_debate(main_transcript, passage1)
dag.add_node(main_node)

# Branch debate
branch_q = identify_branch_point(main_transcript, passage1)
branch_transcript = run_branch_debate(branch_q, agents, rounds=2)

# Create branch node
branch_node = factory.create_node_from_debate(branch_transcript, passage1, branch_q)
dag.add_node(branch_node)

# Connect them
branch_edge = Edge(
    from_node_id=branch_node.node_id,
    to_node_id=main_node.node_id,
    edge_type=EdgeType.BRANCHES_FROM,
    description=f"Explores: {branch_q}",
    detected_by="system"
)
dag.add_edge(branch_edge)

# Process second passage with context
passage2 = "Ten years he enjoyed his spirit and his solitude..."
relevant_nodes = context_retriever.get_relevant_context(passage2, [])
context_text = context_retriever.format_context_for_debate(relevant_nodes)

# Include context in debate system prompts
main_transcript2 = run_debate(passage2, agents, rounds=3, context=context_text)
# ... repeat node creation ...

# Export
dag.save(Path("debate_graph.json"))

# Linearize
linearizer = LinearizationEngine(dag)
markdown = linearizer.render_as_markdown()
with open("debate_narrative.md", 'w') as f:
    f.write(markdown)
```

---

## 7. Integration with Existing Code

### 7.1 Modifications to dialectic_poc.py

```python
# Add to dialectic_poc.py:

def run_debate_with_dag(
    passage: str,
    agents: List[Agent],
    dag: Optional[DebateDAG] = None,
    context_retriever: Optional[ContextRetriever] = None,
    rounds: int = 3,
    logger: Optional[Logger] = None
) -> Tuple[List[DebateTurn], ArgumentNode]:
    """
    Run debate and return both transcript and ArgumentNode

    If dag is provided, checks for relevant past nodes
    """

    # Get relevant context from DAG
    context_text = ""
    if dag and context_retriever:
        relevant_nodes = context_retriever.get_relevant_context(passage, [])
        if relevant_nodes:
            context_text = context_retriever.format_context_for_debate(relevant_nodes)
            if logger:
                logger.log(f"\n[Context] Found {len(relevant_nodes)} relevant past discussions")

    # Run debate (modify run_debate to accept context parameter)
    transcript = run_debate(passage, agents, rounds, logger=logger, context=context_text)

    # Create node
    factory = NodeFactory()
    node = factory.create_node_from_debate(transcript, passage)

    return transcript, node
```

### 7.2 Persistence Between Runs

```python
class DebateSession:
    """Manages persistent DAG across multiple passages"""

    def __init__(self, session_name: str, dag_path: Optional[Path] = None):
        self.session_name = session_name
        self.dag_path = dag_path or Path(f"{session_name}_graph.json")

        # Load existing DAG or create new
        if self.dag_path.exists():
            self.dag = DebateDAG.load(self.dag_path)
            print(f"Loaded existing DAG: {len(self.dag)} nodes")
        else:
            self.dag = DebateDAG()
            print("Created new DAG")

        self.factory = NodeFactory()
        self.detector = EdgeDetector()
        self.retriever = ContextRetriever(self.dag)

    def process_passage(self,
                       passage: str,
                       agents: List[Agent],
                       logger: Optional[Logger] = None) -> ArgumentNode:
        """Process a single passage and update DAG"""

        # Get relevant context
        relevant = self.retriever.get_relevant_context(passage, [])
        context_text = self.retriever.format_context_for_debate(relevant)

        # Run debate
        transcript, node = run_debate_with_dag(
            passage, agents, self.dag, self.retriever, logger=logger
        )

        # Add node to DAG
        self.dag.add_node(node)

        # Detect edges
        edges = self.detector.detect_edges_for_new_node(node, self.dag)
        for edge in edges:
            self.dag.add_edge(edge)

        # Save
        self.save()

        return node

    def process_branch(self,
                      branch_question: str,
                      parent_node_id: str,
                      agents: List[Agent],
                      logger: Optional[Logger] = None) -> ArgumentNode:
        """Process a branch debate"""

        # Run branch debate
        transcript = run_branch_debate(branch_question, agents, rounds=2, logger=logger)

        # Create node
        parent = self.dag.get_node(parent_node_id)
        branch_node = self.factory.create_node_from_debate(
            transcript, parent.source_passage, branch_question
        )

        # Add to DAG
        self.dag.add_node(branch_node)

        # Create branch edge
        branch_edge = Edge(
            from_node_id=branch_node.node_id,
            to_node_id=parent_node_id,
            edge_type=EdgeType.BRANCHES_FROM,
            description=f"Explores: {branch_question[:100]}",
            detected_by="system"
        )
        self.dag.add_edge(branch_edge)

        # Detect other edges
        edges = self.detector.detect_edges_for_new_node(branch_node, self.dag)
        for edge in edges:
            self.dag.add_edge(edge)

        self.save()

        return branch_node

    def save(self):
        """Save current DAG state"""
        self.dag.save(self.dag_path)

    def export_narrative(self, output_path: Optional[Path] = None):
        """Export linearized narrative"""
        output_path = output_path or Path(f"{self.session_name}_narrative.md")

        linearizer = LinearizationEngine(self.dag)
        markdown = linearizer.render_as_markdown()

        with open(output_path, 'w') as f:
            f.write(markdown)

        print(f"Narrative exported to: {output_path}")
```

### 7.3 Incremental Building Example

```python
# New main() for Phase 3:

def main_phase3():
    """Phase 3: Build persistent DAG across multiple passages"""

    # Create session
    session = DebateSession("zarathustra_reading")

    # Initialize logger
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = Logger(f"phase3_log_{timestamp}.md")

    # Agents
    agents = [
        Agent("The Literalist", "Focus on what literally happened", "..."),
        Agent("The Symbolist", "Everything is metaphor", "..."),
        Agent("The Structuralist", "Universal narrative patterns", "...")
    ]

    # Passages to process
    passages = [
        "When Zarathustra was thirty years old, he left his home...",
        "Ten years he enjoyed his spirit and his solitude...",
        "At last his heart transformed, and one morning he rose with the dawn..."
    ]

    # Process each passage
    for i, passage in enumerate(passages, 1):
        logger.log_section(f"PASSAGE {i}")
        logger.log(passage)

        # Main debate
        node = session.process_passage(passage, agents, logger)
        logger.log(f"\nCreated node: {node.node_id} ({node.node_type.value})")

        # Optional: branch debate
        if i == 1:  # Branch on first passage
            branch_q = "What is the significance of 'thirty years'?"
            branch_node = session.process_branch(branch_q, node.node_id, agents, logger)
            logger.log(f"\nCreated branch: {branch_node.node_id}")

    # Export narrative
    session.export_narrative()

    logger.finalize()
    print(f"\nSession saved: {session.dag_path}")
    print(f"DAG contains {len(session.dag)} nodes, {len(session.dag.edges)} edges")

if __name__ == "__main__":
    main_phase3()
```

---

## 8. What to Defer to Later

### Phase 3.5 (Optional Enhancements)

- **Embedding-based similarity** - Requires embedding API access
- **Advanced edge detection** - SUPPORTS, REQUIRES, ANALOGY edge types
- **Manual edge management UI** - Accept/reject suggested edges
- **Node merging** - Combine redundant nodes

### Phase 4 (Multi-Text Reading)

- **Memory compression** - Summarize old nodes to save context
- **Cross-text references** - Link nodes across different books
- **User annotation integration** - Include user notes in nodes
- **Adaptive agent generation** - Meta-learning from feedback

### Phase 5 (UI and Polish)

- **Interactive graph visualization** - D3.js or similar
- **Better linearization** - Narrative flow optimization
- **Search and filter** - Query language for nodes
- **Export formats** - PDF, Obsidian, etc.

---

## 9. Testing Strategy

### Unit Tests

```python
# test_phase3.py

import pytest
from phase3_dag import ArgumentNode, Edge, DebateDAG, NodeType, EdgeType
from dialectic_poc import DebateTurn

def test_node_creation():
    """Test creating an ArgumentNode"""
    turns = [
        DebateTurn("Alice", "This is literal", 1),
        DebateTurn("Bob", "No, it's symbolic", 1),
        DebateTurn("Alice", "We disagree fundamentally", 2),
        DebateTurn("Bob", "Indeed, an impasse", 2)
    ]

    node = ArgumentNode(
        node_type=NodeType.IMPASSE,
        topic="Literal vs symbolic interpretation",
        turns=turns,
        resolution="Irreconcilable disagreement about interpretive framework",
        source_passage="Test passage"
    )

    assert node.node_id
    assert len(node.turns) == 4
    assert node.node_type == NodeType.IMPASSE

def test_dag_operations():
    """Test basic DAG operations"""
    dag = DebateDAG()

    # Add nodes
    node1 = ArgumentNode(
        node_type=NodeType.EXPLORATION,
        topic="Topic 1",
        turns=[],
        resolution="Resolution 1"
    )
    node2 = ArgumentNode(
        node_type=NodeType.SYNTHESIS,
        topic="Topic 2",
        turns=[],
        resolution="Resolution 2"
    )

    dag.add_node(node1)
    dag.add_node(node2)

    assert len(dag) == 2

    # Add edge
    edge = Edge(
        from_node_id=node2.node_id,
        to_node_id=node1.node_id,
        edge_type=EdgeType.ELABORATES
    )
    dag.add_edge(edge)

    assert len(dag.edges) == 1
    assert len(dag.get_outgoing_edges(node2.node_id)) == 1

def test_persistence():
    """Test save/load"""
    from pathlib import Path
    import tempfile

    dag = DebateDAG()
    node = ArgumentNode(
        node_type=NodeType.LEMMA,
        topic="Test topic",
        turns=[DebateTurn("A", "Content", 1)],
        resolution="Test resolution"
    )
    dag.add_node(node)

    # Save
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_graph.json"
        dag.save(path)

        # Load
        loaded_dag = DebateDAG.load(path)

        assert len(loaded_dag) == 1
        loaded_node = loaded_dag.get_node(node.node_id)
        assert loaded_node.topic == "Test topic"
        assert len(loaded_node.turns) == 1
```

### Integration Tests

```python
def test_end_to_end():
    """Test complete workflow"""
    from dialectic_poc import Agent, run_debate

    passage = "Test passage for debate"
    agents = [
        Agent("A", "Stance A", "Focus A"),
        Agent("B", "Stance B", "Focus B")
    ]

    # Create session
    session = DebateSession("test_session")

    # Process passage
    node = session.process_passage(passage, agents)

    assert node.node_id in session.dag.nodes
    assert len(session.dag) == 1

    # Process another
    node2 = session.process_passage("Second passage", agents)

    assert len(session.dag) >= 2

    # Export narrative
    session.export_narrative(Path("test_narrative.md"))
```

---

## 10. Success Criteria

**Phase 3 is successful if:**

1. **Graph builds incrementally** - Can process 10+ passages, accumulating nodes
2. **Context works** - New debates reference relevant past nodes
3. **Edges make sense** - Relationships between nodes are valid
4. **Linearization is readable** - Output document tells coherent story
5. **Persistence works** - Can save and resume sessions

**Red flags that indicate problems:**

- Every debate becomes a node (too granular)
- No nodes are created (detector too conservative)
- All nodes have same type (detector not working)
- No edges detected (detector too strict)
- Context retrieval returns irrelevant nodes
- Linearization is unreadable jumble

---

## 11. Implementation Checklist

### Core Infrastructure
- [ ] ArgumentNode class with all fields
- [ ] NodeType enum
- [ ] Edge class with all fields
- [ ] EdgeType enum
- [ ] DebateDAG class with basic operations
- [ ] Save/load functionality
- [ ] Unit tests for data structures

### Node Creation
- [ ] NodeCreationDetector class
- [ ] Explicit completion marker detection
- [ ] Repetition detection
- [ ] Question-answer detection
- [ ] NodeFactory class
- [ ] Topic generation
- [ ] Resolution generation
- [ ] Tag extraction
- [ ] Key claims extraction
- [ ] Tests for node creation

### Edge Detection
- [ ] EdgeDetector class
- [ ] BRANCHES_FROM edge creation (automatic)
- [ ] CONTRADICTS detection
- [ ] ELABORATES detection
- [ ] Manual edge suggestions
- [ ] Tests for edge detection

### Similarity & Context
- [ ] SimpleSimilarity class
- [ ] Content word extraction
- [ ] Similarity scoring
- [ ] ContextRetriever class
- [ ] Context formatting for debates
- [ ] Tests for similarity

### Linearization
- [ ] LinearizationEngine class
- [ ] Topological sort implementation
- [ ] Markdown rendering
- [ ] Chronological rendering
- [ ] Tests for linearization

### Integration
- [ ] Modify dialectic_poc.py for context parameter
- [ ] run_debate_with_dag() function
- [ ] DebateSession class
- [ ] process_passage() method
- [ ] process_branch() method
- [ ] Integration tests

### End-to-End
- [ ] Process 3+ passages in sequence
- [ ] Verify context retrieval works
- [ ] Verify cross-references appear
- [ ] Export readable narrative
- [ ] Demo on actual Nietzsche text

---

## Conclusion

This implementation plan provides a **concrete, step-by-step path** to building Phase 3's graph structure. The key principles:

1. **Start simple** - Text similarity before embeddings, explicit markers before ML
2. **Test incrementally** - Each component tested in isolation
3. **Integrate gradually** - Build on existing Phase 0/2 code
4. **Defer complexity** - Advanced features to later phases

**Timeline:** 10 days for MVP, 2-3 weeks for robust implementation.

**First step:** Implement ArgumentNode and DebateDAG classes, get save/load working.

**Success looks like:** Processing 10 passages from Nietzsche, building a DAG with 15-20 nodes, exporting a readable narrative that shows how ideas connect across the text.
