# Dialectical Debate System

**A multi-perspective debate system that generates insights through branching discussions and diverse observer viewpoints**

## Status

- ✅ **Phase 0:** Core debate mechanism with branching and merge-back
- ✅ **Phase 1:** Single observer with biased perspectives
- ✅ **Phase 2:** Automated observer generation with diversity optimization
- 🔨 **Phase 3:** Graph structure (DAG) - Ready to implement

## What This Does

The system generates philosophical debates between hard-coded agents (Literalist, Symbolist, Structuralist) on passages of text. Key innovations:

1. **Branch-and-merge:** Debates can branch off to explore specific questions, then merge insights back
2. **Biased observers:** Instead of generic "what's important?" detection, observers with specific perspectives identify non-obvious branch points
3. **Automated diversity:** Generates multiple maximally-different observers for any passage
4. **Rich logging:** Every turn gets LLM-generated summaries, phase summaries, and structured output

## Quick Start

### Prerequisites

- Python 3.8+
- [simonw/llm](https://github.com/simonw/llm) CLI tool
- ElectronHub API access (or modify for your provider)

### Setup

```bash
# Install llm CLI
pip install llm

# Configure your LLM provider
llm keys set electronhub
# Enter your API key

# Set default model
llm models default electronhub/claude-sonnet-4-5-20250929
```

### Run Your First Debate

```bash
cd dialectical-debate/src

# Phase 0: Basic debate with manual branch point
python dialectic_poc.py

# Phase 2: Generate 5 diverse observers and run multi-observer debate
python multi_observer_test.py

# Phase 1: Compare generic vs. observer-driven branch detection
python phase1_comparison.py
```

## Project Structure

```
dialectical-debate/
├── README.md                    # This file
├── QUICKSTART.md               # Detailed getting started guide
├── ARCHITECTURE.md             # System design and concepts
├── src/                        # Source code
│   ├── dialectic_poc.py        # Core: Agents, Observers, Debates, Logging
│   ├── phase2_observer_generation.py  # Automated observer generation
│   ├── phase1_comparison.py    # Generic vs. observer comparison
│   └── multi_observer_test.py  # Multi-observer on same passage
├── docs/                       # Documentation
│   ├── PHASE_0_1_2_COMPLETE.md # What's been built
│   ├── PHASE_3_NEXT.md         # What to build next
│   ├── DESIGN_DECISIONS.md     # Key design choices
│   └── phase3_*.md             # Phase 3 planning documents
├── examples/                   # Sample outputs
│   ├── multi_observer_report_*.md
│   ├── comparison_*.md
│   └── ensemble_*.json
├── tests/                      # Tests (future)
└── data/                       # Debate logs, ensembles (generated)
```

## Core Concepts

### Agents vs. Observers

**Agents** participate in debates:
- The Literalist (focuses on literal text)
- The Symbolist (everything is metaphor)
- The Structuralist (universal narrative patterns)

**Observers** identify branch points from biased perspectives:
- Phase 1: Hand-crafted (Phenomenologist, Materialist Historian, Pragmatist Engineer)
- Phase 2: Auto-generated with maximal diversity

### Debate Flow

```
1. Main Debate (3 rounds)
   ↓
2. Observer identifies branch point
   ↓
3. Branch Debate (2 rounds on specific question)
   ↓
4. Synthesis (what got resolved/remains in tension)
   ↓
5. Merge-back (enriched understanding of original passage)
```

### Key Innovation: Biased Observers

Instead of asking "what's unresolved?" (generic), observers ask "from MY perspective, what are they missing?"

Example observer biases:
- "Only first-person lived experience is primary" → asks about phenomenology
- "All ideas are products of material conditions" → asks about class dynamics
- "Ideas only matter if they have practical consequences" → asks about testability

Result: **Non-obvious branch points** that wouldn't emerge from generic detection.

## Phase 2 Results

**Diversity metrics:**
- Average pairwise distance between generated observers: **0.928**
- Question differentiation across observers: **89.5%**

**Example: Kafka's Metamorphosis**

Five auto-generated observers each found completely different angles:

1. **Bureaucratic Logistics Analyst:** "What administrative category would Gregor occupy?"
2. **Somatic Memory Archaeologist:** "What pre-human motor memories does his body know?"
3. **Narrative Temporality Saboteur:** "Why does the temporal structure create an unbridgeable gap?"
4. **Domestic Architecture Semiotician:** "Why specify 'in his bed'—how does furniture enforce species boundaries?"
5. **Metabolic Catastrophe Physician:** "Is Gregor's mundane worry about trains the confusion of an oxygen-deprived brain?"

## What's Next: Phase 3

Transform from linear transcripts to **semantic knowledge graph**:

- **ArgumentNodes:** Semantic completion units (not individual turns)
- **Typed edges:** BRANCHES_FROM, CONTRADICTS, ELABORATES, etc.
- **Context retrieval:** New debates reference relevant past nodes
- **Linearization:** Graph → coherent narrative via topological sort

**Start here:** `docs/PHASE_3_NEXT.md`

## Model Strategy

**Current (all Sonnet 4.5):**
- Debate agents: Sonnet (need quality, nuance)
- Observers: Sonnet (Haiku had timeout issues)
- Summaries: Sonnet

**Future optimization:**
- Try Haiku again for summaries when stable
- Opus for difficult passages or final synthesis
- Consider cost/speed tradeoffs

## Design Decisions

### Context Retrieval Strategy (Phase 3)

Two competing approaches:

**Option 1: Vector DB / Embeddings**
- Compute embeddings for each ArgumentNode
- Similarity search for relevant context
- Classic RAG approach

**Option 2: Full Backlog in Context**
- Modern LLMs have long context (200K tokens)
- Just include everything for reasonable corpus sizes
- Simpler, no embedding infrastructure

**Current recommendation:** Start with Option 2 (full context) since:
- Simpler to implement
- No embedding infrastructure needed
- Works for 10-100 passages easily
- Can add embeddings later if needed

See `docs/DESIGN_DECISIONS.md` for full discussion.

## Contributing

This is a research prototype. Key areas for exploration:

1. **Observer generation:** Can we get even more diversity? Different generation strategies?
2. **Node boundary detection:** When does a debate become semantically complete?
3. **Edge detection:** Automatic relationship identification between ideas
4. **Linearization:** How to present graphs as readable narratives?

## License

[Your license here]

## Credits

Built with:
- [simonw/llm](https://github.com/simonw/llm) - CLI interface to LLMs
- ElectronHub - Multi-model API proxy
- Claude Sonnet 4.5 - Debate generation and meta-analysis

---

**Last updated:** 2025-11-15
**Version:** 0.3.0 (Phase 2 complete, Phase 3 planned)
