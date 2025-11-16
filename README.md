# Dialectical Debate System

**A multi-perspective debate system that builds persistent knowledge graphs through branching discussions and diverse observer viewpoints**

## What This Does

The system generates philosophical debates between hard-coded agents (Literalist, Symbolist, Structuralist) on passages of text, accumulating insights into a persistent graph structure.

### Key Features

1. **Branching debates:** Discussions branch off to explore specific questions, then integrate back
2. **Biased observers:** Specialized perspectives identify non-obvious tensions worth exploring
3. **Automated diversity:** Generates maximally-different observers for any passage
4. **Persistent knowledge graph:** Debates become nodes in a DAG with typed relationships
5. **Context retrieval:** New debates reference and build on past discussions
6. **Narrative export:** Graph linearizes to readable markdown with topological ordering

## Quick Start

### Prerequisites

- Python 3.8+
- [simonw/llm](https://github.com/simonw/llm) CLI tool
- LLM API access (ElectronHub, OpenAI, Anthropic, etc.)

### Setup

```bash
# Install llm CLI
pip install llm

# Configure your LLM provider
llm keys set electronhub  # or your provider
# Enter your API key

# Set default model
llm models default electronhub/claude-sonnet-4-5-20250929
```

### Run Your First Session

```bash
cd dialectical-debate/src

# Basic debate with manual branch point
python dialectic_poc.py

# Multi-observer debate (generates diverse perspectives)
python multi_observer_test.py

# Full graph-building session (persistent knowledge accumulation)
python test_e2e.py
```

## Project Structure

```
dialectical-debate/
├── README.md                    # This file
├── QUICKSTART.md               # Detailed getting started guide
├── ARCHITECTURE.md             # System design and concepts
├── src/                        # Source code
│   ├── dialectic_poc.py        # Core: Agents, Observers, Debates, Logging
│   ├── debate_graph.py         # ArgumentNode, Edge, DebateDAG classes
│   ├── node_factory.py         # Node creation and completion detection
│   ├── edge_detection.py       # Automatic relationship detection
│   ├── context_retrieval.py    # Context from past debates
│   ├── linearization.py        # Graph to markdown narrative
│   ├── session.py              # Main orchestrator (DebateSession)
│   ├── phase2_observer_generation.py  # Observer auto-generation
│   └── multi_observer_test.py  # Multi-observer examples
├── docs/                       # Documentation
│   ├── DESIGN_DECISIONS.md     # Key design choices
│   ├── ARCHITECTURE.md         # System architecture
│   └── *.md                    # Implementation guides
├── examples/                   # Sample outputs
│   ├── multi_observer_report_*.md
│   └── ensemble_*.json
└── output/                     # Generated sessions (DAGs, narratives)
```

## Core Concepts

### Agents vs. Observers

**Agents** participate in debates:
- **The Literalist:** Focuses on literal text and factual claims
- **The Symbolist:** Reads symbolic and archetypal meanings
- **The Structuralist:** Analyzes patterns and formal relationships

**Observers** identify branch points from biased perspectives:
- Auto-generated with maximal diversity
- Each observer has specific focus and blind spots
- Generate non-obvious questions that generic detection would miss

### Debate Flow

```
1. Main Debate (3 rounds on passage)
   ↓
2. Observer identifies tension/question
   ↓
3. Branch Debate (2 rounds on specific question)
   ↓
4. Node Creation (semantic completion unit)
   ↓
5. Edge Detection (relationships to past nodes)
   ↓
6. Context Integration (available for future debates)
   ↓
7. Narrative Export (linearized markdown)
```

### Knowledge Graph Structure

**ArgumentNode:** A semantically complete debate segment
- Topic (1-2 sentence summary)
- Resolution (paragraph summary)
- Type (synthesis, impasse, exploration, etc.)
- Theme tags, key claims, full transcript

**Edge:** Typed relationship between nodes
- BRANCHES_FROM (branch debates)
- CONTRADICTS (opposing positions)
- ELABORATES (builds on previous idea)

**DebateDAG:** The persistent graph
- Accumulates nodes across multiple passages
- Detects relationships automatically
- Exports to JSON for persistence
- Linearizes to markdown for reading

## Example Session

```python
from session import DebateSession
from dialectic_poc import Agent, Logger

# Create agents
agents = [
    Agent("The Literalist", "You interpret literally...", "Facts"),
    Agent("The Symbolist", "You see symbols...", "Archetypes"),
    Agent("The Structuralist", "You analyze patterns...", "Structure")
]

# Start session
session = DebateSession("my_reading")
logger = Logger("output/my_reading/log.md")

# Process passages
passage1 = "When Zarathustra was thirty years old..."
node1 = session.process_passage(passage1, agents, logger)

# Branch debates happen automatically via observers
# Or manually:
branch_question = "What does 'thirty years' signify?"
node2 = session.process_branch(branch_question, node1.node_id, agents, logger)

# Export narrative
session.export_narrative("output/my_reading/narrative.md")
```

## Observer Generation Example

**Kafka's Metamorphosis passage** generated five maximally-different observers:

1. **Bureaucratic Logistics Analyst:** "What administrative category would Gregor occupy?"
2. **Somatic Memory Archaeologist:** "What pre-human motor memories does his body know?"
3. **Narrative Temporality Saboteur:** "Why does temporal structure create unbridgeable gap?"
4. **Domestic Architecture Semiotician:** "How does furniture enforce species boundaries?"
5. **Metabolic Catastrophe Physician:** "Is Gregor's worry the confusion of oxygen-deprived brain?"

**Diversity metrics:** 92.8% average pairwise distance

## Design Decisions

### Context Retrieval

**Current approach:** Full backlog in context
- Modern LLMs have 200K+ token windows
- No embedding infrastructure needed
- Works perfectly for 10-100 passages
- Can add vector DB later if corpus grows

### Node Boundary Detection

**Four methods:**
1. Explicit completion markers ("we agree...", "fundamental disagreement...")
2. Q&A completion (branch question answered)
3. Repetition detection (circular arguments)
4. Max turns fallback

### Model Strategy

**Current (all Sonnet 4.5):**
- Debate agents: Sonnet (need quality, nuance)
- Node generation: Sonnet (metadata extraction)
- Observers: Sonnet (high temp for diversity)
- Summaries: Sonnet (consistent compression)

**Cost per session:** ~$0.20-0.50 depending on passage complexity

See `docs/DESIGN_DECISIONS.md` for full rationale.

## Development

### Running Tests

```bash
cd src
python test_e2e.py  # End-to-end integration test
```

### Key Files to Understand

1. **session.py** - Main orchestrator, start here
2. **debate_graph.py** - Core data structures
3. **dialectic_poc.py** - Agents, debates, logging
4. **node_factory.py** - How debates become nodes
5. **edge_detection.py** - How relationships are found

## Contributing

Research areas for exploration:

1. **Observer generation:** Alternative diversity metrics, domain-specific observers
2. **Node detection:** Better semantic completion signals
3. **Edge detection:** More sophisticated relationship identification
4. **Linearization:** Alternative narrative strategies (thematic, chronological, etc.)
5. **Context retrieval:** When to switch from full backlog to embeddings

## License

MIT License (see LICENSE file)

## Credits

Built with:
- [simonw/llm](https://github.com/simonw/llm) - CLI interface to LLMs
- ElectronHub - Multi-model API proxy
- Claude Sonnet 4.5 - Debate generation and analysis

---

**Version:** 1.0.0
**Last updated:** 2025-11-16
**Status:** Production-ready
