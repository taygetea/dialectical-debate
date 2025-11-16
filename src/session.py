#!/usr/bin/env python3
"""
Debate Session Orchestrator

Integrates all Phase 3 components:
- DebateDAG for persistence
- ContextRetriever for context injection
- EdgeDetector for automatic relationships
- NodeFactory for creating nodes from debates

Provides high-level interface for graph-building debates.
"""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import Agent, DebateTurn, Logger, llm_call
from debate_graph import DebateDAG, ArgumentNode, NodeType, Edge, EdgeType
from node_factory import NodeCreationDetector, NodeFactory
from context_retrieval import ContextRetriever
from edge_detection import EdgeDetector
from linearization import LinearizationEngine


def generate_session_name(passage: str, temperature: float = 0.7) -> str:
    """
    Generate a concise, meaningful session name from a passage using LLM

    Args:
        passage: The passage to analyze
        temperature: Sampling temperature

    Returns:
        A short, filesystem-safe session name (e.g., "nietzsche_zarathustra_mountains")
    """

    system_prompt = """You are a concise naming assistant.

Generate a SHORT, descriptive name for a debate session based on the given passage.

Requirements:
- 2-4 words maximum
- lowercase with underscores
- NO spaces, NO special characters (except underscores)
- Captures the core topic or key concept
- Filesystem-safe

Examples:
- "When Zarathustra was thirty..." → "zarathustra_thirty_years"
- "To be or not to be..." → "hamlet_existence_question"
- "the teeming chaos of willful being..." → "chaos_structure_reality"

Output ONLY the name, nothing else."""

    user_prompt = f"""Passage:\n{passage}\n\nGenerate session name:"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Clean up response (remove quotes, whitespace, etc.)
    name = response.strip().strip('"\'').replace(' ', '_').lower()

    # Add timestamp to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{name}_{timestamp}"


def generate_continuation_strategy(node: ArgumentNode, temperature: float = 0.7) -> dict:
    """
    Generate a continuation strategy based on node type and content

    Different node types need different continuation approaches:
    - IMPASSE: Generate bridging question to resolve disagreement
    - SYNTHESIS: Explore implications or applications
    - EXPLORATION: Deepen investigation or identify sub-questions
    - etc.

    Args:
        node: The ArgumentNode to continue from
        temperature: Sampling temperature

    Returns:
        Dict with 'question', 'rationale', and 'approach_type'
    """

    # Build context from node
    context = f"""Node Type: {node.node_type.value}
Topic: {node.topic}
Resolution: {node.resolution}
Key Claims: {', '.join(node.key_claims[:3])}"""

    if node.passage:
        context += f"\nOriginal Passage: {node.passage}"
    if node.branch_question:
        context += f"\nBranch Question: {node.branch_question}"

    # Type-specific system prompts
    if node.node_type == NodeType.IMPASSE:
        system_prompt = """You help resolve impasses in philosophical debates.

When agents reach an impasse, the best continuation is often to:
1. Identify the core disagreement
2. Find a bridging question that reframes the tension
3. Look for hidden assumptions causing the deadlock

Generate a question that might help resolve or productively reframe the impasse.

Output JSON:
{
  "question": "Your bridging question here",
  "rationale": "Why this question might help resolve the impasse",
  "approach_type": "resolution"
}"""

    elif node.node_type == NodeType.SYNTHESIS:
        system_prompt = """You help explore implications of philosophical agreements.

When agents reach synthesis, good continuations:
1. Explore implications or consequences
2. Test the synthesis with edge cases
3. Apply the insight to related domains

Generate a question that deepens or tests the synthesis.

Output JSON:
{
  "question": "Your exploration question here",
  "rationale": "Why this deepens the synthesis",
  "approach_type": "implication"
}"""

    elif node.node_type == NodeType.EXPLORATION:
        system_prompt = """You help deepen open-ended investigations.

When a topic remains exploratory, good continuations:
1. Identify the most promising sub-question
2. Find a concrete case or example to ground the discussion
3. Introduce a contrasting perspective not yet considered

Generate a question that productively deepens the exploration.

Output JSON:
{
  "question": "Your deepening question here",
  "rationale": "Why this advances the investigation",
  "approach_type": "deepening"
}"""

    else:  # QUESTION, LEMMA, CLARIFICATION
        system_prompt = """You help extend philosophical discussions.

Generate a natural follow-up question that:
1. Builds on what was established
2. Opens new relevant territory
3. Maintains philosophical depth

Output JSON:
{
  "question": "Your follow-up question here",
  "rationale": "Why this is a natural next step",
  "approach_type": "extension"
}"""

    user_prompt = f"""{context}

Based on this debate node, generate a continuation strategy (JSON only):"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Parse JSON
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        import json
        strategy = json.loads(response)
        return strategy
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response}")
        # Fallback
        return {
            "question": f"What are the implications of this {node.node_type.value}?",
            "rationale": "General follow-up question",
            "approach_type": "extension"
        }


class DebateSession:
    """
    Orchestrates graph-building debates

    Manages:
    - DAG persistence
    - Context retrieval from past debates
    - Node creation from transcripts
    - Automatic edge detection
    - Narrative export
    """

    def __init__(self, session_name: str, load_existing: bool = False):
        """
        Initialize debate session

        Args:
            session_name: Name for this session (used for file paths)
            load_existing: If True, load existing DAG from disk
        """

        self.session_name = session_name
        self.session_dir = Path("output") / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.dag_path = self.session_dir / f"{session_name}_dag.json"

        # Initialize or load DAG
        if load_existing and self.dag_path.exists():
            print(f"Loading existing DAG from {self.dag_path}")
            self.dag = DebateDAG.load(self.dag_path)
        else:
            print(f"Creating new DAG for session '{session_name}'")
            self.dag = DebateDAG()
            self.dag.metadata['session_name'] = session_name

        # Initialize components
        self.retriever = ContextRetriever(self.dag, strategy="full")
        self.edge_detector = EdgeDetector(self.dag)
        self.node_detector = NodeCreationDetector(max_turns=10)

        # Track current main node (for branch detection)
        self.current_main_node: Optional[ArgumentNode] = None

    def process_passage(self,
                       passage: str,
                       agents: List[Agent],
                       logger: Logger,
                       max_rounds: int = 3) -> ArgumentNode:
        """
        Process a passage with context-enhanced debate

        Args:
            passage: The text to debate
            agents: List of Agent objects
            logger: Logger for output
            max_rounds: Maximum debate rounds

        Returns:
            The created ArgumentNode
        """

        logger.log_section(f"PROCESSING PASSAGE (with context from {len(self.dag.nodes)} prior nodes)")
        logger.log(f"\nPassage:\n{passage}\n")

        # 1. Get relevant context from past debates
        context_nodes = self.retriever.get_relevant_context(passage)
        context_text = self.retriever.format_context_for_debate(context_nodes)

        if context_nodes:
            context_summary = self.retriever.get_context_summary(context_nodes)
            logger.log_subsection("Context Retrieved")
            logger.log(context_summary)

        # 2. Run debate with context-enhanced prompts
        transcript = self._run_debate_with_context(
            passage=passage,
            agents=agents,
            logger=logger,
            context=context_text,
            max_rounds=max_rounds
        )

        # 3. Create node from transcript
        logger.log_subsection("Creating ArgumentNode")
        logger.log("Analyzing debate transcript...")

        node = NodeFactory.create_node_from_transcript(
            node_type=NodeType.EXPLORATION,  # Default for main debates
            transcript=transcript,
            passage=passage,
            branch_question=None
        )

        # 4. Add to DAG
        self.dag.add_node(node)
        logger.log_subsection("Node Created")
        logger.log(f"ID: {node.node_id}\nType: {node.node_type.value}\nTopic: {node.topic}")

        # 5. Detect and add edges
        new_edges = self.edge_detector._detect_edges_for_node(node)
        for edge in new_edges:
            self.dag.add_edge(edge)

        if new_edges:
            logger.log_subsection("Edges Detected")
            logger.log(f"Found {len(new_edges)} relationship(s)")
            for edge in new_edges:
                logger.log(f"  {edge.edge_type.value}: {edge.description}")

        # 6. Save DAG
        self.save()

        # Update current main node
        self.current_main_node = node

        return node

    def process_branch(self,
                      branch_question: str,
                      parent_node_id: str,
                      agents: List[Agent],
                      logger: Logger,
                      max_rounds: int = 3) -> ArgumentNode:
        """
        Process a branch debate

        Args:
            branch_question: The question to explore
            parent_node_id: ID of the parent node this branches from
            agents: List of Agent objects
            logger: Logger for output
            max_rounds: Maximum debate rounds

        Returns:
            The created ArgumentNode (branch)
        """

        logger.log_section(f"BRANCH DEBATE: {branch_question}")

        # Verify parent exists
        parent_node = self.dag.get_node(parent_node_id)
        if not parent_node:
            raise ValueError(f"Parent node {parent_node_id} not found in DAG")

        # 1. Get context (include parent node prominently)
        context_nodes = self.retriever.get_relevant_context(branch_question)
        context_text = self._format_branch_context(parent_node, context_nodes)

        logger.log_subsection("Parent Node")
        logger.log(parent_node.topic)

        # 2. Run branch debate
        transcript = self._run_debate_with_context(
            passage=branch_question,
            agents=agents,
            logger=logger,
            context=context_text,
            max_rounds=max_rounds,
            is_branch=True
        )

        # 3. Detect completion and classify
        is_complete, node_type = self.node_detector.check_completion(
            transcript,
            branch_question=branch_question
        )

        if not node_type:
            node_type = NodeType.EXPLORATION  # Default

        logger.log_subsection("Branch Resolution")
        logger.log(f"Detected type: {node_type.value}")

        # 4. Create node
        node = NodeFactory.create_node_from_transcript(
            node_type=node_type,
            transcript=transcript,
            passage=None,
            branch_question=branch_question
        )

        # 5. Add to DAG
        self.dag.add_node(node)

        # 6. Create BRANCHES_FROM edge (automatic, high confidence)
        branch_edge = Edge(
            from_node_id=parent_node_id,
            to_node_id=node.node_id,
            edge_type=EdgeType.BRANCHES_FROM,
            description=f"Branch: {branch_question[:100]}",
            confidence=1.0
        )
        self.dag.add_edge(branch_edge)

        logger.log_subsection("Branch Created")
        logger.log(f"ID: {node.node_id}\nBranches from: {parent_node.topic[:50]}...")

        # 7. Detect other edges
        other_edges = self.edge_detector._detect_edges_for_node(node)
        for edge in other_edges:
            self.dag.add_edge(edge)

        # 8. Save DAG
        self.save()

        return node

    def save(self):
        """Save DAG to disk"""
        self.dag.save(self.dag_path)

    def export_summary(self, output_path: Optional[Path] = None) -> str:
        """
        Export a summary of the current DAG

        Args:
            output_path: Optional path to write summary

        Returns:
            Summary text
        """

        summary = self.dag.summary()

        if output_path:
            with open(output_path, 'w') as f:
                f.write(summary)

        return summary

    def export_narrative(self, output_path: Optional[Path] = None) -> str:
        """
        Export linearized narrative as markdown

        Args:
            output_path: Optional path to write narrative

        Returns:
            Markdown narrative
        """

        engine = LinearizationEngine(self.dag)
        narrative = engine.render_markdown(output_path)

        return narrative

    def _run_debate_with_context(self,
                                 passage: str,
                                 agents: List[Agent],
                                 logger: Logger,
                                 context: str,
                                 max_rounds: int,
                                 is_branch: bool = False) -> List[DebateTurn]:
        """
        Run debate with context injected into agent prompts

        Args:
            passage: Text to debate
            agents: List of agents
            logger: Logger
            context: Formatted context from past debates
            max_rounds: Maximum rounds
            is_branch: Whether this is a branch debate

        Returns:
            List of DebateTurns
        """

        transcript = []

        for round_num in range(1, max_rounds + 1):
            logger.log_subsection(f"Round {round_num}")

            for agent in agents:
                # Build system prompt with context
                system_prompt = agent.get_system_prompt()

                if context:
                    system_prompt += f"\n\n{context}\n\nUse this context to inform your arguments where relevant. You may reference previous discussions."

                # Build user prompt
                if round_num == 1:
                    if is_branch:
                        user_prompt = f"Question to explore: {passage}\n\nProvide your perspective."
                    else:
                        user_prompt = f"Passage:\n{passage}\n\nProvide your opening analysis."
                else:
                    # Include recent turns
                    recent_turns = "\n\n".join([
                        f"{t.agent_name}: {t.content}"
                        for t in transcript[-(len(agents)*2):]  # Last 2 rounds
                    ])
                    user_prompt = f"Previous discussion:\n{recent_turns}\n\nYour response:"

                # Get response from LLM
                response = llm_call(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    model="electronhub/claude-sonnet-4-5-20250929"
                )

                # Create turn
                turn = DebateTurn(agent.name, response, round_num)
                transcript.append(turn)

                # Log with summary
                logger.log_turn_with_summary(turn)

            # Check for completion (branch debates only)
            if is_branch:
                is_complete, _ = self.node_detector.check_completion(
                    transcript,
                    branch_question=passage
                )
                if is_complete:
                    logger.log_subsection("Early Completion")
                    logger.log("Debate reached resolution")
                    break

        return transcript

    def _format_branch_context(self,
                               parent_node: ArgumentNode,
                               other_nodes: List[ArgumentNode]) -> str:
        """
        Format context for branch debate, highlighting parent node

        Args:
            parent_node: The node this branches from
            other_nodes: Other relevant nodes

        Returns:
            Formatted context string
        """

        lines = [
            "CONTEXT FROM MAIN DEBATE:",
            "=" * 50,
            "",
            f"Main Topic: {parent_node.topic}",
            f"Resolution: {parent_node.resolution}",
            ""
        ]

        if parent_node.key_claims:
            lines.append("Key Claims:")
            for claim in parent_node.key_claims[:5]:
                lines.append(f"  - {claim}")
            lines.append("")

        # Add other relevant context (if any, truncated)
        if other_nodes:
            lines.append("OTHER RELEVANT DISCUSSIONS:")
            lines.append("-" * 50)
            lines.append("")

            for node in other_nodes[:3]:  # Max 3 other nodes
                if node.node_id == parent_node.node_id:
                    continue
                lines.append(f"- {node.topic}")
                lines.append(f"  {node.resolution}")
                lines.append("")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get session statistics"""

        return {
            "session_name": self.session_name,
            "total_nodes": len(self.dag.nodes),
            "total_edges": len(self.dag.edges),
            "node_types": {
                ntype.value: len(self.dag.find_nodes_by_type(ntype))
                for ntype in NodeType
            },
            "edge_types": {
                etype.value: len([e for e in self.dag.edges if e.edge_type == etype])
                for etype in EdgeType
            }
        }


if __name__ == "__main__":
    # Test DebateSession
    print("Testing DebateSession integration...\n")

    from dialectic_poc import Agent, Logger

    # Create test agents
    agents = [
        Agent(
            "Literalist",
            "You interpret text literally and factually.",
            "Biographical and historical details"
        ),
        Agent(
            "Symbolist",
            "You see symbolic and archetypal meanings.",
            "Metaphorical and psychological significance"
        )
    ]

    # Create session
    session = DebateSession("test_session")

    # Create logger
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = session.session_dir / f"test_log_{timestamp}.md"
    logger = Logger(log_file)

    # Test passage
    passage = "When Zarathustra was thirty years old, he left his home and the lake of his home, and went into the mountains."

    print("Processing passage 1...")
    node1 = session.process_passage(
        passage=passage,
        agents=agents,
        logger=logger,
        max_rounds=2
    )

    print(f"✓ Created node: {node1.topic}\n")

    # Test branch
    print("Processing branch debate...")
    branch_question = "What is the significance of 'thirty years'?"

    node2 = session.process_branch(
        branch_question=branch_question,
        parent_node_id=node1.node_id,
        agents=agents,
        logger=logger,
        max_rounds=2
    )

    print(f"✓ Created branch node: {node2.topic}\n")

    # Show stats
    stats = session.get_stats()
    print("Session Statistics:")
    print(f"  Nodes: {stats['total_nodes']}")
    print(f"  Edges: {stats['total_edges']}")
    print(f"  Node types: {stats['node_types']}")
    print(f"  Edge types: {stats['edge_types']}")

    # Export summary
    summary_path = session.session_dir / "summary.txt"
    summary = session.export_summary(summary_path)
    print(f"\n✓ Exported summary to {summary_path}")

    print("\n✅ DebateSession integration test complete!")
    print(f"   See output in: {session.session_dir}")
