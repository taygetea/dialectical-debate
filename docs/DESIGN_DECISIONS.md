# Design Decisions

Key architectural choices and their rationale.

---

## 1. Context Retrieval Strategy (Phase 3)

**Decision:** Start with full-backlog-in-context, defer embeddings

### The Problem

New debates need context from past debates. How to provide relevant ArgumentNodes?

### Option 1: Vector Database / Embeddings (Traditional RAG)

**How it works:**
```python
# Compute embeddings for all nodes
for node in dag.nodes:
    node.embedding = compute_embedding(node.topic + node.resolution)

# For new passage
query_embedding = compute_embedding(new_passage)
similarities = cosine_similarity(query_embedding, all_node_embeddings)
relevant_nodes = top_k(similarities, k=5)
```

**Pros:**
- Scales to large corpora (100s-1000s of passages)
- Precise relevance ranking
- Standard approach, well-understood
- Reduces context usage

**Cons:**
- Requires embedding infrastructure (API calls or local model)
- Extra complexity (compute, store, query embeddings)
- Extra cost (embedding API calls)
- May miss subtle relevance (embedding space doesn't capture everything)

### Option 2: Full Backlog in Context (Modern Long-Context)

**How it works:**
```python
# Just include everything
all_nodes = dag.get_all_nodes()
context = format_nodes_as_text(all_nodes)
# Inject into agent system prompts
# Let LLM find what's relevant
```

**Pros:**
- Extremely simple implementation
- No embedding infrastructure needed
- No extra API calls
- LLM sees full context, can find non-obvious relevance
- Modern LLMs have 200K+ context windows
- Works perfectly for reasonable corpus sizes (10-100 passages)

**Cons:**
- Doesn't scale to massive corpora (1000s of passages)
- "Wastes" context window on irrelevant nodes
- Higher per-call cost (more input tokens)
- May hit context limits eventually

### Decision Matrix

| Criterion | Embeddings | Full Context | Winner |
|-----------|------------|--------------|--------|
| Simplicity | ❌ Complex | ✅ Simple | Full Context |
| 10-50 passages | ✅ Works | ✅ Works | Tie |
| 100-500 passages | ✅ Better | ⚠️ Marginal | Embeddings |
| 1000+ passages | ✅ Necessary | ❌ Won't work | Embeddings |
| Implementation time | 2-3 days | 1 hour | Full Context |
| Relevance quality | Good | Excellent* | Full Context |

*LLMs are very good at finding relevant context when they can see everything

### Recommendation: **Full Context for MVP**

**Rationale:**
1. **Most users won't process 100+ passages** - Full context handles this perfectly
2. **Simpler = faster to MVP** - Can validate Phase 3 concepts without embedding complexity
3. **Easy migration path** - Can add embeddings later if needed
4. **Quality may be better** - LLM sees full context, not just top-k retrieved

**Implementation:**
```python
class ContextRetriever:
    def __init__(self, dag: DebateDAG, strategy: str = "full"):
        self.dag = dag
        self.strategy = strategy  # "full" or "embedding"

    def get_relevant_context(self, passage: str) -> List[ArgumentNode]:
        if self.strategy == "full":
            return self.dag.get_all_nodes()
        elif self.strategy == "embedding":
            return self._embedding_search(passage)

    def _embedding_search(self, passage: str):
        # Deferred to Phase 3.5
        raise NotImplementedError("Use strategy='full' for MVP")
```

**Migration trigger:** If users report processing >100 passages regularly, implement embeddings.

---

## 2. LLM Interface: CLI vs. Python API

**Decision:** Use `llm` CLI via subprocess

### Alternatives Considered

**Option A: Direct API (OpenAI/Anthropic Python SDK)**
```python
import anthropic
client = anthropic.Anthropic(api_key="...")
response = client.messages.create(...)
```

**Option B: LiteLLM (unified Python API)**
```python
import litellm
response = litellm.completion(model="...", messages=[...])
```

**Option C: llm CLI (simonw/llm)**
```python
import subprocess
result = subprocess.run(['llm', '-s', system, ...], ...)
```

### Decision Matrix

| Criterion | Direct API | LiteLLM | llm CLI | Winner |
|-----------|-----------|---------|---------|--------|
| Provider flexibility | ❌ Single | ✅ Many | ✅ Many | LiteLLM/llm |
| Setup complexity | Medium | Low | Lowest | llm CLI |
| Performance | Fast | Fast | Slower | Direct/LiteLLM |
| Debugging | Medium | Medium | Easiest | llm CLI |
| Plugin ecosystem | ❌ None | ❌ None | ✅ Rich | llm CLI |

### Chosen: **llm CLI**

**Rationale:**
1. **Model-agnostic** - Works with any provider llm supports (450+ models via plugins)
2. **No API key management in code** - Keys stored via `llm keys set`
3. **Simple provider switching** - `llm models default <model>` changes everything
4. **Plugin ecosystem** - Can use embeddings, logging, caching plugins
5. **User-friendly** - Users already familiar with llm CLI can use same config

**Tradeoffs accepted:**
- Subprocess overhead (~50-100ms per call) - Acceptable for research prototype
- Error handling more complex - Mitigated with clear error messages

**Implementation:**
```python
def llm_call(system_prompt: str,
             user_prompt: str,
             temperature: float = 0.7,
             model: str = "electronhub/claude-sonnet-4-5-20250929") -> str:

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

---

## 3. Hard-Coded Agents vs. Generated Agents

**Decision:** Hard-code the three debate agents, generate observers

### Rationale

**Agents (Literalist, Symbolist, Structuralist):**
- Represent stable interpretive *positions*
- Need to be consistent across all debates for meaningful friction
- Tri-partite structure creates thesis/antithesis/synthesis pattern
- Hand-crafted quality ensures coherence

**Observers (Phase 2 generates them):**
- Represent *exploration* of interpretive space
- Benefit from diversity and novelty
- Different observers for different passages makes sense
- Automated generation scales better

### Could We Generate Agents Too?

**Possible future enhancement:**
```python
# Generate agents tuned to passage type
agents = generate_agent_ensemble(passage, num_agents=3)
# E.g., for scientific text: Empiricist, Theorist, Methodologist
```

**Why we haven't:**
- More complex to ensure stability
- Current 3 agents work well across text types
- Observer diversity already provides variance
- Can revisit in Phase 4+

---

## 4. Temperature Strategy

**Decision:** Different temperatures for different tasks

### Temperature Settings

| Task | Temperature | Rationale |
|------|-------------|-----------|
| Debate agents | 0.7 | Balance coherence + engagement |
| Summaries | 0.3-0.4 | Factual, consistent compression |
| Observer generation | 0.85 | High creativity for diversity |
| Node synthesis | 0.5-0.6 | Balanced analysis |

### Debate Agent Temperature (0.7)

**Tried:**
- 0.3: Too robotic, repetitive, boring
- 0.5: Coherent but predictable
- 0.7: Sweet spot - coherent + engaging
- 0.9: Too creative, agents drift from positions

**Chosen: 0.7** - Maintains positions while allowing dynamic engagement

### Observer Generation (0.85)

**Critical for diversity:**
- Lower temps (0.5-0.7) → observers converge to similar perspectives
- Higher temps (0.85+) → genuinely orthogonal viewpoints

**Results:**
- 0.5 temp: avg diversity 0.65
- 0.85 temp: avg diversity 0.93

**Chosen: 0.85** - Necessary for "maximally different" to work

### Summary Temperature (0.3-0.4)

**Not a creative task:**
- Need factual compression
- Consistency across runs
- Low temp appropriate

**Chosen: 0.3-0.4** - Reliable summarization

---

## 5. Model Selection: Haiku vs. Sonnet

**Decision:** Use Sonnet for everything (fallback from planned Haiku usage)

### Original Plan

- **Debate agents:** Sonnet (need quality)
- **Observers:** Haiku (fast, cheap)
- **Summaries:** Haiku (simple task)

### What Happened

**Haiku 4.5 issues:**
- Timeout errors (no response after 15+ seconds)
- Empty responses
- Inconsistent availability

**Fallback to Sonnet:**
```python
# Changed all instances from:
model="electronhub/claude-haiku-4-5-20251001"
# To:
model="electronhub/claude-sonnet-4-5-20250929"
```

### Cost Impact

**Per debate (with Haiku plan):**
- Debates: Sonnet (~$0.15)
- Summaries: Haiku (~$0.02)
- Total: ~$0.17

**Actual (all Sonnet):**
- Everything: Sonnet (~$0.20)

**Impact:** ~20% cost increase, acceptable for reliability

### When to Retry Haiku

**Triggers:**
1. Haiku becomes stable/faster
2. Cost becomes prohibitive (processing 100s of passages)
3. Summaries specifically become bottleneck

**How to test:**
```python
# Try Haiku for summaries only
# If works reliably for 10+ runs, expand usage
```

---

## 6. Node Boundary Detection

**Decision:** Use 4-method approach (explicit markers, Q&A, repetition, max turns)

### The Problem

When does a debate reach "semantic completion" and become an ArgumentNode?

### Approaches Considered

**A. Fixed round count**
- Every N rounds = 1 node
- Simple but arbitrary
- Might cut off mid-resolution

**B. LLM meta-observer**
- Ask LLM "is this debate complete?"
- Flexible but expensive (extra calls)
- May be inconsistent

**C. Multi-method detection (chosen)**
- Combine multiple signals
- Explicit markers ("we agree...")
- Q&A completion (branch answered question)
- Repetition (circular arguments)
- Fallback (max turns)

### Implementation

```python
class NodeCreationDetector:
    def check_completion(self, transcript):
        # Method 1: Explicit markers
        if self._has_explicit_marker(transcript):
            return True, self._classify_marker_type(transcript)

        # Method 2: Q&A completion (for branches)
        if self.branch_question and self._question_answered(transcript):
            return True, NodeType.SYNTHESIS

        # Method 3: Repetition detection
        if self._detect_repetition(transcript):
            return True, NodeType.IMPASSE

        # Method 4: Max turns (fallback)
        if len(transcript) >= self.max_turns:
            return True, NodeType.EXPLORATION

        return False, None
```

### Why This Works

- **Explicit markers** catch deliberate resolutions
- **Q&A** handles branch debates naturally
- **Repetition** identifies stuck debates
- **Max turns** ensures termination

**Validation:** Test against hand-labeled transcripts, should agree >80%

---

## 7. Edge Types: Which to Implement

**Decision:** MVP implements 3 edge types, defer 4 others

### Implemented (Phase 3 MVP)

1. **BRANCHES_FROM**
   - Automatic (branch debates have parent reference)
   - High confidence (structural relationship)

2. **CONTRADICTS**
   - Pattern matching ("contradicts", "opposes")
   - Check if key claims directly oppose
   - Medium-high confidence

3. **ELABORATES**
   - Pattern matching ("builds on", "extends")
   - Topic similarity + sequential ordering
   - Medium confidence

### Deferred (Phase 3.5+)

4. **SUPPORTS** - Harder to distinguish from ELABORATES
5. **REQUIRES** - Needs dependency analysis
6. **APPLIES_TO** - Needs context understanding
7. **ANALOGY** - Needs semantic similarity

### Rationale

**MVP focus:** Get basic graph structure working
**Deferred types:** Can be added incrementally without redesign

**Migration path:**
```python
class EdgeType(Enum):
    # MVP
    BRANCHES_FROM = "branches_from"
    CONTRADICTS = "contradicts"
    ELABORATES = "elaborates"

    # Phase 3.5 - uncomment when ready
    # SUPPORTS = "supports"
    # REQUIRES = "requires"
    # APPLIES_TO = "applies_to"
    # ANALOGY = "analogy"
```

---

## 8. Persistence Format: JSON vs. Database

**Decision:** JSON files for Phase 3 MVP

### Alternatives

**A. JSON Files**
```python
{
  "nodes": [...],
  "edges": [...],
  "metadata": {...}
}
```

**B. SQLite Database**
```sql
CREATE TABLE nodes (...);
CREATE TABLE edges (...);
```

**C. Graph Database (Neo4j, etc.)**
```cypher
CREATE (n:ArgumentNode {...})
CREATE (n1)-[:CONTRADICTS]->(n2)
```

### Decision Matrix

| Criterion | JSON | SQLite | Graph DB | Winner |
|-----------|------|--------|----------|--------|
| Simplicity | ✅ Easiest | Medium | ❌ Complex | JSON |
| Human-readable | ✅ Yes | ❌ No | ❌ No | JSON |
| Query power | ❌ Limited | ✅ Good | ✅ Excellent | SQLite/Graph |
| Portability | ✅ Perfect | Good | ❌ Complex | JSON |
| Setup | ✅ None | Minimal | ❌ Significant | JSON |

### Chosen: **JSON for MVP**

**Rationale:**
1. **Simplicity** - No database setup
2. **Portability** - Copy files, commit to git
3. **Debugging** - Can inspect/edit by hand
4. **Good enough** - For <100 nodes, JSON is fine

**When to migrate:**
- Graph exceeds ~500 nodes
- Complex queries needed
- Performance becomes issue

**Implementation:**
```python
def save(self, path: Path):
    with open(path, 'w') as f:
        json.dump({
            'nodes': [n.to_dict() for n in self.nodes.values()],
            'edges': [e.to_dict() for e in self.edges],
            'metadata': {...}
        }, f, indent=2)
```

---

## 9. Linearization Algorithm

**Decision:** Topological sort (Kahn's algorithm) with chronological fallback

### The Problem

Graph structure → Linear narrative. How to order nodes?

### Alternatives

**A. Chronological** (creation order)
- Simple
- Ignores dependencies
- May present conclusions before premises

**B. Topological Sort** (dependency order)
- Respects edges (show premises before conclusions)
- Handles DAG structure
- Fails if cycles exist

**C. Hybrid** (chosen)
- Try topological sort first
- Fall back to chronological if cycles detected
- Best of both worlds

### Implementation

```python
def linearize(self) -> List[str]:
    try:
        # Try topological sort
        return self._topological_sort()
    except CycleDetectedError:
        # Fallback to chronological
        logger.warning("Cycle detected, using chronological order")
        return self._chronological_order()
```

### Why Topological Sort?

**Makes sense for debates:**
- Branch should appear after main debate
- Elaborations after original points
- Requirements before dependents

**Kahn's algorithm:**
- Start with nodes that have no incoming edges
- Add their dependents as edges are "removed"
- Linear time O(V + E)

---

## 10. Future Decisions to Make

### Phase 3 Implementation

1. **Context injection method**
   - System prompt vs. user prompt?
   - How much context is too much?

2. **Edge confidence calibration**
   - What threshold for "confident" vs. "tentative"?
   - How to present low-confidence edges?

3. **Node splitting**
   - Should long debates be split into multiple nodes?
   - What's the max size of a single node?

### Phase 4+

4. **Memory compression**
   - How to compress old nodes for context efficiency?
   - Summarize-and-forget vs. full retention?

5. **User feedback integration**
   - How to let users correct edge detection?
   - How to learn from corrections?

6. **Cross-text references**
   - How to handle debates across different source texts?
   - Separate DAGs vs. unified graph?

---

**These decisions are documented to:**
1. Help future implementers understand choices
2. Make migration paths clear
3. Avoid re-litigating settled questions
4. Guide future enhancements
