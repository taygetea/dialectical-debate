# Phase 3 Example Walkthrough

This document shows a **concrete, step-by-step example** of how the Phase 3 system works when processing actual text.

## Scenario: Reading Nietzsche's Zarathustra

We'll process three passages and watch the graph build.

---

## Initial Setup

```python
from phase3_session import DebateSession
from dialectic_poc import Agent, Observer

# Create session
session = DebateSession("zarathustra_prologue")

# Define agents
agents = [
    Agent(
        name="The Literalist",
        stance="Focus on what literally happened in the text",
        focus="Biographical and historical details"
    ),
    Agent(
        name="The Symbolist",
        stance="Everything is metaphor for internal states",
        focus="Symbolic meanings and archetypal patterns"
    ),
    Agent(
        name="The Structuralist",
        stance="This follows universal narrative patterns",
        focus="Story structures and literary conventions"
    )
]

# Define observer
observer = Observer(
    name="The Phenomenologist",
    bias="Only first-person lived experience is primary",
    focus="Subjective states and qualia"
)
```

**Current state:**
- DAG: 0 nodes, 0 edges
- No context available

---

## Passage 1: "When Zarathustra was thirty years old..."

### Input

```
Passage: "When Zarathustra was thirty years old, he left his home
         and the lake of his home, and went into the mountains."
```

### Step 1: Context Retrieval

```python
retriever = ContextRetriever(session.dag)
relevant = retriever.get_relevant_context(passage, [])
```

**Result:** No relevant nodes (DAG is empty)

### Step 2: Run Main Debate

```
ROUND 1:

Literalist: This describes a historical event - Zarathustra (Zoroaster)
left his birthplace at age thirty to begin his spiritual mission. The
detail of "thirty years" is significant in Persian tradition.

Symbolist: The thirty years represents inner maturation. "Home and lake"
symbolize the familiar self, while "mountains" represent transcendence
and elevation. This is the archetypal hero's departure.

Structuralist: Classic monomyth structure - the Call to Adventure. The
protagonist leaves the Ordinary World (home/lake) for the Special World
(mountains). Age thirty marks readiness for transformation.

ROUND 2:

Literalist: But we must attend to the actual geography - Zarathustra is
a real figure, these are Persian mountains, this is a biographical fact.

Symbolist: The "fact" is secondary to its psychological meaning. The
mountains aren't just physical - they're the ascent into higher consciousness.

Structuralist: Both miss the point - this follows the pattern because
Nietzsche deliberately invokes the hero's journey structure that his
audience would recognize.

ROUND 3:

Literalist: Historical context shows Zoroaster did retreat to mountains
for meditation. This isn't pure invention.

Symbolist: And that historical pattern became archetypal precisely because
it represents universal psychological truth about spiritual transformation.

Structuralist: Exactly - the structure works because it mirrors real
patterns of human development, both historical and psychological.
```

### Step 3: Node Creation

```python
detector = NodeCreationDetector()
should_create, node_type, reason = detector.should_create_node(
    main_transcript,
    branch_question=None
)
```

**Detection result:**
- Turns: 9 (3 agents × 3 rounds)
- Explicit markers: None found
- Repetition: Low (agents maintaining positions but developing)
- Max turns: Not reached
- **Decision: NO, not yet complete** (still developing)

Actually, for MVP we'd force completion after 3 rounds:

**Revised decision: YES, create node**
- Type: EXPLORATION (no clear resolution)
- Reason: "Debate complete, no synthesis reached"

```python
factory = NodeFactory()
node_1 = factory.create_node_from_debate(
    turns=main_transcript,
    source_passage=passage1,
    branch_question=None
)
```

**Node 1 created:**
```
node_id: "f3a829bc"
node_type: EXPLORATION
topic: "Interpretation of Zarathustra's departure at thirty: literal,
        symbolic, or structural?"
resolution: "Three perspectives emerged without synthesis. Literalist
            grounds it in historical biography, Symbolist sees archetypal
            psychological transformation, Structuralist identifies narrative
            pattern. Final exchange suggests these may be complementary
            rather than exclusive."
theme_tags: {"zarathustra", "departure", "thirty-years", "mountains",
             "literal-vs-symbolic", "hero-journey"}
key_claims: [
    "Zarathustra's departure at thirty is historically grounded",
    "Mountains symbolize transcendence and higher consciousness",
    "The narrative follows monomyth structure",
    "Historical and symbolic readings may be complementary"
]
```

### Step 4: Branch Point Detection

```python
from dialectic_poc import identify_branch_point

branch_q = identify_branch_point(
    main_transcript,
    passage1,
    observer=phenomenologist
)
```

**Observer (Phenomenologist) identifies:**
```
"What is the qualitative character of Zarathustra's first-person
experience at the moment of leaving home?"
```

### Step 5: Branch Debate

```
ROUND 1:

Literalist: We can't access his subjective experience - we only have
the external fact of departure. First-person qualia are unavailable
to historical analysis.

Symbolist: The experience is one of liberation tinged with loss -
leaving the familiar (home/lake) creates both exhilaration and grief.
This is the felt sense of transformation.

Structuralist: The text doesn't give us interiority here - it's
deliberately external narration. We can't psychologize what isn't present.

ROUND 2:

Literalist: Agreed with Structuralist - the passage is description, not
introspection. The phenomenology is simply not accessible from this text.

Symbolist: But the choice of words implies experience - "left" suggests
agency, "mountains" implies orientation toward elevation. The text carries
phenomenological weight even without explicit first-person narration.

Structuralist: That's projection, not interpretation. The structure is
mythic precisely because it transcends individual experience.
```

**Detection:**
- Question-answer check: LLM judges "YES, adequately addressed"
- Type: QUESTION
- Resolution: Perspectives on whether first-person experience is accessible

```python
branch_node = factory.create_node_from_debate(
    turns=branch_transcript,
    source_passage=passage1,
    branch_question=branch_q
)
```

**Node 2 created:**
```
node_id: "a8b3c4d5"
node_type: QUESTION
topic: "Branch: What is the qualitative character of Zarathustra's
        first-person experience at the moment of leaving home?"
resolution: "Sharp disagreement on accessibility of phenomenology.
            Literalist/Structuralist: text provides no first-person
            access. Symbolist: language choices imply experiential
            qualities. Impasse on whether subjective experience can
            be inferred from external description."
theme_tags: {"phenomenology", "first-person", "experience",
             "zarathustra", "subjectivity"}
key_claims: [
    "Historical text cannot access subjective qualia",
    "Language choices imply phenomenological content",
    "Mythic structure transcends individual experience"
]
```

### Step 6: Edge Detection

```python
detector = EdgeDetector()
edges = detector.detect_edges_for_new_node(branch_node, session.dag)
```

**Automatic BRANCHES_FROM edge:**
```
Edge(
    from_node_id="a8b3c4d5",  # Branch node
    to_node_id="f3a829bc",    # Main node
    edge_type=BRANCHES_FROM,
    description="Explores: What is the qualitative character...",
    confidence=1.0,
    detected_by="system"
)
```

**No other edges detected** (only one other node, insufficient similarity)

### Step 7: Save State

```python
session.dag.save(Path("zarathustra_prologue_graph.json"))
```

**Current state:**
- DAG: 2 nodes, 1 edge
- Graph structure:
  ```
  Node_1 (EXPLORATION)
     ↑
     │ BRANCHES_FROM
     │
  Node_2 (QUESTION)
  ```

---

## Passage 2: "Ten years he enjoyed his spirit..."

### Input

```
Passage: "Ten years he enjoyed his spirit and his solitude here
         and did not tire of it."
```

### Step 1: Context Retrieval

```python
relevant = retriever.get_relevant_context(passage2, [])
```

**Similarity scoring:**
```
Query words: {ten, years, enjoyed, spirit, solitude, tire}

Node f3a829bc (Node_1):
  Words: {zarathustra, departure, thirty, years, mountains, literal,
          symbolic, hero, journey, transformation}
  Intersection: {years}
  Similarity: 0.09 (below threshold 0.3)

Node a8b3c4d5 (Node_2):
  Words: {phenomenology, first-person, experience, zarathustra,
          qualitative, subjective}
  Intersection: {} (none)
  Similarity: 0.0
```

**Result:** No relevant nodes found (similarities too low)

### Step 2: Run Main Debate

```
ROUND 1:

Literalist: This describes the duration of Zarathustra's mountain retreat
- ten years of solitary contemplation before returning to humanity. A
concrete time period.

Symbolist: Ten years represents complete cycle of inner development.
"Enjoyed his spirit" means self-communion. The solitude is not loneliness
but fullness.

Structuralist: Standard mentor/sage preparation period. Think Obi-Wan
on Tatooine, Gandalf researching in Minas Tirith - the wise figure must
withdraw before they can teach.

ROUND 2:

Literalist: The specific number ten may be arbitrary, but the emphasis
on duration matters - this wasn't a brief retreat but sustained isolation.

Symbolist: Nothing in Nietzsche is arbitrary. Ten suggests completeness,
fulfillment. "Did not tire" means the experience remained vital throughout.

Structuralist: The duration creates narrative weight - when he finally
descends, we know this wisdom wasn't hastily acquired.

ROUND 3:

Literalist: We converge on duration as significant, whether literal or
symbolic.

Symbolist: Yes - the long gestation was necessary for whatever transformation
occurred.

Structuralist: Agreed. The time establishes credibility for what comes next.
```

### Step 3: Node Creation

**Detection:**
- Final turns show convergence language: "we converge", "agreed"
- Type: **SYNTHESIS**

```python
node_3 = factory.create_node_from_debate(main_transcript2, passage2)
```

**Node 3 created:**
```
node_id: "e7f1a2b3"
node_type: SYNTHESIS
topic: "Duration and significance of Zarathustra's ten-year solitude"
resolution: "All three perspectives agree on the importance of duration,
            though differing on whether it's literal time, symbolic
            completeness, or narrative necessity. Common ground: the
            extended period establishes depth and credibility for
            Zarathustra's subsequent teaching. The solitude was productive
            rather than empty."
theme_tags: {"solitude", "duration", "ten-years", "preparation",
             "zarathustra", "withdrawal"}
key_claims: [
    "Ten years represents sustained rather than brief retreat",
    "Duration may be literal, symbolic, or narratively functional",
    "Extended solitude establishes credibility",
    "The period was fulfilling rather than tedious"
]
```

### Step 4: Edge Detection

**Check for CONTRADICTS:**
- Node 3 is SYNTHESIS (not IMPASSE)
- No CONTRADICTS edges created

**Check for ELABORATES:**
```
Node_3 tags: {solitude, duration, ten-years, preparation, zarathustra,
              withdrawal}
Node_1 tags: {zarathustra, departure, thirty-years, mountains,
              literal-vs-symbolic, hero-journey}

Shared tags: {zarathustra}
Count: 1 (need 3 for ELABORATES)
```
- Insufficient overlap for automatic edge

**Check manually with LLM:**
```python
suggestions = detector.suggest_manual_edges("e7f1a2b3", session.dag)
```

**LLM suggestion:**
```
RELATIONSHIP: ELABORATES
REASONING: Node 3 describes what happened after the departure in Node 1,
           filling in the ten years Zarathustra spent in mountains.
```

**Edge created:**
```
Edge(
    from_node_id="e7f1a2b3",
    to_node_id="f3a829bc",
    edge_type=ELABORATES,
    description="Describes the ten years following departure",
    confidence=0.8,
    detected_by="llm-suggested"
)
```

**Current state:**
- DAG: 3 nodes, 2 edges
- Graph structure:
  ```
  Node_1 (EXPLORATION)
    ↑      ↑
    │      │ ELABORATES
    │      │
  Node_2  Node_3 (SYNTHESIS)
  ```

---

## Passage 3: "At last his heart transformed..."

### Input

```
Passage: "At last his heart transformed, and one morning he rose
         with the dawn, stepped before the sun, and spoke to it thus:"
```

### Step 1: Context Retrieval

```python
relevant = retriever.get_relevant_context(passage3, [])
```

**Similarity scoring:**
```
Query words: {heart, transformed, morning, rose, dawn, stepped, sun, spoke}

Node e7f1a2b3 (Node_3):
  Words: {solitude, duration, ten-years, preparation, zarathustra,
          withdrawal, sustained, credibility}
  Shared: {} → Similarity: 0.0

Node f3a829bc (Node_1):
  Words: {zarathustra, departure, thirty-years, mountains, literal,
          symbolic, transformation, hero, journey}
  Shared: {transformed/transformation} → Similarity: 0.12

Node a8b3c4d5 (Node_2):
  Words: {phenomenology, first-person, experience, zarathustra}
  Shared: {} → Similarity: 0.0
```

**Result:** No nodes above threshold, but Node_1 has weak relevance

**Context injected (weak match):**
```
RELEVANT PAST DISCUSSIONS:
- Interpretation of Zarathustra's departure at thirty: literal,
  symbolic, or structural?
  → Three perspectives emerged without synthesis...
```

### Step 2: Run Main Debate (with context)

```
ROUND 1:

Literalist: "His heart transformed" describes an internal change, but
"one morning" grounds it in specific time. The transformation culminates
in action - speaking to the sun is a literal religious ritual.

Symbolist: The heart transformation is the completion of inner alchemy.
Dawn/sun represents enlightenment. Speaking to the sun is addressing the
principle of illumination - he's ready to become a teacher.

Structuralist: This is the Return from Special World - transformation
complete, hero brings gift back. The sun speech initiates the descent
from mountains to humanity.

ROUND 2:

Literalist: But was the transformation sudden ("at last... one morning")
or gradual across ten years? The text is ambiguous.

Symbolist: The ten years were gradual preparation, "at last" marks the
sudden breakthrough. Like water heated to boiling - long process, instant
phase change.

Structuralist: Narrative requires both - slow accumulation and decisive
moment. The pattern is ancient: long preparation, sudden call to action.

ROUND 3:

Literalist: I maintain the suddenness is suspect - transformations in
real life are gradual.

Symbolist: But phenomenologically, realizations do feel sudden even when
prepared by long process.

Structuralist: The debate itself proves the text supports both readings
- it's deliberately ambiguous.
```

### Step 3: Node Creation

**Detection:**
- No explicit synthesis markers
- No clear convergence
- Agents maintain disagreement about sudden vs. gradual
- Type: **IMPASSE**

```python
node_4 = factory.create_node_from_debate(main_transcript3, passage3)
```

**Node 4 created:**
```
node_id: "c9d2e3f4"
node_type: IMPASSE
topic: "Nature of Zarathustra's transformation: sudden or gradual?"
resolution: "Irreconcilable disagreement about temporal structure of
            transformation. Literalist: transformations are gradual in
            reality, text is romanticized. Symbolist: long preparation
            enables sudden realization, phenomenologically accurate.
            Structuralist: text deliberately supports both readings.
            Core tension: whether 'at last... one morning' indicates
            instant change or culmination of process."
theme_tags: {"transformation", "sudden-vs-gradual", "heart", "dawn",
             "zarathustra", "time", "change"}
key_claims: [
    "Transformations in reality are gradual, not sudden",
    "Sudden realization can follow long preparation",
    "Text deliberately maintains ambiguity",
    "Phenomenology of change differs from objective process"
]
```

### Step 4: Edge Detection

**Check for CONTRADICTS:**
```
Node_4 type: IMPASSE ✓
Node_3 tags: {solitude, duration, ten-years, preparation...}
Node_4 tags: {transformation, sudden-vs-gradual, heart, dawn...}

Shared: {preparation} (implicitly), but only 1 explicit tag match
```

**LLM check for contradiction:**
```
Node 3 (SYNTHESIS): "Extended solitude was necessary preparation"
Node 4 (IMPASSE): "Unclear if transformation was sudden or gradual"

RELATIONSHIP: ELABORATES (not CONTRADICTS)
REASONING: Node 4 explores the nature of the transformation that was
           prepared during the period described in Node 3. They address
           different questions (duration of preparation vs. mechanism
           of change).
```

**Edge created:**
```
Edge(
    from_node_id="c9d2e3f4",
    to_node_id="e7f1a2b3",
    edge_type=ELABORATES,
    description="Explores the transformation following the preparation period",
    confidence=0.7,
    detected_by="llm-suggested"
)
```

**Also check against Node_1:**
```
Shared tags: {transformation, zarathustra}
Count: 2

Both involve interpretation debates (literal/symbolic)
Weak ELABORATES potential
```

**Second edge created:**
```
Edge(
    from_node_id="c9d2e3f4",
    to_node_id="f3a829bc",
    edge_type=ELABORATES,
    description="Continues interpretive debate from earlier passage",
    confidence=0.5,
    detected_by="automatic"
)
```

**Final state after 3 passages:**
- DAG: 4 nodes, 4 edges
- Graph structure:
  ```
       Node_1 (EXPLORATION)
      ↗    ↑      ↑
     /     │      │ ELABORATES
    /      │      │
  Node_2  Node_3 (SYNTHESIS)
              ↑
              │ ELABORATES
              │
          Node_4 (IMPASSE)
  ```

---

## Linearization Output

```python
linearizer = LinearizationEngine(session.dag)
markdown = linearizer.render_as_markdown()
```

**Topological sort order:**
```
1. Node_1 (f3a829bc) - root (no incoming edges)
2. Node_2 (a8b3c4d5) - branches from Node_1
3. Node_3 (e7f1a2b3) - elaborates Node_1
4. Node_4 (c9d2e3f4) - elaborates Node_3 and Node_1
```

**Rendered markdown (excerpt):**

```markdown
# Dialectical Debate Graph

**Generated:** 2025-11-15 14:30
**Nodes:** 4
**Edges:** 4

---

## 1. Interpretation of Zarathustra's departure at thirty

*Type: exploration | Created: 2025-11-15 14:15*

**Tags:** departure, hero-journey, literal-vs-symbolic, mountains,
thirty-years, zarathustra

> When Zarathustra was thirty years old, he left his home and the
> lake of his home, and went into the mountains.

**Resolution:**

Three perspectives emerged without synthesis. Literalist grounds it
in historical biography of Zoroaster, Symbolist sees archetypal
psychological transformation, Structuralist identifies monomyth
narrative pattern. Final exchange suggests these may be complementary
rather than exclusive frameworks for understanding the passage.

**Key Claims:**

- Zarathustra's departure at thirty is historically grounded in
  Persian tradition
- Mountains symbolize transcendence and higher consciousness
- The narrative follows hero's journey structure
- Historical and symbolic readings may be complementary

**Relationships:**

*Leads to:*
- [branches_from] What is the qualitative character of Zarathustra's...
- [elaborates] Duration and significance of Zarathustra's ten-year...
- [elaborates] Nature of Zarathustra's transformation: sudden or...

<details>
<summary>Full Debate Transcript (9 turns)</summary>

**Literalist** (Round 1):
This describes a historical event - Zarathustra (Zoroaster) left his
birthplace at age thirty to begin his spiritual mission...

[... full transcript ...]

</details>

---

## 2. What is the qualitative character of Zarathustra's first-person experience?

*Type: question | Created: 2025-11-15 14:18*

**Tags:** experience, first-person, phenomenology, subjectivity, zarathustra

> When Zarathustra was thirty years old, he left his home and the
> lake of his home, and went into the mountains.

**Resolution:**

Sharp disagreement on accessibility of phenomenology from external
narrative. Literalist and Structuralist argue the text provides no
first-person access to subjective experience. Symbolist maintains
language choices imply experiential qualities. Fundamental impasse
on whether subjective qualia can be inferred from third-person
description.

**Key Claims:**

- Historical text cannot access subjective qualia
- Language choices imply phenomenological content
- Mythic structure transcends individual experience

**Relationships:**

*Builds on:*
- [branches_from] Interpretation of Zarathustra's departure at thirty...

---

## 3. Duration and significance of Zarathustra's ten-year solitude

*Type: synthesis | Created: 2025-11-15 14:25*

**Tags:** duration, preparation, solitude, ten-years, withdrawal, zarathustra

> Ten years he enjoyed his spirit and his solitude here and did not
> tire of it.

**Resolution:**

All three perspectives converge on the importance of duration, though
differing on whether it represents literal time, symbolic completeness,
or narrative necessity. Common ground established: the extended period
demonstrates depth and establishes credibility for Zarathustra's
subsequent role as teacher. The solitude was productive and fulfilling
rather than empty or tedious.

**Key Claims:**

- Ten years represents sustained rather than brief retreat
- Duration may be literal, symbolic, or narratively functional
- Extended solitude establishes credibility
- The period was fulfilling rather than tedious

**Relationships:**

*Builds on:*
- [elaborates] Interpretation of Zarathustra's departure at thirty...

*Leads to:*
- [elaborates] Nature of Zarathustra's transformation: sudden or...

---

## 4. Nature of Zarathustra's transformation: sudden or gradual?

*Type: impasse | Created: 2025-11-15 14:30*

**Tags:** change, dawn, heart, sudden-vs-gradual, time, transformation,
zarathustra

> At last his heart transformed, and one morning he rose with the dawn,
> stepped before the sun, and spoke to it thus:

**Resolution:**

Irreconcilable disagreement about temporal structure of transformation.
Literalist maintains transformations in reality are gradual and the text
romanticizes. Symbolist argues long preparation enables phenomenologically
sudden realization. Structuralist claims text deliberately supports both
readings. Core tension unresolved: whether "at last... one morning"
indicates instant phase change or mere culmination marker of gradual
process.

**Key Claims:**

- Transformations in reality are gradual, not sudden
- Sudden realization can follow long preparation (phase change model)
- Text deliberately maintains ambiguity on this point
- Phenomenology of change differs from objective temporal process

**Relationships:**

*Builds on:*
- [elaborates] Duration and significance of Zarathustra's ten-year...
- [elaborates] Interpretation of Zarathustra's departure at thirty...

---
```

---

## Query Example: Finding Related Nodes

```python
# User wants to explore more about "transformation"
query = "How does transformation work?"

similar = session.dag.find_nodes_by_topic(query, threshold=0.3)
```

**Results:**
```
[
    ("c9d2e3f4", 0.67),  # Node 4: "transformation" in topic + tags
    ("f3a829bc", 0.31),  # Node 1: "transformation" in claims
]
```

**Formatted output:**
```
RELATED DISCUSSIONS:

1. Nature of Zarathustra's transformation: sudden or gradual? (67% match)
   → Irreconcilable disagreement about temporal structure...

2. Interpretation of Zarathustra's departure at thirty (31% match)
   → Three perspectives emerged without synthesis...
```

---

## Summary Statistics

After processing 3 passages:

**Graph Metrics:**
- Total nodes: 4
- Node types: 1 EXPLORATION, 1 QUESTION, 1 SYNTHESIS, 1 IMPASSE
- Total edges: 4
- Edge types: 1 BRANCHES_FROM, 3 ELABORATES
- Average tags per node: 5.5
- Average claims per node: 3.25

**Coverage:**
- Passages processed: 3
- Debates generated: 4 (3 main + 1 branch)
- Total turns: 33 (9 + 6 + 9 + 9)
- LLM calls: ~20 (debates + summaries + edge detection)

**Relationships discovered:**
- Node 1 → {Node 2 (branch), Node 3, Node 4} (root of discussion)
- Node 3 → Node 4 (preparation → transformation)
- Shared themes: "zarathustra" (all), "transformation" (2), "time" (2)

**Reading insights:**
- The three passages form a narrative arc: departure → solitude → transformation
- Two unresolved tensions: literal vs. symbolic interpretation, sudden vs. gradual change
- One synthesis reached: importance of duration
- One specialized question explored: accessibility of phenomenology

This demonstrates how the graph captures both the linear narrative flow and the conceptual relationships between ideas across passages.
