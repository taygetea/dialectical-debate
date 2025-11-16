#!/usr/bin/env python3
"""
Phase 3: Edge Detection

Automatically detects relationships between ArgumentNodes.

MVP implements 3 edge types:
- BRANCHES_FROM: Automatic (branch nodes have parent reference)
- CONTRADICTS: Pattern matching + claim analysis
- ELABORATES: Pattern matching + topic similarity
"""

import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase3_dag import ArgumentNode, Edge, EdgeType, DebateDAG
from phase3_similarity import SimpleSimilarity


class EdgeDetector:
    """Detects relationships between ArgumentNodes"""

    def __init__(self, dag: DebateDAG):
        """
        Initialize edge detector

        Args:
            dag: The DebateDAG to analyze
        """
        self.dag = dag

        # Patterns for detecting contradictions
        self.contradiction_patterns = [
            r'\bcontradict',
            r'\boppose',
            r'\bdisagree',
            r'\brefute',
            r'\bcounter',
            r'\bagainst\b',
            r'\bhowever\b',
            r'\bbut\b',
            r'\balthough\b',
            r'\bconversely\b',
            r'\bcontrary\b'
        ]

        # Patterns for detecting elaborations
        self.elaboration_patterns = [
            r'\bbuild',
            r'\bextend',
            r'\bdevelop',
            r'\bexpand',
            r'\belaborate',
            r'\bfurther',
            r'\bmoreover',
            r'\badditionally',
            r'\badd to',
            r'\bcontinue'
        ]

    def detect_all_edges(self, new_node: Optional[ArgumentNode] = None) -> List[Edge]:
        """
        Detect all edges in the DAG

        Args:
            new_node: If provided, only detect edges involving this node
                     (more efficient for incremental building)

        Returns:
            List of detected edges
        """

        edges = []

        # Always detect BRANCHES_FROM first (automatic)
        edges.extend(self.detect_branches_from())

        # Then detect semantic relationships
        if new_node:
            # Only check relationships between new_node and existing nodes
            edges.extend(self._detect_edges_for_node(new_node))
        else:
            # Check all pairs (expensive, use sparingly)
            edges.extend(self.detect_contradictions())
            edges.extend(self.detect_elaborations())

        return edges

    def detect_branches_from(self) -> List[Edge]:
        """
        Detect BRANCHES_FROM edges (automatic and high confidence)

        These edges are determined by the branch_question field:
        - If a node has branch_question, it branched from some parent
        - Parent can be inferred from context (last main debate node)

        Returns:
            List of BRANCHES_FROM edges
        """

        edges = []

        # Get all nodes chronologically
        all_nodes = self.dag.get_all_nodes()

        # Track the current "main" debate node
        main_node = None

        for node in all_nodes:
            if node.branch_question:
                # This is a branch node
                if main_node:
                    # Create BRANCHES_FROM edge from main_node to this node
                    edge = Edge(
                        from_node_id=main_node.node_id,
                        to_node_id=node.node_id,
                        edge_type=EdgeType.BRANCHES_FROM,
                        description=f"Branch debate on: {node.branch_question[:100]}...",
                        confidence=1.0,  # Automatic, always confident
                    )
                    edges.append(edge)
            else:
                # This is a main debate node
                main_node = node

        return edges

    def detect_contradictions(self) -> List[Edge]:
        """
        Detect CONTRADICTS edges using pattern matching and claim analysis

        Returns:
            List of CONTRADICTS edges with confidence scores
        """

        edges = []
        all_nodes = self.dag.get_all_nodes()

        # Compare each pair
        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                edge = self._check_contradiction(node1, node2)
                if edge:
                    edges.append(edge)

        return edges

    def _check_contradiction(self,
                            node1: ArgumentNode,
                            node2: ArgumentNode) -> Optional[Edge]:
        """
        Check if two nodes contradict each other

        Signals:
        1. Contradiction language in resolution/claims
        2. Opposite node types (SYNTHESIS vs IMPASSE on similar topic)
        3. Contradictory key claims

        Returns:
            Edge if contradiction detected, else None
        """

        # Signal 1: Pattern matching in resolutions
        combined_text = f"{node1.resolution} {node2.resolution}"
        pattern_score = self._count_patterns(combined_text, self.contradiction_patterns)

        # Signal 2: Contradictory claims
        claim_score = self._check_contradictory_claims(node1.key_claims, node2.key_claims)

        # Signal 3: Similar topic but opposite types
        topic_similarity = SimpleSimilarity.compute_similarity(node1, node2.topic)
        type_opposition = (
            (node1.node_type.value == "synthesis" and node2.node_type.value == "impasse") or
            (node1.node_type.value == "impasse" and node2.node_type.value == "synthesis")
        )
        type_score = 1.0 if (topic_similarity > 0.3 and type_opposition) else 0.0

        # Combine signals
        total_score = (pattern_score * 0.4 + claim_score * 0.4 + type_score * 0.2)

        # Threshold for contradiction
        if total_score > 0.5:
            # Determine direction (which contradicts which)
            # Default: newer contradicts older
            from_node = node2 if node2.created_at > node1.created_at else node1
            to_node = node1 if from_node == node2 else node2

            return Edge(
                from_node_id=from_node.node_id,
                to_node_id=to_node.node_id,
                edge_type=EdgeType.CONTRADICTS,
                description=self._generate_contradiction_description(from_node, to_node),
                confidence=min(total_score, 1.0)
            )

        return None

    def detect_elaborations(self) -> List[Edge]:
        """
        Detect ELABORATES edges using pattern matching and topic similarity

        Returns:
            List of ELABORATES edges with confidence scores
        """

        edges = []
        all_nodes = self.dag.get_all_nodes()

        # Check sequential pairs (elaborations usually follow what they elaborate)
        for i in range(len(all_nodes) - 1):
            node1 = all_nodes[i]
            node2 = all_nodes[i + 1]

            edge = self._check_elaboration(node1, node2)
            if edge:
                edges.append(edge)

        return edges

    def _check_elaboration(self,
                          earlier_node: ArgumentNode,
                          later_node: ArgumentNode) -> Optional[Edge]:
        """
        Check if later_node elaborates on earlier_node

        Signals:
        1. Elaboration language in later node
        2. High topic similarity
        3. Shared theme tags
        4. Later node is CLARIFICATION or LEMMA type

        Returns:
            Edge if elaboration detected, else None
        """

        # Signal 1: Pattern matching
        pattern_score = self._count_patterns(
            later_node.resolution,
            self.elaboration_patterns
        )

        # Signal 2: Topic similarity
        similarity = SimpleSimilarity.compute_similarity(earlier_node, later_node.topic)
        similarity_score = similarity if similarity > 0.4 else 0.0

        # Signal 3: Shared tags
        shared_tags = earlier_node.theme_tags & later_node.theme_tags
        tag_score = min(len(shared_tags) / 3, 1.0) if shared_tags else 0.0

        # Signal 4: Node type
        is_clarification = later_node.node_type.value in ["clarification", "lemma"]
        type_score = 0.5 if is_clarification else 0.0

        # Combine signals
        total_score = (
            pattern_score * 0.3 +
            similarity_score * 0.4 +
            tag_score * 0.2 +
            type_score * 0.1
        )

        # Threshold for elaboration
        if total_score > 0.4:
            return Edge(
                from_node_id=later_node.node_id,
                to_node_id=earlier_node.node_id,
                edge_type=EdgeType.ELABORATES,
                description=self._generate_elaboration_description(earlier_node, later_node),
                confidence=min(total_score, 1.0)
            )

        return None

    def _detect_edges_for_node(self, new_node: ArgumentNode) -> List[Edge]:
        """
        Detect edges involving a specific node (more efficient)

        Args:
            new_node: The node to check relationships for

        Returns:
            List of edges involving new_node
        """

        edges = []
        all_nodes = self.dag.get_all_nodes()

        # Check contradictions with all existing nodes
        for existing_node in all_nodes:
            if existing_node.node_id == new_node.node_id:
                continue

            # Check both directions
            edge = self._check_contradiction(new_node, existing_node)
            if edge:
                edges.append(edge)

        # Check elaborations (only if new_node is later chronologically)
        for existing_node in all_nodes:
            if existing_node.node_id == new_node.node_id:
                continue

            if new_node.created_at > existing_node.created_at:
                # new_node might elaborate on existing_node
                edge = self._check_elaboration(existing_node, new_node)
                if edge:
                    edges.append(edge)

        return edges

    # Helper methods

    def _count_patterns(self, text: str, patterns: List[str]) -> float:
        """
        Count pattern matches in text, return normalized score

        Returns:
            Score 0.0-1.0 based on pattern frequency
        """

        text_lower = text.lower()
        matches = 0

        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches += 1

        # Normalize to 0-1 (cap at 3 matches = 1.0)
        return min(matches / 3, 1.0)

    def _check_contradictory_claims(self,
                                   claims1: List[str],
                                   claims2: List[str]) -> float:
        """
        Check if claim lists contain contradictory statements

        Simple heuristic: Look for negation + similar words

        Returns:
            Score 0.0-1.0 indicating contradiction strength
        """

        if not claims1 or not claims2:
            return 0.0

        contradictions = 0
        total_comparisons = 0

        for c1 in claims1:
            for c2 in claims2:
                total_comparisons += 1

                # Check for negation markers
                c1_lower = c1.lower()
                c2_lower = c2.lower()

                has_negation = (
                    ('not' in c1_lower and 'not' not in c2_lower) or
                    ('not' in c2_lower and 'not' not in c1_lower) or
                    ('no ' in c1_lower and 'no ' not in c2_lower) or
                    ('no ' in c2_lower and 'no ' not in c1_lower)
                )

                # Check for word overlap
                words1 = set(SimpleSimilarity._extract_words(c1))
                words2 = set(SimpleSimilarity._extract_words(c2))
                overlap = len(words1 & words2) / max(len(words1 | words2), 1)

                # If negation + high overlap, likely contradiction
                if has_negation and overlap > 0.3:
                    contradictions += 1

        if total_comparisons == 0:
            return 0.0

        return contradictions / total_comparisons

    def _generate_contradiction_description(self,
                                           node1: ArgumentNode,
                                           node2: ArgumentNode) -> str:
        """Generate human-readable description of contradiction"""

        return f"'{node1.topic[:50]}...' contradicts '{node2.topic[:50]}...'"

    def _generate_elaboration_description(self,
                                         base_node: ArgumentNode,
                                         elaborating_node: ArgumentNode) -> str:
        """Generate human-readable description of elaboration"""

        return f"'{elaborating_node.topic[:50]}...' elaborates on '{base_node.topic[:50]}...'"


if __name__ == "__main__":
    # Test with mock data
    print("Testing EdgeDetector...")

    from phase3_dag import DebateDAG, ArgumentNode, NodeType
    import time

    dag = DebateDAG()

    # Create mock nodes with relationships

    # Node 1: Main debate
    node1 = ArgumentNode.create(
        node_type=NodeType.EXPLORATION,
        topic="Zarathustra's departure represents literal or symbolic journey",
        resolution="Three perspectives emerged without full resolution. The Literalist sees biographical fact, the Symbolist sees transformative ascent, the Structuralist sees narrative archetype.",
        passage="When Zarathustra was thirty years old...",
        theme_tags={"departure", "transformation", "journey"},
        key_claims=[
            "Literalist: Departure is historical fact",
            "Symbolist: Mountains represent consciousness",
            "Structuralist: Archetypal withdrawal pattern"
        ]
    )
    time.sleep(0.01)  # Ensure different timestamps

    # Node 2: Branch debate (should have BRANCHES_FROM edge)
    node2 = ArgumentNode.create(
        node_type=NodeType.SYNTHESIS,
        topic="The meaning of 'thirty years' in Zarathustra's life",
        resolution="We agree that 'thirty' functions on multiple levels simultaneously. Not mutually exclusive.",
        branch_question="What does thirty years signify?",
        theme_tags={"age", "maturity", "threshold"},
        key_claims=[
            "Multiple interpretive layers coexist",
            "Biographical and symbolic readings compatible"
        ]
    )
    time.sleep(0.01)

    # Node 3: Contradicts node 1 (opposite view)
    node3 = ArgumentNode.create(
        node_type=NodeType.IMPASSE,
        topic="Whether symbolic interpretation is valid or projection",
        resolution="Fundamental disagreement: The Symbolist insists on universal archetypes, but the Literalist argues this is reader projection. Cannot reconcile opposing views.",
        theme_tags={"symbolism", "interpretation", "projection"},
        key_claims=[
            "Literalist: Symbolic readings are not textually grounded",
            "Symbolist: Universal archetypes are real"
        ]
    )
    time.sleep(0.01)

    # Node 4: Elaborates on node 2 (builds on age discussion)
    node4 = ArgumentNode.create(
        node_type=NodeType.CLARIFICATION,
        topic="Further exploration of threshold symbolism in Nietzsche",
        resolution="Building on our previous discussion of 'thirty years', we find that Nietzsche consistently uses age markers to signal developmental thresholds across his works.",
        theme_tags={"age", "threshold", "development"},
        key_claims=[
            "Pattern extends beyond Zarathustra",
            "Threshold symbolism is recurrent motif"
        ]
    )

    # Add nodes to DAG
    dag.add_node(node1)
    dag.add_node(node2)
    dag.add_node(node3)
    dag.add_node(node4)

    print(f"✓ Created DAG with {len(dag.nodes)} nodes\n")

    # Test edge detector
    detector = EdgeDetector(dag)

    # Test 1: Detect BRANCHES_FROM edges
    print("Test 1: Detect BRANCHES_FROM edges")
    branches = detector.detect_branches_from()
    print(f"✓ Found {len(branches)} BRANCHES_FROM edge(s)")
    for edge in branches:
        from_node = dag.get_node(edge.from_node_id)
        to_node = dag.get_node(edge.to_node_id)
        print(f"  {from_node.topic[:40]}... ↗ {to_node.topic[:40]}...")
        print(f"  Confidence: {edge.confidence}")

    # Test 2: Detect CONTRADICTS edges
    print("\nTest 2: Detect CONTRADICTS edges")
    contradictions = detector.detect_contradictions()
    print(f"✓ Found {len(contradictions)} CONTRADICTS edge(s)")
    for edge in contradictions:
        from_node = dag.get_node(edge.from_node_id)
        to_node = dag.get_node(edge.to_node_id)
        print(f"  {from_node.topic[:40]}... ⊥ {to_node.topic[:40]}...")
        print(f"  Confidence: {edge.confidence:.2f}")
        print(f"  Description: {edge.description}")

    # Test 3: Detect ELABORATES edges
    print("\nTest 3: Detect ELABORATES edges")
    elaborations = detector.detect_elaborations()
    print(f"✓ Found {len(elaborations)} ELABORATES edge(s)")
    for edge in elaborations:
        from_node = dag.get_node(edge.from_node_id)
        to_node = dag.get_node(edge.to_node_id)
        print(f"  {from_node.topic[:40]}... ⇢ {to_node.topic[:40]}...")
        print(f"  Confidence: {edge.confidence:.2f}")
        print(f"  Description: {edge.description}")

    # Test 4: Detect all edges for specific node
    print("\nTest 4: Detect edges for node4 specifically")
    edges_for_node4 = detector._detect_edges_for_node(node4)
    print(f"✓ Found {len(edges_for_node4)} edge(s) involving node4")

    # Test 5: Add all detected edges to DAG
    print("\nTest 5: Add all edges to DAG")
    all_edges = detector.detect_all_edges()
    for edge in all_edges:
        dag.add_edge(edge)
    print(f"✓ Added {len(dag.edges)} total edges to DAG")
    print(f"\n{dag.summary()}")

    print("\n✅ EdgeDetector tests complete!")
