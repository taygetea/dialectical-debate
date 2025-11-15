# Phase 3 Quick Reference

## Core Concepts

**ArgumentNode** = A semantically complete debate segment (not individual turns)
- Types: Synthesis, Impasse, Lemma, Question, Exploration, Clarification
- Contains: topic, turns, resolution, tags, claims

**Edge** = Typed relationship between nodes
- Types: Supports, Contradicts, Elaborates, Requires, AppliesTo, Analogy, BranchesFrom

**DAG** = Directed Acyclic Graph storing all nodes and edges

## The Hard Problem

**When does a sequence of DebateTurns become an ArgumentNode?**

MVP Solutions:
1. Explicit markers ("we agree that...", "fundamental disagreement")
2. Question-answer completion (for branch debates)
3. Repetition detection (circular arguments)
4. Max turn limit (force completion)

## MVP Architecture

```
DebateSession
    ├── DebateDAG (nodes + edges)
    ├── NodeFactory (creates nodes from transcripts)
    ├── EdgeDetector (finds relationships)
    ├── ContextRetriever (finds relevant past nodes)
    └── LinearizationEngine (renders as narrative)
```

## Key Classes

### ArgumentNode
```python
ArgumentNode(
    node_type: NodeType,
    topic: str,              # 1-2 sentence summary
    turns: List[DebateTurn], # Full transcript
    resolution: str,         # Paragraph summary
    theme_tags: Set[str],    # ["free-will", "causation"]
    key_claims: List[str]    # Main assertions
)
```

### Edge
```python
Edge(
    from_node_id: str,
    to_node_id: str,
    edge_type: EdgeType,
    description: Optional[str],
    confidence: float
)
```

### DebateDAG
```python
dag = DebateDAG()
dag.add_node(node)
dag.add_edge(edge)
dag.find_nodes_by_topic("free will")
dag.save(Path("graph.json"))
```

## Workflow

### Single Passage
```python
session = DebateSession("my_reading")

# Process passage
node = session.process_passage(passage, agents, logger)
# → Automatically: finds relevant context, runs debate, creates node, detects edges

# Optional branch
branch_node = session.process_branch(question, parent_node_id, agents, logger)

# Export
session.export_narrative()
```

### Context Retrieval
```python
retriever = ContextRetriever(dag)

# Get relevant nodes for new passage
relevant = retriever.get_relevant_context(passage, current_turns)

# Format for debate
context_text = retriever.format_context_for_debate(relevant)
# → Injected into agent system prompts
```

### Linearization
```python
linearizer = LinearizationEngine(dag)
node_order = linearizer.topological_sort()
markdown = linearizer.render_as_markdown(node_order)
```

## Implementation Priority

### Week 1: Data Structures
- ArgumentNode, Edge, DebateDAG classes
- Save/load functionality
- NodeCreationDetector
- NodeFactory

### Week 2: Graph Building
- Integration with dialectic_poc.py
- SimpleSimilarity + ContextRetriever
- EdgeDetector basics
- BRANCHES_FROM edges (automatic)

### Week 3: Linearization
- LinearizationEngine
- Topological sort
- Markdown rendering
- End-to-end testing

## MVP Features

**Include:**
- Text-based similarity (not embeddings)
- Explicit completion markers
- BRANCHES_FROM, CONTRADICTS, ELABORATES edges
- Topological sort linearization
- JSON persistence

**Defer:**
- Embedding-based similarity
- SUPPORTS, REQUIRES, ANALOGY edges
- Memory compression
- Interactive UI
- Cross-text references

## Testing Checklist

- [ ] Create node from debate transcript
- [ ] Detect completion via explicit markers
- [ ] Detect repetition/circular arguments
- [ ] Save and load DAG
- [ ] Find similar nodes via text overlap
- [ ] Retrieve relevant context
- [ ] Auto-detect CONTRADICTS edges
- [ ] Topological sort works
- [ ] Markdown rendering readable
- [ ] Process 10+ passages incrementally

## Success Criteria

**Phase 3 succeeds if:**
1. Graph builds incrementally across passages
2. New debates reference relevant past nodes
3. Edges connect related ideas
4. Linearized output is readable
5. Session persists across runs

**Red flags:**
- Every turn becomes a node
- No nodes created
- All same type
- No edges detected
- Irrelevant context retrieved

## File Structure

```
dialectic_poc.py          # Existing Phase 0/2 code
phase3_dag.py             # New: ArgumentNode, Edge, DebateDAG
phase3_nodes.py           # New: NodeCreationDetector, NodeFactory
phase3_edges.py           # New: EdgeDetector
phase3_similarity.py      # New: SimpleSimilarity, ContextRetriever
phase3_linearize.py       # New: LinearizationEngine
phase3_session.py         # New: DebateSession
test_phase3.py            # Tests
```

## Example Usage

```python
from phase3_session import DebateSession
from dialectic_poc import Agent

# Initialize
session = DebateSession("zarathustra")
agents = [Agent("Literalist", ...), Agent("Symbolist", ...)]

# Process passages
passages = ["When Zarathustra was thirty...", "Ten years he enjoyed..."]

for passage in passages:
    node = session.process_passage(passage, agents)
    print(f"Created: {node.topic}")

# Export
session.export_narrative(Path("zarathustra_narrative.md"))
print(f"DAG: {len(session.dag)} nodes, {len(session.dag.edges)} edges")
```

## Node Creation Heuristics

**Creates SYNTHESIS when:**
- "We agree that..."
- "Common ground..."
- "Both perspectives show..."

**Creates IMPASSE when:**
- "Fundamental disagreement"
- "Irreconcilable"
- "Cannot reconcile"

**Creates QUESTION when:**
- Branch debate question answered
- Multiple perspectives explored

**Creates EXPLORATION when:**
- Max turns reached
- No clear resolution
- Default fallback

## Edge Detection

**BRANCHES_FROM (automatic):**
- Created when branch debate spawned from parent

**CONTRADICTS (auto-detected):**
- Both nodes are IMPASSE
- Share 2+ theme tags
- Confidence: 0.6

**ELABORATES (auto-detected):**
- Share 3+ theme tags
- Newer node elaborates older
- Confidence: 0.5

## Similarity Scoring (MVP)

Simple Jaccard similarity:
1. Extract content words (remove stop words)
2. Compare word sets
3. score = |intersection| / |union|
4. Threshold: 0.3 for relevance

## Next Steps After MVP

1. Add embeddings for better similarity
2. Implement more edge types
3. Build interactive graph viewer
4. Add memory compression
5. Support multiple books
6. User feedback loop
