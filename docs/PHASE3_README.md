# Phase 3: Graph Structure Implementation - Documentation Index

**Created:** 2025-11-15
**Status:** Planning Complete, Ready for Implementation
**Estimated Timeline:** 10 days MVP, 2-3 weeks robust implementation

---

## Overview

Phase 3 transforms the dialectical debate system from linear transcript generation into a **semantic graph** that can accumulate knowledge across multiple passages, cross-reference ideas, and present coherent narratives.

**Current State:**
- ✅ Phase 0: Working debate generation with branching
- ✅ Phase 2: Automated observer generation
- 🔨 Phase 3: Graph structure (this phase)

**Core Innovation:**
Transform sequences of DebateTurns into ArgumentNodes (semantic completion units) connected by typed edges, enabling:
- Context retrieval from past debates
- Cross-referencing of related ideas
- Linearization into readable narrative
- Persistent knowledge accumulation

---

## Documentation Files

### 1. **phase3_implementation_plan.md** (56KB)
**The main reference document** - Complete implementation specification

**Contents:**
- Data structures (ArgumentNode, Edge, DAG)
- Node creation strategy (detecting semantic completion)
- Edge detection algorithms
- Similarity and context retrieval
- Linearization (topological sort)
- Step-by-step implementation sequence
- Integration with existing code
- Testing strategy
- Success criteria
- Complete code examples

**Use this for:** Detailed implementation guidance, understanding design decisions

---

### 2. **phase3_quick_reference.md** (6KB)
**Quick lookup guide** - Essential concepts and patterns

**Contents:**
- Core concepts at a glance
- Key class signatures
- Workflow diagrams
- Implementation priorities
- MVP feature checklist
- Common patterns

**Use this for:** Quick lookups while coding, refreshing memory on APIs

---

### 3. **phase3_architecture_diagram.md** (20KB)
**Visual system architecture** - Diagrams and flow charts

**Contents:**
- System overview diagram
- Data flow visualizations
- Component dependency graph
- Algorithm flowcharts
- Persistence format
- Example graph structures

**Use this for:** Understanding system structure, debugging flow issues

---

### 4. **phase3_example_walkthrough.md** (25KB)
**Concrete working example** - Step-by-step execution trace

**Contents:**
- Complete example processing 3 Nietzsche passages
- Detailed trace of each step (context retrieval → debate → node creation → edge detection)
- Actual node/edge creation with content
- Final linearized output
- Query examples

**Use this for:** Understanding how components work together, validation testing

---

## Quick Start

### For Implementation

1. **Read first:** `phase3_implementation_plan.md` sections 1-2 (Data Structures, Node Creation)
2. **Start coding:** Begin with Week 1, Day 1-2 tasks
3. **Reference:** Use `phase3_quick_reference.md` for API signatures
4. **Validate:** Compare output to `phase3_example_walkthrough.md`

### For Understanding the System

1. **Read first:** This file (overview)
2. **Visualize:** `phase3_architecture_diagram.md` (system structure)
3. **See it work:** `phase3_example_walkthrough.md` (concrete example)
4. **Deep dive:** `phase3_implementation_plan.md` (full specification)

---

## Key Concepts

### ArgumentNode
Not individual debate turns, but **semantic completion units**:
- **SYNTHESIS** - Agents converged on shared understanding
- **IMPASSE** - Irreconcilable disagreement identified
- **LEMMA** - Sub-argument established
- **QUESTION** - Question posed and explored
- **EXPLORATION** - Open-ended investigation
- **CLARIFICATION** - Definition or distinction established

### The Hard Problem
**When does a sequence of DebateTurns become an ArgumentNode?**

MVP Solutions:
1. Explicit completion markers ("we agree", "irreconcilable")
2. Question-answer detection (for branch debates)
3. Repetition detection (circular arguments)
4. Max turn limit (force completion)

### Edge Types
- **BRANCHES_FROM** - Focused exploration of parent topic
- **CONTRADICTS** - Conflicting conclusions
- **ELABORATES** - Adds detail/depth
- SUPPORTS, REQUIRES, APPLIES_TO, ANALOGY (Phase 4)

### Context Retrieval
When processing new passage:
1. Find similar nodes (text similarity → embeddings later)
2. Format as context summary
3. Inject into agent system prompts
4. Enables cross-referencing of ideas

---

## Implementation Timeline

### Week 1: Core Data Structures (Days 1-4)
- ArgumentNode, Edge, DebateDAG classes
- NodeCreationDetector (completion detection)
- NodeFactory (transcript → node)
- Unit tests, save/load

### Week 2: Graph Building (Days 5-7)
- Integration with dialectic_poc.py
- SimpleSimilarity + ContextRetriever
- EdgeDetector (BRANCHES_FROM, CONTRADICTS, ELABORATES)
- Automatic edge creation

### Week 3: Linearization and Testing (Days 8-10)
- LinearizationEngine (topological sort)
- Markdown rendering
- End-to-end testing (10+ passages)
- Validation against example walkthrough

---

## Success Criteria

**Phase 3 succeeds if:**
1. ✅ Graph builds incrementally across 10+ passages
2. ✅ New debates reference relevant past nodes
3. ✅ Edges connect related ideas meaningfully
4. ✅ Linearized output is readable narrative
5. ✅ Session persists and resumes correctly

**Red flags:**
- ❌ Every turn becomes a node (too granular)
- ❌ No nodes created (detector too strict)
- ❌ All same node type (detector broken)
- ❌ No edges detected (relationships not found)
- ❌ Context retrieval returns irrelevant nodes
- ❌ Linearization is unreadable

---

## File Structure (After Implementation)

```
# Existing
dialectic_poc.py              # Phase 0/2 code (agents, debates, observers)

# New Phase 3 files
phase3_dag.py                 # ArgumentNode, Edge, DebateDAG
phase3_nodes.py               # NodeCreationDetector, NodeFactory
phase3_edges.py               # EdgeDetector
phase3_similarity.py          # SimpleSimilarity, ContextRetriever
phase3_linearize.py           # LinearizationEngine
phase3_session.py             # DebateSession (main orchestrator)
test_phase3.py                # Unit and integration tests

# Data files (generated)
zarathustra_prologue_graph.json      # DAG structure
zarathustra_prologue_turns.json      # Full transcripts
zarathustra_prologue_narrative.md    # Linearized output
```

---

## Example Usage

```python
from phase3_session import DebateSession
from dialectic_poc import Agent

# Initialize session
session = DebateSession("my_reading")

# Define agents
agents = [
    Agent("Literalist", "Focus on literal meaning", "Historical facts"),
    Agent("Symbolist", "Everything is metaphor", "Psychological depth"),
]

# Process passages
passages = [
    "When Zarathustra was thirty years old...",
    "Ten years he enjoyed his spirit...",
    "At last his heart transformed..."
]

for passage in passages:
    node = session.process_passage(passage, agents)
    print(f"Created: {node.topic}")

# Export readable narrative
session.export_narrative()

print(f"Graph: {len(session.dag)} nodes, {len(session.dag.edges)} edges")
```

**Output:**
```
Created: Interpretation of Zarathustra's departure at thirty
Created: Duration and significance of ten-year solitude
Created: Nature of transformation: sudden or gradual
Graph: 4 nodes, 4 edges
Narrative exported to: my_reading_narrative.md
```

---

## What's Included in MVP

**Core Features:**
- ✅ ArgumentNode creation with 6 node types
- ✅ Simple text-based similarity (Jaccard)
- ✅ BRANCHES_FROM, CONTRADICTS, ELABORATES edges
- ✅ Topological sort linearization
- ✅ JSON persistence (save/load sessions)
- ✅ Context retrieval and injection
- ✅ Markdown narrative export

**Deferred to Later Phases:**
- ⏳ Embedding-based similarity (Phase 3.5)
- ⏳ SUPPORTS, REQUIRES, ANALOGY edges (Phase 3.5)
- ⏳ Memory compression (Phase 4)
- ⏳ Interactive graph UI (Phase 5)
- ⏳ Cross-text references (Phase 4)
- ⏳ User feedback loop (Phase 4)

---

## Testing Approach

### Unit Tests
- Node creation from transcripts
- Completion detection heuristics
- Similarity scoring
- Edge detection rules
- Save/load round-trip
- Topological sort correctness

### Integration Tests
- End-to-end: 3 passages → graph → narrative
- Context retrieval works
- Cross-references appear
- Session persistence
- Compare to example walkthrough

### Validation
- Process actual Nietzsche text (10 passages)
- Manual review of node quality
- Check edge validity
- Verify narrative readability

---

## Next Steps

1. **Review documentation** - Read implementation plan, quick ref, and example
2. **Set up environment** - Ensure dialectic_poc.py runs successfully
3. **Start Week 1, Day 1** - Implement ArgumentNode and DebateDAG
4. **Test incrementally** - Unit test each component
5. **Integrate gradually** - Build on existing Phase 0/2 code

---

## Questions to Answer During Implementation

### Design Decisions
- [ ] Optimal min/max turns for node creation?
- [ ] Best threshold for text similarity (currently 0.3)?
- [ ] Should CONTRADICTS edges be bidirectional?
- [ ] How many relevant nodes to inject as context (currently 3)?

### Technical Choices
- [ ] Use separate JSON files for turns or embed in nodes?
- [ ] Cache embeddings when switching to Phase 3.5?
- [ ] Incremental save vs. save at end of session?
- [ ] How to handle cycles if they occur?

### Quality Metrics
- [ ] What makes a "good" node?
- [ ] When are edges helpful vs. noise?
- [ ] How to measure narrative quality?
- [ ] Success rate for context relevance?

---

## Resources

### Code References
- `dialectic_poc.py` - Existing agents, debates, observers
- `dialecticaldebate.md` - Original design document and requirements
- Example log: `dialectic_log_20251115_083026.md`

### External Dependencies
- Python 3.8+
- `llm` CLI tool (simonw/llm) with ElectronHub API key
- Standard library: dataclasses, json, pathlib, datetime, hashlib

### Key Papers/Concepts
- Topological sort (Kahn's algorithm)
- Jaccard similarity (set-based text comparison)
- DAG (Directed Acyclic Graph) structures
- Semantic completion in dialogue

---

## Troubleshooting Guide

### "No nodes are being created"
- Check NodeCreationDetector thresholds
- Verify min_turns not too high
- Add debug logging to detection logic

### "All nodes are same type"
- Review completion marker detection
- Check explicit marker keywords
- Test with known SYNTHESIS/IMPASSE examples

### "Context retrieval returns irrelevant nodes"
- Lower similarity threshold (try 0.2)
- Check content word extraction
- Consider adding more theme tags

### "Edges aren't detected"
- Verify tag extraction working
- Check edge detection thresholds
- Use manual LLM suggestions

### "Linearization is unreadable"
- Verify topological sort working
- Check for cycles in graph
- Try chronological ordering instead

---

## Contributing / Extending

To add new features:

1. **New node types** - Extend NodeType enum, update detection logic
2. **New edge types** - Extend EdgeType enum, add detection method
3. **Better similarity** - Replace SimpleSimilarity with EmbeddingSimilarity
4. **New linearization** - Extend LinearizationEngine with custom ordering
5. **UI integration** - Build on DebateSession API

---

## Contact / Support

This is a personal research project by olivia (@taygetea, @4confusedemoji).

For issues or questions:
- Review the documentation files first
- Check the example walkthrough
- Consult dialecticaldebate.md for original design intent

---

**Ready to implement?** Start with `phase3_implementation_plan.md` Section 6: Implementation Sequence, Week 1, Day 1.

**Just exploring?** Read `phase3_example_walkthrough.md` to see the system in action.

**Need a refresher?** Use `phase3_quick_reference.md` for fast lookups.

**Confused about architecture?** Check `phase3_architecture_diagram.md` for visual explanations.
