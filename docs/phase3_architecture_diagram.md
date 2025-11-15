# Phase 3 Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DIALECTICAL DEBATE SYSTEM                  │
│                           Phase 3: DAG                          │
└─────────────────────────────────────────────────────────────────┘

                              USER
                                │
                                │ reads passage
                                ▼
                        ┌───────────────┐
                        │ DebateSession │
                        │  (orchestr.)  │
                        └───────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Retrieve │    │   Run    │    │  Create  │
        │ Context  │    │  Debate  │    │   Node   │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             │               │               │
        ┌────▼────────────────▼──────────────▼────┐
        │          Core Graph (DebateDAG)         │
        │  ┌──────────────────────────────────┐   │
        │  │    ArgumentNode Storage          │   │
        │  │  {node_id → ArgumentNode}        │   │
        │  └──────────────────────────────────┘   │
        │  ┌──────────────────────────────────┐   │
        │  │    Edge Storage                  │   │
        │  │  [Edge, Edge, Edge, ...]         │   │
        │  └──────────────────────────────────┘   │
        └──────────────┬──────────────────────────┘
                       │
                       │ save/load
                       ▼
                ┌──────────────┐
                │  JSON Files  │
                │  graph.json  │
                │  turns.json  │
                └──────────────┘
```

## Data Flow: Processing a Passage

```
INPUT: New passage text
│
├─ STEP 1: Context Retrieval
│  │
│  ├─ ContextRetriever.get_relevant_context()
│  │  │
│  │  ├─ SimpleSimilarity.find_similar_nodes()
│  │  │  └─ Compare passage to all nodes (Jaccard)
│  │  │
│  │  └─ Returns: [ArgumentNode, ArgumentNode, ...]
│  │
│  └─ ContextRetriever.format_context_for_debate()
│     └─ Returns: formatted context string
│
├─ STEP 2: Run Debate (from dialectic_poc.py)
│  │
│  ├─ Main debate (3 rounds)
│  │  └─ System prompts include retrieved context
│  │
│  ├─ Observer identifies branch point
│  │
│  └─ Branch debate (2 rounds)
│     └─ Returns: List[DebateTurn]
│
├─ STEP 3: Node Creation
│  │
│  ├─ NodeCreationDetector.should_create_node()
│  │  │
│  │  ├─ Check explicit markers
│  │  ├─ Check question answered
│  │  ├─ Detect repetition
│  │  └─ Returns: (bool, NodeType, reason)
│  │
│  └─ NodeFactory.create_node_from_debate()
│     │
│     ├─ _generate_topic() → LLM call
│     ├─ _generate_resolution() → LLM call
│     ├─ _extract_theme_tags() → LLM call
│     ├─ _extract_key_claims() → LLM call
│     │
│     └─ Returns: ArgumentNode
│
├─ STEP 4: Edge Detection
│  │
│  └─ EdgeDetector.detect_edges_for_new_node()
│     │
│     ├─ _find_contradictions()
│     │  └─ Check: shared tags + IMPASSE type
│     │
│     └─ _find_elaborations()
│        └─ Check: shared tags + chronology
│
├─ STEP 5: Update Graph
│  │
│  ├─ DAG.add_node(node)
│  │
│  └─ DAG.add_edge(edge) for each detected edge
│
└─ OUTPUT: ArgumentNode added to persistent graph
```

## Node Structure

```
┌────────────────────────────────────────────────────────────┐
│                     ArgumentNode                           │
├────────────────────────────────────────────────────────────┤
│  Identity                                                  │
│  ├─ node_id: "a3f2b8..."                                  │
│  ├─ node_type: SYNTHESIS | IMPASSE | LEMMA | ...         │
│  └─ created_at: datetime                                   │
├────────────────────────────────────────────────────────────┤
│  Content                                                   │
│  ├─ topic: "Literal vs symbolic interpretation"          │
│  ├─ turns: [DebateTurn, DebateTurn, ...]                 │
│  └─ resolution: "Agents converged on..."                  │
├────────────────────────────────────────────────────────────┤
│  Semantic                                                  │
│  ├─ theme_tags: {"free-will", "causation"}               │
│  ├─ key_claims: ["X implies Y", "Z is problematic"]      │
│  └─ source_passage: "When Zarathustra..."                │
├────────────────────────────────────────────────────────────┤
│  Graph Connections (managed by DAG)                        │
│  ├─ parent_nodes: {node_id1, node_id2}                   │
│  └─ child_nodes: {node_id3, node_id4}                    │
└────────────────────────────────────────────────────────────┘
```

## Edge Types and Meanings

```
Node A ──BRANCHES_FROM──→ Node B
       "A emerged as focused exploration of B"

Node A ──CONTRADICTS──→ Node B
       "A's conclusion conflicts with B's"

Node A ──ELABORATES──→ Node B
       "A adds detail/depth to B's topic"

Node A ──SUPPORTS──→ Node B   [Phase 4]
       "A provides evidence for B"

Node A ──REQUIRES──→ Node B   [Phase 4]
       "A logically depends on B"

Node A ──APPLIES_TO──→ Node B   [Phase 4]
       "A is specific instance of general B"

Node A ──ANALOGY──→ Node B   [Phase 4]
       "A is structurally similar to B"
```

## Linearization Process

```
INPUT: DebateDAG with N nodes

├─ Topological Sort (Kahn's algorithm)
│  │
│  ├─ Calculate in-degree for each node
│  │  (count incoming BRANCHES_FROM + REQUIRES edges)
│  │
│  ├─ Start with nodes having in-degree = 0
│  │
│  ├─ Process nodes, reducing in-degree of neighbors
│  │
│  └─ Returns: [node_id1, node_id2, ..., node_idN]
│
└─ Render as Markdown
   │
   ├─ For each node in order:
   │  │
   │  ├─ Render header (topic, type, timestamp)
   │  ├─ Render metadata (tags, source passage)
   │  ├─ Render resolution
   │  ├─ Render key claims
   │  ├─ Render relationships (incoming/outgoing edges)
   │  └─ Render collapsible transcript
   │
   └─ OUTPUT: Readable narrative document
```

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    Session Start                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │ Load existing │
          │  DAG or new   │
          └───────┬───────┘
                  │
          ┌───────▼────────┐
          │  Process       │◄────┐
          │  Passage       │     │
          └───────┬────────┘     │
                  │              │
          ┌───────▼────────┐     │
          │  Create Node   │     │
          └───────┬────────┘     │
                  │              │
          ┌───────▼────────┐     │
          │  Detect Edges  │     │
          └───────┬────────┘     │
                  │              │
          ┌───────▼────────┐     │
          │  Save DAG      │     │
          └───────┬────────┘     │
                  │              │
          ┌───────▼────────┐     │
          │  More passages?├─YES─┘
          └───────┬────────┘
                  │ NO
                  ▼
          ┌───────────────┐
          │  Export       │
          │  Narrative    │
          └───────────────┘
```

## Component Dependencies

```
┌──────────────────────────────────────────────────────────┐
│                    dialectic_poc.py                      │
│  (Existing Phase 0/2 code)                               │
│  ├─ Agent, Observer, DebateTurn                         │
│  ├─ run_debate()                                         │
│  ├─ identify_branch_point()                             │
│  └─ llm_call()                                           │
└──────────────────┬───────────────────────────────────────┘
                   │ imports
                   ▼
┌──────────────────────────────────────────────────────────┐
│              phase3_dag.py (NEW)                         │
│  ├─ ArgumentNode                                         │
│  ├─ Edge                                                 │
│  └─ DebateDAG                                            │
└──────────────────┬───────────────────────────────────────┘
                   │ used by
         ┌─────────┼─────────┐
         ▼         ▼         ▼
┌─────────────┐ ┌──────────┐ ┌──────────────┐
│phase3_nodes │ │ phase3_  │ │   phase3_    │
│    .py      │ │edges.py  │ │linearize.py  │
│             │ │          │ │              │
│NodeCreation-│ │Edge-     │ │Linearization-│
│Detector     │ │Detector  │ │Engine        │
│NodeFactory  │ │          │ │              │
└─────────────┘ └──────────┘ └──────────────┘
         │         │                │
         └─────────┼────────────────┘
                   │ used by
                   ▼
         ┌─────────────────────┐
         │ phase3_similarity.py│
         │                     │
         │ SimpleSimilarity    │
         │ ContextRetriever    │
         └──────────┬──────────┘
                    │ used by
                    ▼
         ┌─────────────────────┐
         │ phase3_session.py   │
         │                     │
         │ DebateSession       │
         │ (Main orchestrator) │
         └─────────────────────┘
```

## Similarity Comparison Flow

```
Query: "What is the nature of time?"

                    │
                    ▼
        ┌────────────────────────┐
        │   Extract Content      │
        │   Words                │
        │                        │
        │ {"nature", "time"}     │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │   For each node in DAG:│
        │                        │
        │   Node A: {"time",     │
        │   "causation", "flow"} │
        │   → Jaccard: 0.33      │
        │                        │
        │   Node B: {"free-will",│
        │   "choice", "future"}  │
        │   → Jaccard: 0.14      │
        │                        │
        │   Node C: {"temporal", │
        │   "sequence", "time"}  │
        │   → Jaccard: 0.40      │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │   Filter by threshold  │
        │   (>= 0.3)             │
        │                        │
        │   Keep: Node A, Node C │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │   Sort by score        │
        │                        │
        │   1. Node C (0.40)     │
        │   2. Node A (0.33)     │
        └───────────┬────────────┘
                    │
                    ▼
             Top K results
             (inject as context)
```

## Example Graph After 3 Passages

```
Passage 1: "When Zarathustra was thirty..."

    Node_1 (EXPLORATION)
    Topic: "Age and maturity in spiritual journey"
         │
         │ BRANCHES_FROM
         ▼
    Node_2 (QUESTION)
    Topic: "Significance of thirty years"

─────────────────────────────────────────

Passage 2: "Ten years in solitude..."

    Node_3 (SYNTHESIS)
    Topic: "Solitude as preparation"
         │
         │ ELABORATES
         ▼
    Node_1 (EXPLORATION)

─────────────────────────────────────────

Passage 3: "His heart transformed..."

    Node_4 (IMPASSE)
    Topic: "Transformation: sudden vs gradual"
         │
         │ CONTRADICTS
         ▼
    Node_3 (SYNTHESIS)
         │
         │ ELABORATES
         ▼
    Node_1 (EXPLORATION)

─────────────────────────────────────────

Final Graph:

       Node_1
      /   |   \\
     /    |    \\
  Node_2 Node_3 Node_4
           |
         (contradicts)
           |
         Node_4
```

## Persistence Format

```
debate_graph.json
├─ nodes: {
│    "a3f2b8": {
│      "node_id": "a3f2b8",
│      "node_type": "synthesis",
│      "topic": "...",
│      "resolution": "...",
│      "theme_tags": ["tag1", "tag2"],
│      "key_claims": ["claim1", "claim2"],
│      "parent_nodes": ["b4e1c2"],
│      "child_nodes": [],
│      "turn_count": 6
│    },
│    ...
│  }
├─ edges: [
│    {
│      "from_node_id": "a3f2b8",
│      "to_node_id": "b4e1c2",
│      "edge_type": "elaborates",
│      "description": "...",
│      "confidence": 0.8
│    },
│    ...
│  ]
└─ metadata: {
     "created_at": "2025-11-15T...",
     "node_count": 15,
     "edge_count": 12
   }

debate_graph_turns.json
└─ {
     "a3f2b8": [
       {"agent": "Literalist", "content": "...", "round": 1},
       {"agent": "Symbolist", "content": "...", "round": 1},
       ...
     ],
     ...
   }
```

## Key Algorithms

### 1. Semantic Completion Detection
```
Input: List[DebateTurn]
│
├─ Check: len(turns) >= min_turns (4)?
│  └─ NO → return False (not complete)
│
├─ Check: len(turns) >= max_turns (12)?
│  └─ YES → return True, EXPLORATION (force completion)
│
├─ Check: explicit markers in recent turns?
│  ├─ "we agree" → return True, SYNTHESIS
│  ├─ "irreconcilable" → return True, IMPASSE
│  └─ "to clarify" → return True, CLARIFICATION
│
├─ Check: question answered? (for branches)
│  └─ LLM judges → return True/False, QUESTION
│
└─ Check: repetition detected?
   └─ Word overlap > 0.6 → return True, IMPASSE
```

### 2. Edge Detection
```
Input: new_node, existing_DAG
│
├─ Find CONTRADICTS candidates
│  │
│  └─ For each existing node:
│     ├─ Check: shared tags >= 2?
│     ├─ Check: both are IMPASSE or SYNTHESIS?
│     └─ YES → create CONTRADICTS edge
│
└─ Find ELABORATES candidates
   │
   └─ For each existing node:
      ├─ Check: shared tags >= 3?
      ├─ Check: new_node.created_at > node.created_at?
      └─ YES → create ELABORATES edge
```

### 3. Context Retrieval
```
Input: passage_text, current_turns
│
├─ Combine: query = passage + recent_turns
│
├─ For each node in DAG:
│  ├─ Compute similarity(query, node)
│  └─ Store (node_id, score)
│
├─ Filter: score >= threshold (0.3)
│
├─ Sort by score descending
│
└─ Return top K nodes (3)
```
