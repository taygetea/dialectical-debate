# System Architecture

## Overview

The Dialectical Debate System generates philosophical insights through multi-perspective debates with branching exploration and automated observer generation.

## Core Architecture Layers

```
┌─────────────────────────────────────────┐
│         User Interface Layer            │
│  (Python scripts, CLI interaction)      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Orchestration Layer                │
│  (DebateSession, multi-observer loops)  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Debate Generation Layer           │
│  (Agents, Observers, run_debate)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        LLM Interface Layer              │
│  (llm_call → subprocess → llm CLI)      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Logging & Persistence Layer        │
│  (Logger, JSON export, file output)     │
└─────────────────────────────────────────┘
```

## Core Components

### 1. Agent System

**Purpose:** Represent distinct interpretive perspectives in debates

**Classes:**
```python
class Agent:
    name: str         # "The Literalist"
    stance: str       # What they always look for
    focus: str        # Their area of expertise

    get_system_prompt() → str  # Generate LLM system prompt
```

**Built-in Agents:**
1. **The Literalist** - Focuses on literal text, biographical facts
2. **The Symbolist** - Everything is metaphor, psychological archetypes
3. **The Structuralist** - Universal narrative patterns, intertextuality

**Design Principle:** Agents are hard-coded and consistent. They maintain their perspective across all debates, creating reliable interpretive friction.

### 2. Observer System

**Purpose:** Identify branch points from biased perspectives

**Phase 1 - Hand-Crafted:**
```python
class Observer:
    name: str
    bias: str              # Core orientation
    focus: str             # Specific angles
    blind_spots: List[str] # What they systematically miss
    example_questions: List[str]  # Good questions from their perspective
    anti_examples: List[str]      # Bad (too generic) questions

    identify_branch(transcript, passage) → str  # Return branch question
```

**Phase 2 - Auto-Generated:**
```python
def generate_observer_ensemble(passage, num_perspectives=5):
    """Iteratively generate maximally different observers"""
    # 1. Generate first perspective (high temp, creative)
    # 2-N. Generate perspectives maximally different from existing
    # Returns: List of perspective dicts
```

**Key Innovation:** Instead of generic "what's unresolved?", observers ask "from MY perspective, what are they missing?"

### 3. Debate Engine

**Core Flow:**
```python
def run_debate(passage, agents, rounds=3, logger=None):
    transcript = []

    for round in range(rounds):
        for agent in agents:
            # Build context from previous turns
            context = build_context(transcript)

            # Generate response
            response = llm_call(
                agent.get_system_prompt(),
                f"Passage: {passage}\n{context}\nRespond:",
                temperature=0.7
            )

            # Log with summary
            turn = DebateTurn(agent.name, response, round)
            transcript.append(turn)
            logger.log_turn_with_summary(turn)

    return transcript
```

**Key Features:**
- Accumulating context (each turn sees all previous turns)
- Per-turn LLM summarization
- Structured output (DebateTurn objects)
- Optional logging

### 4. Branch-and-Merge

**Branching:**
```python
def identify_branch_point(transcript, passage, observer=None):
    if observer:
        # Observer-driven: Use biased perspective
        return observer.identify_branch(transcript, passage)
    else:
        # Generic: Ask for "most important unresolved question"
        return llm_call(generic_prompt, ...)
```

**Branch Debate:**
```python
def run_branch_debate(branch_question, agents, rounds=2):
    # Same structure as main debate, but focused on specific question
    # Returns: transcript of branch discussion
```

**Synthesis:**
```python
def synthesize_branch_resolution(branch_question, branch_transcript):
    # LLM summarizes:
    # - What perspectives emerged
    # - What got resolved
    # - What remains in tension
```

**Merge-Back:**
```python
def merge_branch_back(main_transcript, branch_question,
                      branch_synthesis, original_passage):
    # LLM generates enriched understanding:
    # - How does branch resolution change interpretation of main debate?
    # - What new insights emerged?
```

### 5. Logging System

**Purpose:** Structured, summarized output for human consumption

```python
class Logger:
    output_file: str
    log_entries: List[str]
    start_time: datetime

    log(text)                    # Write to console + file
    log_section(title)           # Major section header
    log_subsection(title)        # Minor section header

    summarize_turn(agent, content) → str  # LLM 1-line summary
    log_turn_with_summary(turn)           # Log turn + summary
    log_phase_summary(phase, description) # Phase-level summary

    finalize()  # Write session metadata, close file
```

**Output Structure:**
```markdown
# Dialectical Debate Log
Started: TIMESTAMP

## MAIN DEBATE
[turns with summaries]

PHASE SUMMARY: Main Debate
[2-3 sentence LLM summary]

## BRANCH POINT IDENTIFIED
Question: ...

## BRANCH DEBATE
[turns with summaries]

BRANCH SYNTHESIS
[synthesis text]

## ENRICHED UNDERSTANDING (MERGE-BACK)
[merge-back text]

## SESSION COMPLETE
Duration: X seconds
```

### 6. LLM Interface

**llm_call function:**
```python
def llm_call(system_prompt: str,
             user_prompt: str,
             temperature: float = 0.7,
             model: str = "electronhub/claude-sonnet-4-5-20250929") → str:

    result = subprocess.run(
        ['llm', '-m', model, '-s', system_prompt,
         '-o', 'temperature', str(temperature)],
        input=user_prompt,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
```

**Design Decisions:**
- Uses subprocess to call `llm` CLI (not Python API)
- All models currently: Sonnet 4.5 (Haiku had timeout issues)
- Temperature defaults:
  - Debates: 0.7
  - Summaries: 0.3-0.4
  - Observer generation: 0.85 (high for diversity)

### 7. Observer Generation (Phase 2)

**First Perspective:**
```python
def generate_first_perspective(passage, temperature=0.8):
    """Generate initial observer for passage"""
    # High temp, creative exploration
    # Returns: {name, bias, focus, blind_spots}
```

**Contrasting Perspectives:**
```python
def generate_contrasting_perspective(passage, existing_perspectives, temperature=0.8):
    """Generate perspective maximally different from existing ones"""

    # Prompt includes all existing perspectives
    # Explicitly asks for "maximally different"
    # Measures success via Jaccard distance

    # Returns: {name, bias, focus, blind_spots}
```

**Diversity Measurement:**
```python
def measure_perspective_diversity(p1, p2):
    """How different are two perspectives?"""

    # Jaccard similarity on key terms
    p1_words = set((p1.bias + p1.focus).lower().split())
    p2_words = set((p2.bias + p2.focus).lower().split())

    similarity = len(p1_words & p2_words) / len(p1_words | p2_words)
    return {'jaccard_distance': 1 - similarity}
```

**Iterative Loop:**
```
Generate first perspective
For i in 2..N:
    Generate perspective maximally different from all existing
    Measure average distance from existing perspectives
    Add to ensemble

Return: List of N diverse perspectives
```

**Typical Results:**
- Average pairwise distance: 0.90-0.95
- No perspective pairs below 0.85 distance
- Genuinely orthogonal interpretive angles

## Data Flow

### Phase 0: Single Passage, Generic Branch

```
Passage
  ↓
Main Debate (Literalist, Symbolist, Structuralist, 3 rounds)
  ↓
Generic Branch Detection ("what's unresolved?")
  ↓
Branch Question
  ↓
Branch Debate (same agents, 2 rounds, focused question)
  ↓
Branch Synthesis (LLM summary)
  ↓
Merge-Back (LLM enriched understanding)
  ↓
Output: dialectic_log_TIMESTAMP.md
```

### Phase 1: Observer-Driven Branch

```
Passage
  ↓
Main Debate (3 rounds)
  ↓
Observer.identify_branch(transcript, passage)
  ↓
Branch Question (biased perspective)
  ↓
Branch Debate → Synthesis → Merge-Back
  ↓
Output: Comparison showing generic vs. observer questions
```

### Phase 2: Multi-Observer

```
Passage
  ↓
Generate Observer Ensemble (iterative, maximally different)
  ↓
Main Debate (shared for all observers)
  ↓
For each observer:
    Observer.identify_branch() → unique branch question
    Run branch debate on that question
    Synthesize
  ↓
Compare: How different are the branch questions?
  ↓
Output: multi_observer_report_TIMESTAMP.md
        ensemble_TIMESTAMP.json
        branch_1.md, branch_2.md, ...
```

## Key Design Decisions

### 1. Why subprocess + llm CLI instead of Python API?

**Pros:**
- Model-agnostic (works with any llm-compatible provider)
- No API key management in code
- Leverages llm's plugin ecosystem
- Simple to swap providers

**Cons:**
- Slower than direct API calls
- Subprocess overhead
- Error handling more complex

**Decision:** Simplicity and flexibility outweigh performance for research prototype.

### 2. Why hard-coded agents?

**Rationale:**
- Reliable interpretive friction requires stable perspectives
- Agents represent *positions*, not dynamic exploration
- Three agents = thesis/antithesis/synthesis pattern
- Could add more agents later, but 3 works well

### 3. Why generate observers instead of using templates?

**Phase 1 showed:**
- Hand-crafted observers (Phenomenologist, etc.) work well
- Each finds genuinely different angles
- But: labor-intensive to create many observers

**Phase 2 solution:**
- Automate generation with "maximally different from existing" loop
- Achieves 0.90+ diversity
- Adapts to passage content automatically
- Scales to N observers without manual work

### 4. Why branch-and-merge instead of just longer debates?

**Branching enables:**
- Focused exploration of specific tensions
- Non-obvious questions that wouldn't emerge in main debate
- Depth on particular points without losing main thread
- Merge-back creates synthesis across levels

**Alternative (rejected):**
- Just run longer debates (5-10 rounds)
- Problem: Agents repeat themselves, drift, lose focus
- Branching maintains structure while adding depth

### 5. Temperature strategy

**Debates (0.7):**
- Middle ground: coherent but not robotic
- Agents maintain positions while engaging

**Summaries (0.3-0.4):**
- Lower temp for consistency
- Factual compression, not creative

**Observer generation (0.85):**
- High temp for creative divergence
- Necessary to avoid convergence to similar perspectives

## Extensibility

### Adding New Agents

```python
new_agent = Agent(
    name="The Pragmatist",
    stance="Ideas only matter if they have practical consequences",
    focus="Testability, actionability, real-world implications"
)

agents = [literalist, symbolist, structuralist, new_agent]
```

### Adding New Observer Personas (Manual)

```python
new_observer = Observer(
    name="The Quantum Grammarian",
    bias="All meaning exists in superposition until observed",
    focus="Ambiguity, multiple simultaneous readings, uncertainty",
    blind_spots=["Definitive interpretations", "Historical context"],
    example_questions=["What readings collapse if we force coherence?"]
)
```

### Custom Debate Formats

```python
# Asymmetric rounds
round1 = run_debate(passage, agents, rounds=1)  # Opening
branch = identify_and_run_branch(...)
round2 = run_debate(passage, agents, rounds=2)  # Continue with branch insights

# Multiple branches
branch1 = run_branch_debate(question1, ...)
branch2 = run_branch_debate(question2, ...)
merge = merge_multiple_branches([branch1, branch2], ...)
```

## Performance Characteristics

**Phase 0 (single passage):**
- Duration: ~2-4 minutes
- LLM calls: ~20-25
- Cost: ~$0.10-0.20 (Sonnet 4.5)
- Output: ~20KB markdown

**Phase 2 (5 observers):**
- Duration: ~8-12 minutes
- LLM calls: ~100-120
- Cost: ~$1.00-1.50 (Sonnet 4.5)
- Output: ~100KB total (main report + 5 branches)

**Observer generation (5 perspectives):**
- Duration: ~1-2 minutes
- LLM calls: 5
- Cost: ~$0.05-0.10
- Output: JSON ensemble file

## Future Architecture (Phase 3+)

### Graph Structure

```
ArgumentNode (semantic completion unit)
  ├── topic: str
  ├── turns: List[DebateTurn]
  ├── resolution: str
  ├── node_type: NodeType
  └── embedding: Vector

Edge (typed relationship)
  ├── from_node_id: str
  ├── to_node_id: str
  ├── edge_type: EdgeType
  └── confidence: float

DebateDAG
  ├── nodes: Dict[str, ArgumentNode]
  ├── edges: List[Edge]
  ├── find_relevant_context(passage) → List[ArgumentNode]
  └── linearize() → str
```

### Context Retrieval

**Two approaches under consideration:**

**Option 1: Embedding-based (traditional RAG)**
- Compute embeddings for each ArgumentNode
- Vector similarity search
- Retrieve top-k relevant nodes

**Option 2: Full backlog in context**
- Modern LLMs have 200K+ context
- Just include entire graph for reasonable sizes (10-100 passages)
- Simpler, no embedding infrastructure

**Current recommendation:** Start with Option 2 (full context), add embeddings only if needed.

---

**Next:** See `docs/PHASE_3_NEXT.md` for implementation details.
