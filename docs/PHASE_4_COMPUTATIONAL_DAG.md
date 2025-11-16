# Phase 4: Computational DAG Architecture

## Overview

Phase 4 transforms the debate system from a linear tree structure into a true computational directed acyclic graph (DAG) with:
- Real-time observer monitoring during debates
- Multiple branch points flagged and prioritized
- Parallel branch exploration with cross-awareness
- Automatic branch merging at convergence points
- Stub preservation for deferred exploration
- Discontinuity as a strength (revisiting with new context)

## Design Principles

### 1. Full Autonomy
The system runs completely autonomously without user intervention:
- Observers automatically flag tensions as they emerge
- Branch selection uses automatic strategies (diverse, urgent, deep, meta)
- Merge detection and creation is automatic
- Stub revisiting is automatic when context makes them relevant

**Rationale:** This will be part of a larger autonomous system. Manual intervention doesn't scale.

### 2. Parallel Execution Model
Branches are explored in parallel (conceptually):
- Multiple branches run with awareness of each other
- Each branch knows what else is being explored
- Context includes: parent debate, sibling branches, unexplored stubs
- No sequential dependency (A doesn't need to finish before B starts)

**Rationale:** Mimics how multiple lines of inquiry can be pursued simultaneously.

### 3. Discontinuity as Strength
Returning to stubbed questions later with different context is a feature, not a bug:
- Stubs preserve unexplored tensions
- As DAG grows, context changes
- A stub that seemed unimportant early may become crucial later
- Revisiting with new perspective mirrors human thought

**Rationale:** Real thinking isn't linear. We come back to questions with new understanding.

### 4. Full DAG Commitment
No backward compatibility with simple tree mode:
- DAG structure is the only mode
- Nodes can have multiple parents (merge points)
- Edges represent: branches_from, merges_into, contradicts, elaborates
- Graph can have cycles of reference (A references B which references A)

**Rationale:** Half-measures create complexity without benefits. Commit fully.

## Architecture Changes

### Current (Phase 3): Linear Tree
```
Main Debate (3 rounds)
  ↓ [completes]
Observer generates question(s)
  ↓ [after completion]
Branch(es) explored sequentially
  ↓
Done
```

**Limitations:**
- Observers only see completed debates
- One branch at a time
- No cross-branch awareness
- No merge points
- No stubs (unexplored tensions lost)

### Phase 4: Computational DAG
```
Main Debate
  ├─ Turn 1 → Observer flags tension T1
  ├─ Turn 2 → Observer flags tension T2, T3
  ├─ Turn 3 → Observer flags tension T4, T5, T6
  ↓
[Main debate completes, creates Node M]

Branch Selection (automatic)
  Flagged: T1, T2, T3, T4, T5, T6 (6 tensions)
  Selected: T2, T4, T5 (diverse strategy, max 3)
  Stubbed: T1, T3, T6 (preserved for later)
  ↓
Parallel Branch Exploration
  Branch B2 (from T2) ←─┐
  Branch B4 (from T4)   ├─ cross-aware
  Branch B5 (from T5) ←─┘

  Each branch context includes:
  - Parent debate (Node M)
  - Other active branches (B2, B4, B5)
  - Stubbed tensions (T1, T3, T6)
  ↓
Merge Detection (automatic)
  Semantic similarity: B2 ≈ B4 (threshold > 0.7)
  Create merge node: Node S (synthesizes B2 + B4)
  Edges: B2 → S, B4 → S (type: MERGES_INTO)
  ↓
Stub Revisiting (automatic)
  Current context: Nodes M, B2, B4, B5, S
  Check stub T3: "Is this now relevant?"
  → Yes: Explore as new branch B3
  → No: Keep as stub
  ↓
Rich DAG Structure
  Node M (main)
    ├─→ Node B2 ─┐
    ├─→ Node B4 ─┴→ Node S (merge)
    ├─→ Node B5
    └─→ Node B3 (from revisited stub)

  Stubs: T1, T6 (still unexplored)
```

## Component Specifications

### 1. Real-Time Observer Monitoring

**File:** `src/debate_monitor.py`

**Components:**
- `TensionFlag` - Data class for flagged tensions
  - `turn_number: int` - When this was flagged
  - `question: str` - The branch question
  - `observer_name: str` - Who flagged it
  - `urgency: float` - Score 0.0-1.0
  - `context_excerpt: str` - What triggered it
  - `rationale: str` - Why observer flagged this

- `DebateMonitor` - Watches debates in real-time
  - `observers: List[Observer]` - Observers watching
  - `flagged_tensions: List[TensionFlag]` - All flagged tensions
  - `process_turn(turn, transcript) -> List[TensionFlag]` - Check after each turn

**Observer Changes:**
Add methods to `Observer` class in `dialectic_poc.py`:
- `check_for_tension(turn, transcript) -> Optional[Dict]` - Real-time tension detection
- `rate_urgency(tension, transcript) -> float` - Score urgency 0.0-1.0

**Behavior:**
- After each turn, each observer checks for tensions
- Observer uses LLM to detect if current turn reveals gap/assumption/tension
- Not all turns generate flags (threshold for significance)
- Multiple observers may flag the same turn (different angles)

### 2. Branch Selection & Prioritization

**File:** `src/branch_selector.py`

**Components:**
- `BranchSelector` - Chooses which tensions to explore
  - `select_branches(tensions, max_branches, strategy) -> (selected, stubbed)`
  - Strategies:
    - `"diverse"` - Maximize difference between selected branches (default)
    - `"urgent"` - Highest urgency scores first
    - `"deep"` - Prioritize questions likely to spawn sub-branches
    - `"meta"` - Prioritize questions about the debate itself

**Diversity Calculation:**
- Use LLM to compute semantic distance between questions
- Greedy selection: pick first, then pick most different from selected, repeat
- Ensures selected branches explore genuinely different angles

**Defaults:**
- `max_branches = 3` - Don't explore more than 3 branches per node
- `strategy = "diverse"` - Maximize coverage of question space
- `urgency_threshold = 0.3` - Don't flag tensions below this

### 3. Branch Stubs (Unexplored Tensions)

**File:** `src/branch_stub.py`

**Components:**
- `BranchStub` - Represents an unexplored tension
  - `stub_id: str` - Unique identifier
  - `question: str` - The branch question
  - `parent_node_id: str` - Where this would branch from
  - `flagged_at_turn: int` - When observer flagged it
  - `observer_name: str` - Who flagged it
  - `urgency: float` - Original urgency score
  - `status: str` - "stub", "explored", "superseded"
  - `created_at: datetime` - When flagged
  - `revisit_checks: List[Dict]` - History of revisit checks

- `should_revisit(current_dag) -> (bool, reason)` - Check if now relevant
  - LLM compares stub question to current DAG nodes
  - Returns (True, reason) if stub now seems important given new context
  - Updates `revisit_checks` history

**Lifecycle:**
1. **Created** - Tension flagged but not selected for immediate exploration
2. **Stubbed** - Stored in `DAG.stubs`
3. **Checked** - Periodically (after each new node) check if now relevant
4. **Explored** - If relevant, becomes a new branch; status → "explored"
5. **Superseded** - If another node addresses it; status → "superseded"

**Revisit Triggers:**
- After each new node is added to DAG
- When merge nodes are created (new synthesis may make stub relevant)
- When sub-branches complete (new depth may need stub)

### 4. Cross-Branch Awareness

**Modified:** `src/session.py`

**Context Enhancement:**
When running branch debates, include rich context:

```python
def run_branch_with_awareness(
    branch_question: str,
    parent_node: ArgumentNode,
    other_branches: List[ArgumentNode],
    stubs: List[BranchStub],
    agents: List[Agent]
) -> ArgumentNode:
    """
    Run branch debate with full DAG awareness
    """

    context = f"""
CONTEXT FOR THIS BRANCH:

PARENT DEBATE:
Topic: {parent_node.topic}
Resolution: {parent_node.resolution}

OTHER BRANCHES BEING EXPLORED IN PARALLEL:
{format_other_branches(other_branches)}

UNEXPLORED TENSIONS (stubs we chose not to pursue):
{format_stubs(stubs)}

YOUR BRANCH QUESTION:
{branch_question}

You are exploring this question with awareness of the broader inquiry.
Reference other branches if relevant. Note if this connects to unexplored stubs.
"""

    # Run debate with this enriched context
```

**Agent Turn Generation:**
First turn of branch includes full context. Subsequent turns maintain awareness.

**Benefits:**
- Branches can reference each other's findings
- Agents can note "this relates to [other branch]"
- Explicit awareness prevents redundant exploration
- Creates natural merge opportunities

### 5. Branch Merging

**File:** `src/branch_merger.py`

**Components:**
- `MergeOpportunity` - Data class for potential merges
  - `branches: List[str]` - Node IDs to merge
  - `similarity: float` - Semantic similarity score
  - `reason: str` - Why these should merge
  - `synthesis_preview: str` - What merged insight would be

- `BranchMerger` - Detects and creates merges
  - `find_merge_opportunities(branches, threshold=0.7) -> List[MergeOpportunity]`
  - `create_merge_node(branches, reason) -> ArgumentNode`

**Merge Detection:**
1. After branches complete, compare them pairwise
2. Compute semantic similarity (LLM-based)
   - Compare resolutions, key claims, theme tags
   - Score 0.0 (completely different) to 1.0 (identical)
3. If similarity > threshold (0.7), flag as merge opportunity
4. Generate synthesis preview (what would merged node say?)

**Merge Node Creation:**
- `NodeType.SYNTHESIS` (existing type, used for merges)
- Topic: "Synthesis: [reason for merge]"
- Resolution: LLM-generated synthesis of merged branches
- Theme tags: Union of both branches' tags
- Key claims: Synthesized from both branches
- Edges: Both parent branches → merge node (type: MERGES_INTO)

**Automatic Execution:**
All detected merge opportunities are automatically executed. No user approval needed.

### 6. Execution Flow

**Modified:** `src/session.py`, `app.py`

**New Execution Phases:**

```python
class DebatePhase(Enum):
    MAIN_DEBATE = "main_debate"
    SELECTING_BRANCHES = "selecting_branches"
    EXPLORING_BRANCHES = "exploring_branches"
    DETECTING_MERGES = "detecting_merges"
    REVISITING_STUBS = "revisiting_stubs"
    COMPLETE = "complete"

def run_autonomous_debate_session(
    passage: str,
    agents: List[Agent],
    observers: List[Observer],
    max_main_rounds: int = 3,
    max_branches: int = 3,
    selection_strategy: str = "diverse",
    merge_threshold: float = 0.7
) -> DebateDAG:
    """
    Fully autonomous debate session with DAG construction
    """

    # Initialize components
    monitor = DebateMonitor(observers)
    selector = BranchSelector()
    merger = BranchMerger()
    dag = DebateDAG()

    # Phase 1: Main Debate with Real-Time Monitoring
    print("\n=== PHASE 1: MAIN DEBATE ===")
    main_transcript = []

    for round_num in range(max_main_rounds):
        for agent in agents:
            turn = generate_agent_turn(agent, main_transcript, passage)
            main_transcript.append(turn)

            # Observers watch in real-time
            new_flags = monitor.process_turn(turn, main_transcript)
            if new_flags:
                print(f"  ⚠ {len(new_flags)} tension(s) flagged at turn {len(main_transcript)}")

    # Create main node
    main_node = create_node_from_transcript(main_transcript, passage)
    dag.add_node(main_node)
    print(f"  ✓ Created main node: {main_node.node_id}")

    # Phase 2: Branch Selection
    print(f"\n=== PHASE 2: BRANCH SELECTION ===")
    print(f"Observers flagged {len(monitor.flagged_tensions)} tensions")

    selected, stubbed = selector.select_branches(
        monitor.flagged_tensions,
        max_branches=max_branches,
        strategy=selection_strategy
    )

    print(f"Selected {len(selected)} to explore, {len(stubbed)} stubbed")

    # Store stubs
    for tension_flag in stubbed:
        stub = BranchStub.from_tension_flag(tension_flag, main_node.node_id)
        dag.stubs.append(stub)
        print(f"  📌 Stubbed: {stub.question[:60]}...")

    # Phase 3: Parallel Branch Exploration
    print(f"\n=== PHASE 3: EXPLORING BRANCHES ===")
    branch_nodes = []

    for i, tension_flag in enumerate(selected, 1):
        print(f"\n[{i}/{len(selected)}] Exploring: {tension_flag.question}")

        branch_node = run_branch_with_awareness(
            branch_question=tension_flag.question,
            parent_node=main_node,
            other_branches=branch_nodes,  # Already-explored branches
            stubs=dag.stubs,
            agents=agents
        )

        dag.add_node(branch_node)
        dag.add_edge(Edge(
            from_node_id=main_node.node_id,
            to_node_id=branch_node.node_id,
            edge_type=EdgeType.BRANCHES_FROM,
            description=tension_flag.question[:100]
        ))

        branch_nodes.append(branch_node)
        print(f"  ✓ Created branch node: {branch_node.node_id}")

    # Phase 4: Merge Detection
    print(f"\n=== PHASE 4: DETECTING MERGES ===")
    merge_opportunities = merger.find_merge_opportunities(
        branch_nodes,
        threshold=merge_threshold
    )

    print(f"Found {len(merge_opportunities)} merge opportunities")

    for merge_opp in merge_opportunities:
        print(f"  🔗 Merging: {merge_opp.reason}")

        merge_node = merger.create_merge_node(
            branches=[dag.get_node(nid) for nid in merge_opp.branches],
            reason=merge_opp.reason
        )

        dag.add_node(merge_node)

        # Add edges from each merged branch to merge node
        for branch_id in merge_opp.branches:
            dag.add_edge(Edge(
                from_node_id=branch_id,
                to_node_id=merge_node.node_id,
                edge_type=EdgeType.MERGES_INTO,
                description=f"Merged: {merge_opp.reason[:100]}"
            ))

        print(f"  ✓ Created merge node: {merge_node.node_id}")

    # Phase 5: Stub Revisiting
    print(f"\n=== PHASE 5: REVISITING STUBS ===")
    newly_explored = []

    for stub in dag.stubs:
        if stub.status != "stub":
            continue

        should_explore, reason = stub.should_revisit(dag)

        if should_explore:
            print(f"  🔄 Revisiting stub: {stub.question[:60]}...")
            print(f"     Reason: {reason}")

            # Explore this stub now
            stub_node = run_branch_with_awareness(
                branch_question=stub.question,
                parent_node=dag.get_node(stub.parent_node_id),
                other_branches=branch_nodes + newly_explored,
                stubs=[s for s in dag.stubs if s != stub],
                agents=agents
            )

            dag.add_node(stub_node)
            dag.add_edge(Edge(
                from_node_id=stub.parent_node_id,
                to_node_id=stub_node.node_id,
                edge_type=EdgeType.BRANCHES_FROM,
                description=f"Revisited stub: {stub.question[:100]}"
            ))

            stub.status = "explored"
            newly_explored.append(stub_node)
            print(f"  ✓ Created node from stub: {stub_node.node_id}")

    # Final statistics
    print(f"\n=== SESSION COMPLETE ===")
    print(f"Nodes created: {len(dag.nodes)}")
    print(f"Edges created: {len(dag.edges)}")
    print(f"Stubs remaining: {len([s for s in dag.stubs if s.status == 'stub'])}")
    print(f"Stubs explored: {len([s for s in dag.stubs if s.status == 'explored'])}")

    return dag
```

## Data Structure Changes

### DebateDAG Enhancement
```python
class DebateDAG:
    def __init__(self):
        self.nodes: Dict[str, ArgumentNode] = {}
        self.edges: List[Edge] = []
        self.stubs: List[BranchStub] = []  # NEW

    def get_active_stubs(self) -> List[BranchStub]:
        """Get stubs that are still unexplored"""
        return [s for s in self.stubs if s.status == "stub"]

    def get_explored_stubs(self) -> List[BranchStub]:
        """Get stubs that were later explored"""
        return [s for s in self.stubs if s.status == "explored"]
```

### EdgeType Enhancement
```python
class EdgeType(Enum):
    BRANCHES_FROM = "branches_from"      # Existing
    CONTRADICTS = "contradicts"          # Existing
    ELABORATES = "elaborates"            # Existing
    MERGES_INTO = "merges_into"          # NEW - multiple nodes merge
    REFERENCES = "references"            # NEW - cross-branch reference
    SUPERSEDES = "supersedes"            # NEW - newer node supersedes stub
```

### ArgumentNode Enhancement
No changes needed - nodes already support multiple edges, theme tags, etc.

## UI Changes

### Real-Time Tension Display
During main debate, show flagged tensions as they occur:
```
Round 2, Turn 3: The Heideggerian Purist
[debate content...]

⚠ TENSION FLAGGED by Dialectical Observer
  "What is the ontological status of 'structure' itself?"
  Urgency: 0.8
```

### Branch Selection Summary
After main debate:
```
=== BRANCH SELECTION ===
6 tensions flagged by observers

SELECTED FOR EXPLORATION (diverse strategy):
✓ "What is the ontological status of 'structure' itself?" (urgency: 0.8)
✓ "How does temporality affect our 'feeling' of structure?" (urgency: 0.6)
✓ "Can we distinguish chaos from complexity?" (urgency: 0.7)

STUBBED FOR LATER:
📌 "Is 'willful being' redundant or meaningful?" (urgency: 0.5)
📌 "What role does language play in accessing structure?" (urgency: 0.4)
📌 "Are 'blind men' perceiving or constructing?" (urgency: 0.6)
```

### Multi-Branch Progress
While exploring branches:
```
=== EXPLORING BRANCHES ===
[1/3] Exploring: "What is the ontological status of 'structure' itself?"
      Round 1... ✓
      Round 2... ✓
      Complete: Node B1

[2/3] Exploring: "How does temporality affect our 'feeling' of structure?"
      Round 1... ✓
      Round 2... ✓
      Complete: Node B2

[3/3] Exploring: "Can we distinguish chaos from complexity?"
      Round 1... ⏳
```

### Merge Detection
```
=== DETECTING MERGES ===
Found 1 merge opportunity

🔗 Merging B1 + B2
   Reason: Both converge on structure as temporally emergent
   Similarity: 0.82
   Creating synthesis node... ✓
```

### Stub Revisiting
```
=== REVISITING STUBS ===
Checking 3 stubs against current DAG...

🔄 Revisiting: "Are 'blind men' perceiving or constructing?"
   Reason: Merge node S1 introduces perception vs construction tension
   Exploring... ✓

📌 Keeping stubbed: "Is 'willful being' redundant or meaningful?"
   Not yet relevant to current branches

📌 Keeping stubbed: "What role does language play in accessing structure?"
   Not yet relevant to current branches
```

### Graph Visualization
Enhanced to show:
- Multiple parents (merge nodes have 2+ incoming edges)
- Stub indicators (grayed-out potential branches)
- Edge types (different colors for branches_from, merges_into, references)
- Layered layout (not just tree structure)

## Progressive Execution in UI

The app.py execution state becomes:

```python
st.session_state.execution_state = {
    'phase': DebatePhase.MAIN_DEBATE,

    # Main debate
    'main_transcript': [],
    'main_round': 1,
    'main_agent_idx': 0,

    # Monitoring
    'monitor': DebateMonitor(observers),
    'flagged_tensions': [],

    # Branch selection
    'selected_branches': [],
    'stubbed_tensions': [],

    # Branch exploration
    'current_branch_idx': 0,
    'branch_transcripts': {},  # {branch_idx: transcript}
    'completed_branches': [],  # List of ArgumentNodes

    # Merging
    'merge_opportunities': [],
    'created_merges': [],

    # Stub revisiting
    'revisited_stubs': [],
}
```

Progressive display shows each phase completing before moving to next.

## Testing Strategy

### Unit Tests
1. `test_debate_monitor.py` - Observer flagging behavior
2. `test_branch_selector.py` - Selection strategies
3. `test_branch_stub.py` - Stub lifecycle and revisiting
4. `test_branch_merger.py` - Merge detection and creation

### Integration Tests
1. `test_autonomous_session.py` - Full session from passage to DAG
2. `test_stub_revisiting_flow.py` - Stub becomes relevant and gets explored
3. `test_merge_creation.py` - Branches converge and create merge node

### End-to-End Tests
1. Run with real philosophical passage
2. Verify DAG structure (not tree)
3. Verify stubs are preserved
4. Verify merges happen when appropriate

## Migration Path

Since we're fully committing (no backward compatibility):

1. **Mark old code as deprecated** - Add warnings to old session.py functions
2. **Create new entry points** - `run_autonomous_debate_session()` is the new standard
3. **Update app.py** - Replace old execution with new phase-based execution
4. **Update examples** - All examples use new DAG approach
5. **Archive old code** - Move old linear execution to `src/deprecated/`

## Success Criteria

Phase 4 is complete when:

- ✅ Observers flag tensions in real-time during debates
- ✅ Multiple tensions are flagged per debate (not just one)
- ✅ Branch selection automatically chooses subset to explore
- ✅ Unexplored tensions are preserved as stubs
- ✅ Branches run with awareness of each other
- ✅ Merge detection automatically finds convergence points
- ✅ Merge nodes are created with synthesis of merged branches
- ✅ Stubs are automatically revisited when they become relevant
- ✅ Final result is a true DAG (not a tree)
- ✅ DAG contains cycles of reference (A references B references A)
- ✅ UI shows full DAG structure with stubs visible
- ✅ System runs completely autonomously (no user intervention)

## Future Extensions (Phase 5+)

- **Cross-passage DAG linking** - Multiple passages create interconnected DAG
- **Adaptive observer generation** - Generate new observers when needed
- **Meta-level analysis** - Observers that watch the DAG itself and flag meta-tensions
- **Parallel passage processing** - Process multiple passages simultaneously
- **DAG querying** - Natural language queries over the DAG structure
- **Consolidation nodes** - Periodic summary nodes that consolidate large sub-DAGs

---

## Summary

Phase 4 transforms the system from:
- **Linear tree** (main → branch → done)

To:
- **Computational DAG** (real-time flagging → selection → parallel exploration → merging → stub revisiting)

This creates a rich knowledge structure that mirrors how real philosophical inquiry works:
- Multiple lines of investigation pursued simultaneously
- Some questions deferred (stubs) and revisited with new context
- Convergence points where different approaches merge
- Non-linear, graph-like structure of ideas

All automated, no user intervention required.
