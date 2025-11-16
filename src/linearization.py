#!/usr/bin/env python3
"""
Linearization Engine

Converts DebateDAG to linear markdown narrative.

Strategy: Topological sort with chronological fallback
"""

import sys
from pathlib import Path
from typing import List, Set, Dict
from collections import deque

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from debate_graph import DebateDAG, ArgumentNode, EdgeType


class LinearizationEngine:
    """Converts graph to readable narrative"""

    def __init__(self, dag: DebateDAG):
        """
        Initialize linearization engine

        Args:
            dag: The DebateDAG to linearize
        """
        self.dag = dag

    def linearize(self) -> List[str]:
        """
        Get node IDs in linear order

        Uses topological sort (respects dependencies)
        Falls back to chronological if cycles detected

        Returns:
            Ordered list of node IDs
        """

        try:
            return self._topological_sort()
        except ValueError as e:
            # Cycle detected, fall back to chronological
            print(f"Warning: {e}. Using chronological order.")
            return self._chronological_order()

    def _topological_sort(self) -> List[str]:
        """
        Topological sort using Kahn's algorithm

        Returns nodes in dependency order:
        - Parent nodes before children
        - Prerequisites before dependents

        Raises:
            ValueError: If cycle detected
        """

        # Build adjacency list and in-degree count
        in_degree = {node_id: 0 for node_id in self.dag.nodes}
        adj_list = {node_id: [] for node_id in self.dag.nodes}

        for edge in self.dag.edges:
            # Edge goes FROM -> TO
            # For ordering, we want TO to come after FROM
            adj_list[edge.from_node_id].append(edge.to_node_id)
            in_degree[edge.to_node_id] += 1

        # Start with nodes that have no incoming edges
        queue = deque([
            node_id for node_id, degree in in_degree.items()
            if degree == 0
        ])

        # Sort queue by creation time for deterministic order
        queue = deque(sorted(queue, key=lambda nid: self.dag.nodes[nid].created_at))

        result = []

        while queue:
            # Process node with no dependencies
            node_id = queue.popleft()
            result.append(node_id)

            # Reduce in-degree for neighbors
            for neighbor_id in adj_list[node_id]:
                in_degree[neighbor_id] -= 1

                # If neighbor now has no dependencies, add to queue
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # If we didn't process all nodes, there's a cycle
        if len(result) != len(self.dag.nodes):
            raise ValueError("Cycle detected in graph")

        return result

    def _chronological_order(self) -> List[str]:
        """
        Fallback: Order by creation time

        Returns:
            Node IDs sorted by created_at
        """

        nodes = sorted(self.dag.nodes.values(), key=lambda n: n.created_at)
        return [node.node_id for node in nodes]

    def render_markdown(self, output_path: Path = None) -> str:
        """
        Generate markdown narrative

        Args:
            output_path: Optional path to write output

        Returns:
            Markdown string
        """

        # Get node order
        node_order = self.linearize()

        # Build markdown sections
        sections = []

        # Header
        sections.append(self._render_header())
        sections.append("")

        # Table of contents
        sections.append(self._render_toc(node_order))
        sections.append("")

        # Nodes
        for i, node_id in enumerate(node_order, 1):
            node = self.dag.get_node(node_id)
            sections.append(self._render_node(node, number=i))
            sections.append("")

        markdown = "\n".join(sections)

        # Write to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(markdown)

        return markdown

    def _render_header(self) -> str:
        """Render document header"""

        lines = [
            f"# Debate Session: {self.dag.metadata.get('session_name', 'Unknown')}",
            "",
            f"**Generated:** {self.dag.metadata.get('created_at', 'Unknown')}",
            f"**Nodes:** {len(self.dag.nodes)}",
            f"**Edges:** {len(self.dag.edges)}",
            ""
        ]

        return "\n".join(lines)

    def _render_toc(self, node_order: List[str]) -> str:
        """Render table of contents"""

        lines = [
            "## Table of Contents",
            ""
        ]

        for i, node_id in enumerate(node_order, 1):
            node = self.dag.get_node(node_id)
            # Create anchor link
            anchor = f"node-{i}"
            lines.append(f"{i}. [{node.topic[:80]}](##{anchor})")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _render_node(self, node: ArgumentNode, number: int) -> str:
        """Render a single node"""

        lines = []

        # Header with anchor
        anchor = f"node-{number}"
        lines.append(f"## {number}. {node.topic} {{#{anchor}}}")
        lines.append("")

        # Metadata
        lines.append(f"**Type:** {node.node_type.value}")

        if node.theme_tags:
            tags = " ".join([f"#{tag}" for tag in sorted(node.theme_tags)])
            lines.append(f"**Tags:** {tags}")

        # Show edges
        incoming = self.dag.get_incoming_edges(node.node_id)
        outgoing = self.dag.get_outgoing_edges(node.node_id)

        if incoming or outgoing:
            edge_strs = []
            for edge in incoming:
                from_node = self.dag.get_node(edge.from_node_id)
                edge_strs.append(f"← {edge.edge_type.value} from '{from_node.topic[:40]}...'")
            for edge in outgoing:
                to_node = self.dag.get_node(edge.to_node_id)
                edge_strs.append(f"→ {edge.edge_type.value} to '{to_node.topic[:40]}...'")

            lines.append(f"**Edges:** {', '.join(edge_strs)}")

        lines.append("")

        # Resolution
        lines.append("**Summary:**")
        lines.append("")
        lines.append(node.resolution)
        lines.append("")

        # Key claims
        if node.key_claims:
            lines.append("**Key Claims:**")
            for claim in node.key_claims:
                lines.append(f"- {claim}")
            lines.append("")

        # Original passage (if main debate)
        if node.passage:
            lines.append("<details>")
            lines.append("<summary>Original Passage</summary>")
            lines.append("")
            lines.append(node.passage)
            lines.append("")
            lines.append("</details>")
            lines.append("")

        # Branch question (if branch)
        if node.branch_question:
            lines.append(f"**Branch Question:** {node.branch_question}")
            lines.append("")

        # Full transcript (collapsible)
        if node.turns_data:
            lines.append("<details>")
            lines.append(f"<summary>Full Transcript ({len(node.turns_data)} turns)</summary>")
            lines.append("")

            for turn_data in node.turns_data:
                lines.append(f"**{turn_data['agent_name']}** (Round {turn_data['round_num']}):")
                lines.append(turn_data['content'])
                lines.append("")

            lines.append("</details>")

        lines.append("---")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test with mock data
    print("Testing LinearizationEngine...\n")

    from debate_graph import DebateDAG, ArgumentNode, NodeType, Edge, EdgeType, create_edge
    import time

    # Create test DAG
    dag = DebateDAG()
    dag.metadata['session_name'] = 'Test Session'

    # Node 1: Main debate
    node1 = ArgumentNode.create(
        node_type=NodeType.EXPLORATION,
        topic="Zarathustra's departure at age thirty",
        resolution="Three interpretive positions emerged: literal (biographical departure), symbolic (spiritual ascent), and structural (narrative archetype). Tension remains about where meaning resides.",
        passage="When Zarathustra was thirty years old, he left his home and the lake of his home, and went into the mountains.",
        theme_tags={"departure", "transformation", "mountains"},
        key_claims=[
            "Literalist: Factual biographical event",
            "Symbolist: Mountains represent higher consciousness",
            "Structuralist: Archetypal withdrawal pattern"
        ],
        turns_data=[
            {"agent_name": "Literalist", "content": "This describes a literal departure...", "round_num": 1},
            {"agent_name": "Symbolist", "content": "The mountains symbolize ascent...", "round_num": 1},
            {"agent_name": "Structuralist", "content": "This follows hero withdrawal motif...", "round_num": 1}
        ]
    )
    time.sleep(0.01)

    # Node 2: Branch from node 1
    node2 = ArgumentNode.create(
        node_type=NodeType.SYNTHESIS,
        topic="The significance of 'thirty years'",
        resolution="Resolved that 'thirty' operates on multiple levels: biographical fact, psychological threshold, and literary convention. Not mutually exclusive.",
        branch_question="What does 'thirty years' signify?",
        theme_tags={"age", "maturity", "threshold"},
        key_claims=[
            "Multiple interpretive layers coexist",
            "Age serves biographical and symbolic functions"
        ],
        turns_data=[
            {"agent_name": "Literalist", "content": "Thirty is the age...", "round_num": 1},
            {"agent_name": "Symbolist", "content": "Thirty marks maturity...", "round_num": 1}
        ]
    )
    time.sleep(0.01)

    # Node 3: Another main debate (chronologically later)
    node3 = ArgumentNode.create(
        node_type=NodeType.EXPLORATION,
        topic="Zarathustra's descent from mountains after ten years",
        resolution="Debate explored whether descent represents return to society or philosophical method. Multiple perspectives remain in play.",
        passage="After ten years in solitude, Zarathustra descended to bring wisdom to humanity.",
        theme_tags={"descent", "solitude", "wisdom"},
        key_claims=[
            "Descent as social return",
            "Descent as pedagogical method"
        ],
        turns_data=[
            {"agent_name": "Literalist", "content": "He literally came down...", "round_num": 1},
            {"agent_name": "Symbolist", "content": "Descent mirrors cave allegory...", "round_num": 1}
        ]
    )

    # Add nodes
    dag.add_node(node1)
    dag.add_node(node2)
    dag.add_node(node3)

    # Add edges
    edge1 = create_edge(
        from_node=node1,
        to_node=node2,
        edge_type=EdgeType.BRANCHES_FROM,
        description="Branch question on age significance"
    )

    edge2 = create_edge(
        from_node=node1,
        to_node=node3,
        edge_type=EdgeType.ELABORATES,
        description="Continues exploration of Zarathustra's journey",
        confidence=0.8
    )

    dag.add_edge(edge1)
    dag.add_edge(edge2)

    print(f"Created test DAG: {dag}")
    print(f"  Nodes: {len(dag.nodes)}")
    print(f"  Edges: {len(dag.edges)}\n")

    # Test linearization
    engine = LinearizationEngine(dag)

    print("Testing topological sort...")
    node_order = engine.linearize()
    print(f"✓ Order: {len(node_order)} nodes")
    for i, node_id in enumerate(node_order, 1):
        node = dag.get_node(node_id)
        print(f"  {i}. {node.topic[:50]}...")

    # Test markdown generation
    print("\nGenerating markdown...")
    markdown = engine.render_markdown()
    print(f"✓ Generated {len(markdown)} characters of markdown")

    # Show preview
    print("\nMarkdown preview (first 800 chars):")
    print("=" * 60)
    print(markdown[:800])
    print("...")
    print("=" * 60)

    # Save to file
    output_path = Path("/tmp/linearized_test.md")
    engine.render_markdown(output_path)
    print(f"\n✓ Saved full output to {output_path}")

    print("\n✅ LinearizationEngine tests complete!")
