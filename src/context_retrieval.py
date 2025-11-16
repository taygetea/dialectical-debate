#!/usr/bin/env python3
"""
Context Retrieval

Provides relevant ArgumentNodes as context for new debates.

Strategy: Full backlog in context (no embeddings for MVP)
Rationale: See docs/DESIGN_DECISIONS.md
"""

import sys
from pathlib import Path
from typing import List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from debate_graph import ArgumentNode, DebateDAG, NodeType
from dialectic_poc import DebateTurn


class ContextRetriever:
    """Retrieves relevant ArgumentNodes as context for new debates

    MVP Strategy: Full backlog approach
    - Include all nodes in context (for corpora <100 passages)
    - Let LLM filter what's relevant
    - Modern LLMs have 200K+ context windows

    Future: Can add embedding-based retrieval if needed
    """

    def __init__(self, dag: DebateDAG, strategy: str = "full"):
        """
        Initialize context retriever

        Args:
            dag: The DebateDAG to retrieve context from
            strategy: "full" (include all nodes) or "embedding" (not implemented)
        """
        self.dag = dag
        self.strategy = strategy

        if strategy not in ["full"]:
            raise ValueError(f"Strategy '{strategy}' not implemented. Use 'full' for MVP.")

    def get_relevant_context(self,
                            passage: str,
                            current_turns: List[DebateTurn] = None,
                            max_nodes: int = None) -> List[ArgumentNode]:
        """
        Get relevant ArgumentNodes for a new debate

        Args:
            passage: The new passage being debated
            current_turns: Current debate turns (for incremental retrieval)
            max_nodes: Maximum nodes to return (None = all)

        Returns:
            List of relevant ArgumentNodes
        """

        if self.strategy == "full":
            # Return all nodes, sorted chronologically
            all_nodes = self.dag.get_all_nodes()

            if max_nodes:
                return all_nodes[:max_nodes]
            return all_nodes

        else:
            # Future: embedding-based retrieval
            raise NotImplementedError(f"Strategy '{self.strategy}' not implemented")

    def format_context_for_debate(self,
                                  nodes: List[ArgumentNode],
                                  max_chars: int = 8000) -> str:
        """
        Format ArgumentNodes as text for injection into agent prompts

        Args:
            nodes: List of ArgumentNodes to format
            max_chars: Maximum characters (truncate if needed)

        Returns:
            Formatted string for system prompt injection
        """

        if not nodes:
            return ""

        lines = [
            "PREVIOUS RELEVANT DISCUSSIONS:",
            "=" * 50,
            ""
        ]

        for i, node in enumerate(nodes, 1):
            # Format each node concisely
            node_text = self._format_single_node(node, number=i)
            lines.append(node_text)
            lines.append("")  # Blank line between nodes

        full_text = "\n".join(lines)

        # Truncate if too long
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[...context truncated...]"

        return full_text

    def _format_single_node(self, node: ArgumentNode, number: int) -> str:
        """Format a single ArgumentNode for context display"""

        # Header with type and topic
        header = f"{number}. [{node.node_type.value.upper()}] {node.topic}"

        # Resolution summary
        resolution = f"   Resolution: {node.resolution}"

        # Key claims (if any)
        claims_section = ""
        if node.key_claims:
            claims = "\n".join(f"   - {claim}" for claim in node.key_claims[:3])
            claims_section = f"   Key claims:\n{claims}"

        # Tags (if any)
        tags_section = ""
        if node.theme_tags:
            tags = ", ".join(sorted(node.theme_tags)[:5])
            tags_section = f"   Tags: {tags}"

        # Combine sections
        sections = [header, resolution]
        if claims_section:
            sections.append(claims_section)
        if tags_section:
            sections.append(tags_section)

        return "\n".join(sections)

    def get_context_summary(self, nodes: List[ArgumentNode]) -> str:
        """
        Generate a brief summary of available context

        Useful for logging/debugging
        """

        if not nodes:
            return "No prior context available"

        # Count by type
        type_counts = {}
        for node in nodes:
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1

        # Format counts
        type_strs = [f"{count} {ntype.value}" for ntype, count in type_counts.items()]

        # Collect all tags
        all_tags = set()
        for node in nodes:
            all_tags.update(node.theme_tags)

        tag_str = f"Tags: {', '.join(sorted(all_tags)[:10])}" if all_tags else ""

        return f"Context: {len(nodes)} nodes ({', '.join(type_strs)}). {tag_str}"


class SimpleSimilarity:
    """
    Simple text-based similarity (Jaccard distance)

    Future enhancement: Can be used for filtered context retrieval
    Currently not used in MVP (full backlog strategy)
    """

    @staticmethod
    def compute_similarity(node: ArgumentNode, text: str) -> float:
        """
        Compute Jaccard similarity between node and text

        Args:
            node: ArgumentNode to compare
            text: Text to compare (passage or question)

        Returns:
            Similarity score 0.0-1.0
        """

        # Extract words from node
        node_text = f"{node.topic} {node.resolution}"
        node_words = set(SimpleSimilarity._extract_words(node_text))

        # Extract words from text
        text_words = set(SimpleSimilarity._extract_words(text))

        # Jaccard similarity
        if not node_words or not text_words:
            return 0.0

        overlap = len(node_words & text_words)
        total = len(node_words | text_words)

        return overlap / total if total > 0 else 0.0

    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract words from text (lowercase, alphanumeric only)"""
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out very short words (articles, etc.)
        return [w for w in words if len(w) > 2]

    @staticmethod
    def rank_nodes_by_similarity(nodes: List[ArgumentNode],
                                 text: str,
                                 top_k: int = 5) -> List[ArgumentNode]:
        """
        Rank nodes by similarity to text, return top-k

        Future: Can be used instead of full backlog
        """

        scored = [(node, SimpleSimilarity.compute_similarity(node, text))
                  for node in nodes]

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top-k nodes
        return [node for node, score in scored[:top_k]]


if __name__ == "__main__":
    # Test with mock data
    print("Testing ContextRetriever...")

    # Create mock DAG with nodes
    from debate_graph import DebateDAG, ArgumentNode, NodeType

    dag = DebateDAG()

    # Add some mock nodes
    node1 = ArgumentNode.create(
        node_type=NodeType.EXPLORATION,
        topic="Zarathustra's departure represents literal or symbolic journey",
        resolution="Three perspectives emerged: literal biography, symbolic transformation, structural narrative pattern. Tension remains unresolved.",
        passage="When Zarathustra was thirty years old...",
        theme_tags={"departure", "transformation", "mountains"},
        key_claims=[
            "Literalist: Historical departure from society",
            "Symbolist: Mountains represent higher consciousness",
            "Structuralist: Archetypal withdrawal motif"
        ]
    )

    node2 = ArgumentNode.create(
        node_type=NodeType.SYNTHESIS,
        topic="The meaning of 'thirty years' in Zarathustra's life",
        resolution="Resolved that 'thirty' functions simultaneously as biographical fact, psychological threshold, and genre marker.",
        branch_question="What does thirty years signify?",
        theme_tags={"age", "maturity", "threshold"},
        key_claims=[
            "Not mutually exclusive readings",
            "Multiple interpretive layers coexist"
        ]
    )

    node3 = ArgumentNode.create(
        node_type=NodeType.IMPASSE,
        topic="Whether mountains have inherent symbolic meaning",
        resolution="Fundamental disagreement: Symbolist sees universal archetypes, Literalist sees reader projection. Cannot reconcile.",
        theme_tags={"symbolism", "interpretation", "meaning"},
        key_claims=[
            "Symbolist: Mountains universally represent ascent",
            "Literalist: Mountains are just geography"
        ]
    )

    dag.add_node(node1)
    dag.add_node(node2)
    dag.add_node(node3)

    # Test retriever
    retriever = ContextRetriever(dag, strategy="full")

    # Get context for new passage
    new_passage = "Zarathustra descended from the mountains after ten years..."

    context_nodes = retriever.get_relevant_context(new_passage)
    print(f"\n✓ Retrieved {len(context_nodes)} nodes")

    # Format context
    formatted = retriever.format_context_for_debate(context_nodes)
    print(f"\n✓ Formatted context ({len(formatted)} chars):")
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

    # Test summary
    summary = retriever.get_context_summary(context_nodes)
    print(f"\n✓ Summary: {summary}")

    # Test similarity (future feature)
    print("\n\nTesting SimpleSimilarity...")

    similarity1 = SimpleSimilarity.compute_similarity(node1, new_passage)
    similarity2 = SimpleSimilarity.compute_similarity(node2, new_passage)
    similarity3 = SimpleSimilarity.compute_similarity(node3, new_passage)

    print(f"✓ Similarity to node1 (departure): {similarity1:.3f}")
    print(f"✓ Similarity to node2 (thirty years): {similarity2:.3f}")
    print(f"✓ Similarity to node3 (mountains): {similarity3:.3f}")

    # Rank by similarity
    ranked = SimpleSimilarity.rank_nodes_by_similarity(
        context_nodes,
        new_passage,
        top_k=2
    )
    print(f"\n✓ Top 2 most relevant nodes:")
    for i, node in enumerate(ranked, 1):
        print(f"   {i}. {node.topic[:50]}...")

    print("\n✅ ContextRetriever tests complete!")
