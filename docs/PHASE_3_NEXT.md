# Phase 3: What to Build Next

**Goal:** Transform from linear transcripts to semantic knowledge graph

**Status:** Planning complete, ready for implementation

**Estimated Timeline:** 10 days MVP, 2-3 weeks robust

---

## Quick Overview

### Current State (Phases 0-2 Complete)

```
Passage → Debate → Branch → Synthesis → Markdown output
              ↓
         (forgotten after run)
```

**Problem:** Each passage processed independently, no accumulated knowledge, no cross-reference.

### Target State (Phase 3)

```
Passage → Debate → ArgumentNode → DebateDAG
                        ↓
              (persistent graph)
                        ↓
Next Passage → Find relevant context → Enhanced debate → New nodes
```

**Solution:** Debates become nodes in a graph, enabling context retrieval and narrative generation.

---

## Core Concepts

### ArgumentNode

**Not** individual turns. **Semantic completion units** - debates that reached a resolution point.

**Types:**
- **Synthesis:** Agents reached agreement
- **Impasse:** Fundamental disagreement, can't resolve
- **Lemma:** Established sub-point for larger argument
- **Question:** Posed question awaiting answer
- **Exploration:** Investigated topic without resolution
- **Clarification:** Refined understanding of specific point

**Contains:**
```python
ArgumentNode(
    node_id: str,                  # Unique identifier
    node_type: NodeType,           # Synthesis, Impasse, etc.
    topic: str,                    # 1-2 sentence summary
    turns: List[DebateTurn],       # Full transcript
    resolution: str,               # Paragraph summary of outcome
    theme_tags: Set[str],          # ["free-will", "causation", "agency"]
    key_claims: List[str],         # Main assertions made
    created_at: datetime
)
```

### Edge

**Typed relationship between nodes**

**Types (MVP - implement these 3 first):**
- **BRANCHES_FROM:** Branch debate from main debate
- **CONTRADICTS:** Direct opposition
- **ELABORATES:** Expands on previous point

**Deferred to later:**
- SUPPORTS, REQUIRES, APPLIES_TO, ANALOGY

**Contains:**
```python
Edge(
    from_node_id: str,
    to_node_id: str,
    edge_type: EdgeType,
    description: Optional[str],    # Human-readable explanation
    confidence: float              # 0.0-1.0
)
```

### DebateDAG

**The graph itself**

**Core operations:**
```python
dag = DebateDAG()

# Add
dag.add_node(node)
dag.add_edge(edge)

# Query
nodes = dag.find_nodes_by_topic("free will")
nodes = dag.find_nodes_by_tags({"causation", "agency"})
relevant = dag.find_similar_nodes(passage, top_k=5)

# Persist
dag.save(Path("my_reading.json"))
dag = DebateDAG.load(Path("my_reading.json"))

# Render
narrative = dag.linearize()  # Topological sort → markdown
```

---

## The Hard Problem: Node Boundaries

**Question:** When does a sequence of DebateTurns become an ArgumentNode?

### MVP Solution (4 detection methods)

**1. Explicit completion markers**
```python
# Look for phrases like:
- "we agree that..."
- "fundamental disagreement..."
- "this resolves to..."
- "the tension remains between..."
```

**2. Question-answer completion**
```python
# For branch debates:
- Branch started with question Q
- Debate produced answer/synthesis
- Question resolved → create node
```

**3. Repetition detection**
```python
# Circular arguments:
- Agents repeating same points
- No new concepts introduced
- Stuck in loop → create Impasse node
```

**4. Max turn limit**
```python
# Fallback:
- Debate reaches N turns (e.g., 10)
- Force completion
- Create Exploration node
```

### Detection Workflow

```python
detector = NodeCreationDetector()

for turn in new_turns:
    transcript.append(turn)

    if detector.check_completion(transcript):
        node_type = detector.classify_resolution(transcript)
        node = NodeFactory.create_node(node_type, transcript)
        dag.add_node(node)
        break
```

---

## Implementation Sequence

### Week 1: Core Data Structures (Days 1-4)

**Day 1-2: ArgumentNode + Edge + DebateDAG**

Create `phase3_dag.py`:
```python
class NodeType(Enum):
    SYNTHESIS = "synthesis"
    IMPASSE = "impasse"
    LEMMA = "lemma"
    QUESTION = "question"
    EXPLORATION = "exploration"
    CLARIFICATION = "clarification"

class ArgumentNode:
    # Implementation from docs/phase3_implementation_plan.md

class EdgeType(Enum):
    BRANCHES_FROM = "branches_from"
    CONTRADICTS = "contradicts"
    ELABORATES = "elaborates"
    # Defer: SUPPORTS, REQUIRES, APPLIES_TO, ANALOGY

class Edge:
    # Implementation from plan

class DebateDAG:
    nodes: Dict[str, ArgumentNode]
    edges: List[Edge]

    def add_node(node) / add_edge(edge)
    def find_nodes_by_topic(topic: str)
    def find_nodes_by_tags(tags: Set[str])
    def save(path) / load(path)  # JSON serialization
```

**Day 3: Node Creation Logic**

Create `phase3_nodes.py`:
```python
class NodeCreationDetector:
    """Detects when debate reaches semantic completion"""

    def check_completion(self, transcript: List[DebateTurn]) -> bool:
        # Check all 4 methods:
        # 1. Explicit markers
        # 2. Question answered (for branches)
        # 3. Repetition detected
        # 4. Max turns reached

    def classify_resolution(self, transcript) -> NodeType:
        # Determine type: Synthesis, Impasse, etc.

class NodeFactory:
    """Creates ArgumentNodes from transcripts"""

    @staticmethod
    def create_node(node_type: NodeType,
                   transcript: List[DebateTurn],
                   passage: str = None) -> ArgumentNode:
        # Use LLM to generate:
        # - topic (1-2 sentence summary)
        # - resolution (paragraph summary)
        # - theme_tags (extract key concepts)
        # - key_claims (main assertions)
```

**Day 4: Testing + JSON Persistence**
- Test creating nodes from existing debate transcripts
- Test save/load functionality
- Validate JSON format

---

### Week 2: Graph Building (Days 5-7)

**Day 5: Context Retrieval**

Create `phase3_similarity.py`:

**Decision Point: Which approach?**

**Option 1: Simple Text Similarity (MVP)**
```python
class SimpleSimilarity:
    """Text-based Jaccard similarity (no embeddings)"""

    def compute_similarity(node: ArgumentNode, passage: str) -> float:
        # Jaccard distance on word sets
        # Fast, no external dependencies

class ContextRetriever:
    def __init__(self, dag: DebateDAG):
        self.dag = dag
        self.similarity = SimpleSimilarity()

    def get_relevant_context(self, passage: str,
                            current_turns: List[DebateTurn],
                            top_k: int = 5) -> List[ArgumentNode]:
        # Find similar nodes
        # Return top-k most relevant

    def format_context_for_debate(self, nodes: List[ArgumentNode]) -> str:
        # Format as text to inject into agent system prompts
        # "Previous relevant discussions:..."
```

**Option 2: Full Backlog (Alternative MVP)**
```python
class FullContextRetriever:
    """Just include entire graph (for small corpora)"""

    def get_all_context(self, dag: DebateDAG) -> List[ArgumentNode]:
        # Return all nodes
        # Modern LLMs have 200K+ context

    def format_for_debate(self, nodes: List[ArgumentNode]) -> str:
        # Format entire graph
        # Let LLM find what's relevant
```

**Recommendation:** Start with Option 1 (SimpleSimilarity), fall back to Option 2 if similarity doesn't work well.

**Day 6: Edge Detection**

Create `phase3_edges.py`:
```python
class EdgeDetector:
    """Detects relationships between nodes"""

    def detect_branches_from(self, dag: DebateDAG) -> List[Edge]:
        # Automatic: branch nodes have parent reference
        # Easy to detect

    def detect_contradictions(self, dag: DebateDAG) -> List[Edge]:
        # Pattern matching:
        # - Look for "contradicts", "opposes", "disagrees with"
        # - Check if key claims directly oppose
        # - Confidence based on strength of opposition

    def detect_elaborations(self, dag: DebateDAG) -> List[Edge]:
        # Pattern matching:
        # - "builds on", "extends", "develops"
        # - Topic similarity + sequential ordering
        # - Confidence based on semantic overlap
```

**Day 7: Integration with dialectic_poc.py**

Create `phase3_session.py`:
```python
class DebateSession:
    """Orchestrates graph-building debates"""

    def __init__(self, session_name: str):
        self.dag = DebateDAG()
        self.retriever = ContextRetriever(self.dag)
        self.edge_detector = EdgeDetector()
        self.session_name = session_name

    def process_passage(self, passage: str,
                       agents: List[Agent],
                       logger: Logger) -> ArgumentNode:
        """Process passage with context retrieval"""

        # 1. Get relevant context
        relevant_nodes = self.retriever.get_relevant_context(passage)

        # 2. Format context for agents
        context = self.retriever.format_context_for_debate(relevant_nodes)

        # 3. Run debate with context-enhanced prompts
        transcript = run_debate_with_context(
            passage, agents, context, logger
        )

        # 4. Create node
        node = NodeFactory.create_node(
            NodeType.EXPLORATION,  # Or detect type
            transcript,
            passage
        )

        # 5. Add to graph
        self.dag.add_node(node)

        # 6. Detect edges
        new_edges = self.edge_detector.detect_edges(self.dag, node)
        for edge in new_edges:
            self.dag.add_edge(edge)

        # 7. Save
        self.dag.save(Path(f"{self.session_name}.json"))

        return node

    def process_branch(self, branch_question: str,
                      parent_node_id: str,
                      agents: List[Agent],
                      logger: Logger) -> ArgumentNode:
        """Process branch with automatic BRANCHES_FROM edge"""

        # Similar to process_passage but:
        # - Create branch node
        # - Automatically add BRANCHES_FROM edge to parent
        # - Detect other edge types

    def export_narrative(self, output_file: str):
        """Export linearized narrative"""
        # Call linearization engine (Week 3)
```

---

### Week 3: Linearization + Testing (Days 8-10)

**Day 8-9: Linearization Engine**

Create `phase3_linearize.py`:
```python
class LinearizationEngine:
    """Convert graph to readable narrative"""

    def __init__(self, dag: DebateDAG):
        self.dag = dag

    def topological_sort(self) -> List[str]:
        """Order nodes respecting dependencies (Kahn's algorithm)"""
        # Return list of node_ids in dependency order
        # Handle cycles gracefully (fallback to chronological)

    def render_as_markdown(self, node_order: List[str]) -> str:
        """Generate markdown narrative"""
        # For each node:
        # - Header with topic
        # - Summary (resolution)
        # - Collapsible full transcript
        # - Incoming/outgoing edges
        # - Tags and key claims

    def create_table_of_contents(self) -> str:
        """Generate TOC with hyperlinks"""

    def export(self, output_path: Path):
        """Write to file"""
```

**Example markdown output:**
```markdown
# Debate Session: Nietzsche Reading

Generated: 2025-11-15
Nodes: 12
Edges: 18

## Table of Contents
1. [Zarathustra's Departure](#node-1)
2. [Meaning of "Thirty Years"](#node-2)
3. [...](#node-3)

---

## 1. Zarathustra's Departure {#node-1}

**Type:** Exploration
**Tags:** #departure #transformation #mountains
**Edges:** → Branches to [2](#node-2), [5](#node-5)

**Summary:**
Three interpretations emerged: literal biographical event, symbolic psychological transformation, and structural narrative pattern. Unresolved tension about where meaning resides.

**Key Claims:**
- Literalist: "Departure occurred at specific age from specific location"
- Symbolist: "Mountains represent ascent toward higher consciousness"
- Structuralist: "Deploys archetypal withdrawal motif"

<details>
<summary>Full Transcript (3 rounds, 9 turns)</summary>

### Round 1
**The Literalist:**
[full turn text]
...

</details>

---

## 2. Meaning of "Thirty Years" {#node-2}

**Type:** Question → Synthesis
**Tags:** #age #maturity #threshold
**Edges:** ← Branches from [1](#node-1), → Elaborated by [4](#node-4)

**Summary:**
Branch debate resolved that "thirty" functions simultaneously as biographical fact, psychological threshold, and genre marker. Not mutually exclusive readings.

...
```

**Day 10: End-to-End Testing**
- Process 10+ passages
- Verify graph builds correctly
- Test context retrieval works
- Validate linearization output
- Compare to `docs/phase3_example_walkthrough.md`

---

## Context Retrieval: The Decision

**Critical design choice:** How to provide context to new debates?

### Option 1: Embedding-Based RAG (Traditional)

**Pros:**
- Scales to large corpora (100s-1000s of passages)
- Precise relevance ranking
- Standard approach

**Cons:**
- Requires embedding infrastructure
- Extra API calls or local model
- Complexity

**Implementation:**
```python
# Compute embeddings
for node in dag.nodes:
    node.embedding = get_embedding(node.topic + node.resolution)

# Retrieve
query_embedding = get_embedding(new_passage)
similarities = cosine_similarity(query_embedding, all_embeddings)
top_nodes = get_top_k(similarities)
```

### Option 2: Full Backlog in Context (Modern)

**Pros:**
- Extremely simple
- No embedding infrastructure
- Let LLM find what's relevant
- Works for 10-100 passages easily (fits in 200K context)

**Cons:**
- Doesn't scale to massive corpora
- Wastes context on irrelevant nodes
- Higher cost per call

**Implementation:**
```python
# Just include everything
all_nodes = dag.get_all_nodes()
context = format_all_nodes(all_nodes)
# Let LLM filter what's relevant
```

### Recommendation: Start with Option 2

**Rationale:**
- Simpler to implement
- Good enough for MVP (most people won't process 100+ passages)
- Can add embeddings later if needed
- Modern LLMs are good at finding relevant context

**Migration path:**
```python
class ContextRetriever:
    def __init__(self, dag, strategy="full"):
        self.strategy = strategy  # "full" or "embedding"

    def get_relevant_context(self, passage):
        if self.strategy == "full":
            return self.dag.get_all_nodes()
        elif self.strategy == "embedding":
            return self.embedding_search(passage)
```

---

## Success Criteria

Phase 3 successful if:

✅ **Graph builds incrementally**
- Process passage 1 → creates node 1
- Process passage 2 → creates node 2 + edges
- Process passage 3 → creates node 3 + edges + finds relevant context from 1,2

✅ **Context retrieval works**
- New debates reference relevant past nodes
- Agents say things like "As we discussed in [previous passage]..."
- Context injection improves debate quality

✅ **Edges connect related ideas**
- BRANCHES_FROM edges automatic and correct
- CONTRADICTS/ELABORATES edges detected with >70% accuracy
- Manual validation shows sensible relationships

✅ **Linearization readable**
- Topological sort produces coherent ordering
- Markdown output navigable
- TOC links work

✅ **Persistence works**
- Save → load → continue session
- JSON format human-readable
- No data loss

---

## Testing Strategy

### Unit Tests

```python
# test_phase3.py

def test_node_creation():
    # Create node from transcript
    # Verify all fields populated

def test_completion_detection():
    # Test all 4 detection methods
    # Explicit markers, Q&A, repetition, max turns

def test_edge_detection():
    # Create mock nodes with relationships
    # Verify edges detected correctly

def test_similarity():
    # Compute similarity between known-related nodes
    # Should be > 0.7

def test_topological_sort():
    # Create graph with dependencies
    # Verify sort respects ordering
```

### Integration Tests

```python
def test_end_to_end():
    """Process 3 passages, verify graph"""

    session = DebateSession("test")

    # Passage 1
    node1 = session.process_passage(passage1, agents, logger)
    assert len(session.dag.nodes) == 1

    # Passage 2
    node2 = session.process_passage(passage2, agents, logger)
    assert len(session.dag.nodes) == 2
    # Should have created edges
    assert len(session.dag.edges) > 0

    # Passage 3 with branch
    node3 = session.process_passage(passage3, agents, logger)
    branch_node = session.process_branch(question, node3.node_id, agents, logger)

    # Verify structure
    assert len(session.dag.nodes) == 4
    # Branch should have BRANCHES_FROM edge
    branches = [e for e in session.dag.edges if e.edge_type == EdgeType.BRANCHES_FROM]
    assert len(branches) >= 1

    # Verify persistence
    session.dag.save(Path("test.json"))
    loaded = DebateDAG.load(Path("test.json"))
    assert len(loaded.nodes) == len(session.dag.nodes)

    # Verify linearization
    narrative = session.export_narrative()
    assert len(narrative) > 0
    assert "Table of Contents" in narrative
```

### Validation Against Example

Compare output to `docs/phase3_example_walkthrough.md`:
- Same 3 Nietzsche passages
- Should produce similar node count (±1)
- Should detect similar edges
- Linearized output should be comparable quality

---

## Files to Create

```
src/phase3_dag.py              # ArgumentNode, Edge, DebateDAG
src/phase3_nodes.py            # NodeCreationDetector, NodeFactory
src/phase3_edges.py            # EdgeDetector
src/phase3_similarity.py       # SimpleSimilarity, ContextRetriever
src/phase3_linearize.py        # LinearizationEngine
src/phase3_session.py          # DebateSession (main orchestrator)
tests/test_phase3.py           # Unit + integration tests
```

---

## Next Steps

1. **Read detailed plan:** `docs/phase3_implementation_plan.md`
2. **Review example:** `docs/phase3_example_walkthrough.md`
3. **Start coding:** Begin with `phase3_dag.py`
4. **Test incrementally:** Don't build everything before testing
5. **Reference architecture:** `docs/phase3_architecture_diagram.md`

---

## Questions to Resolve

### During Implementation

1. **Node boundary detection:** Will the 4 methods be sufficient? May need to tune.
2. **Context format:** How to inject past nodes into agent prompts? System prompt vs user prompt?
3. **Edge confidence:** How to calibrate confidence scores?
4. **Cycle handling:** What if graph has cycles? (Shouldn't in MVP, but possible)
5. **Performance:** Will full-context approach be too slow? May need to switch to embeddings sooner.

### Design Decisions

Document these in `docs/DESIGN_DECISIONS.md` as you make them.

---

**Ready to start?** Begin with Week 1, Day 1: Create `src/phase3_dag.py` with ArgumentNode, Edge, and DebateDAG classes.
