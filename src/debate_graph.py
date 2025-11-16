#!/usr/bin/env python3
"""
Phase 3: Graph Data Structures

Core classes for the dialectical debate DAG:
- ArgumentNode: Semantic completion units
- Edge: Typed relationships between nodes
- DebateDAG: The graph itself
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid


class NodeType(Enum):
    """Types of argument nodes"""
    SYNTHESIS = "synthesis"          # Agents reached agreement
    IMPASSE = "impasse"              # Fundamental disagreement, can't resolve
    LEMMA = "lemma"                  # Established sub-point for larger argument
    QUESTION = "question"            # Posed question awaiting answer
    EXPLORATION = "exploration"      # Investigated topic without resolution
    CLARIFICATION = "clarification"  # Refined understanding of specific point


class EdgeType(Enum):
    """Types of relationships between nodes"""
    # MVP - Implement these 3 first
    BRANCHES_FROM = "branches_from"  # Branch debate from main debate
    CONTRADICTS = "contradicts"      # Direct opposition
    ELABORATES = "elaborates"        # Expands on previous point

    # Deferred to Phase 3.5+
    # SUPPORTS = "supports"
    # REQUIRES = "requires"
    # APPLIES_TO = "applies_to"
    # ANALOGY = "analogy"


@dataclass
class ArgumentNode:
    """A semantically complete debate segment (not individual turns)"""

    node_id: str                          # Unique identifier
    node_type: NodeType                   # Type of resolution
    topic: str                            # 1-2 sentence summary
    resolution: str                       # Paragraph summary of outcome
    passage: Optional[str] = None         # Original passage (if main debate)
    branch_question: Optional[str] = None # Question (if branch debate)
    theme_tags: Set[str] = field(default_factory=set)  # ["free-will", "causation"]
    key_claims: List[str] = field(default_factory=list)  # Main assertions
    created_at: datetime = field(default_factory=datetime.now)

    # Store turns as serializable dicts (not DebateTurn objects for now)
    turns_data: List[Dict] = field(default_factory=list)

    @classmethod
    def create(cls,
               node_type: NodeType,
               topic: str,
               resolution: str,
               passage: Optional[str] = None,
               branch_question: Optional[str] = None,
               theme_tags: Optional[Set[str]] = None,
               key_claims: Optional[List[str]] = None,
               turns_data: Optional[List[Dict]] = None) -> 'ArgumentNode':
        """Factory method to create a new ArgumentNode"""
        return cls(
            node_id=str(uuid.uuid4()),
            node_type=node_type,
            topic=topic,
            resolution=resolution,
            passage=passage,
            branch_question=branch_question,
            theme_tags=theme_tags or set(),
            key_claims=key_claims or [],
            turns_data=turns_data or []
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enum to string
        data['node_type'] = self.node_type.value
        # Convert set to list for JSON
        data['theme_tags'] = list(self.theme_tags)
        # Convert datetime to ISO string
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ArgumentNode':
        """Create ArgumentNode from dictionary"""
        return cls(
            node_id=data['node_id'],
            node_type=NodeType(data['node_type']),
            topic=data['topic'],
            resolution=data['resolution'],
            passage=data.get('passage'),
            branch_question=data.get('branch_question'),
            theme_tags=set(data.get('theme_tags', [])),
            key_claims=data.get('key_claims', []),
            created_at=datetime.fromisoformat(data['created_at']),
            turns_data=data.get('turns_data', [])
        )

    def __repr__(self) -> str:
        return f"ArgumentNode(id={self.node_id[:8]}..., type={self.node_type.value}, topic='{self.topic[:50]}...')"


@dataclass
class Edge:
    """Typed relationship between ArgumentNodes"""

    from_node_id: str                # Source node
    to_node_id: str                  # Target node
    edge_type: EdgeType              # Type of relationship
    description: Optional[str] = None  # Human-readable explanation
    confidence: float = 1.0          # 0.0-1.0, how confident we are

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'edge_type': self.edge_type.value,
            'description': self.description,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Edge':
        """Create Edge from dictionary"""
        return cls(
            from_node_id=data['from_node_id'],
            to_node_id=data['to_node_id'],
            edge_type=EdgeType(data['edge_type']),
            description=data.get('description'),
            confidence=data.get('confidence', 1.0)
        )

    def __repr__(self) -> str:
        return f"Edge({self.from_node_id[:8]}... --[{self.edge_type.value}]--> {self.to_node_id[:8]}...)"


class DebateDAG:
    """Directed Acyclic Graph storing ArgumentNodes and Edges"""

    def __init__(self):
        self.nodes: Dict[str, ArgumentNode] = {}
        self.edges: List[Edge] = []
        self.metadata: Dict = {
            'created_at': datetime.now().isoformat(),
            'version': '0.3.0'
        }

    def add_node(self, node: ArgumentNode) -> None:
        """Add a node to the graph"""
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists in graph")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph"""
        # Validate nodes exist
        if edge.from_node_id not in self.nodes:
            raise ValueError(f"Source node {edge.from_node_id} not found in graph")
        if edge.to_node_id not in self.nodes:
            raise ValueError(f"Target node {edge.to_node_id} not found in graph")

        # Check for duplicate edges
        for existing_edge in self.edges:
            if (existing_edge.from_node_id == edge.from_node_id and
                existing_edge.to_node_id == edge.to_node_id and
                existing_edge.edge_type == edge.edge_type):
                # Edge already exists, skip
                return

        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[ArgumentNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def find_nodes_by_topic(self, topic_query: str) -> List[ArgumentNode]:
        """Find nodes by topic substring match (case-insensitive)"""
        topic_lower = topic_query.lower()
        return [
            node for node in self.nodes.values()
            if topic_lower in node.topic.lower()
        ]

    def find_nodes_by_tags(self, tags: Set[str]) -> List[ArgumentNode]:
        """Find nodes that have any of the given tags"""
        return [
            node for node in self.nodes.values()
            if node.theme_tags & tags  # Set intersection
        ]

    def find_nodes_by_type(self, node_type: NodeType) -> List[ArgumentNode]:
        """Find all nodes of a given type"""
        return [
            node for node in self.nodes.values()
            if node.node_type == node_type
        ]

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Get all edges pointing to this node"""
        return [edge for edge in self.edges if edge.to_node_id == node_id]

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all edges originating from this node"""
        return [edge for edge in self.edges if edge.from_node_id == node_id]

    def get_all_nodes(self) -> List[ArgumentNode]:
        """Get all nodes sorted by creation time"""
        return sorted(self.nodes.values(), key=lambda n: n.created_at)

    def save(self, path: Path) -> None:
        """Save graph to JSON file"""
        data = {
            'metadata': self.metadata,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges]
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'DebateDAG':
        """Load graph from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)

        dag = cls()
        dag.metadata = data.get('metadata', {})

        # Load nodes
        for node_data in data.get('nodes', []):
            node = ArgumentNode.from_dict(node_data)
            dag.nodes[node.node_id] = node

        # Load edges
        for edge_data in data.get('edges', []):
            edge = Edge.from_dict(edge_data)
            dag.edges.append(edge)

        return dag

    def __repr__(self) -> str:
        return f"DebateDAG(nodes={len(self.nodes)}, edges={len(self.edges)})"

    def summary(self) -> str:
        """Generate a text summary of the graph"""
        lines = [
            f"DebateDAG Summary",
            f"================",
            f"Nodes: {len(self.nodes)}",
            f"Edges: {len(self.edges)}",
            f"",
            f"Node Types:",
        ]

        # Count by type
        type_counts = {}
        for node in self.nodes.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1

        for node_type, count in sorted(type_counts.items(), key=lambda x: x[0].value):
            lines.append(f"  {node_type.value}: {count}")

        lines.append("")
        lines.append("Edge Types:")

        # Count by type
        edge_type_counts = {}
        for edge in self.edges:
            edge_type_counts[edge.edge_type] = edge_type_counts.get(edge.edge_type, 0) + 1

        for edge_type, count in sorted(edge_type_counts.items(), key=lambda x: x[0].value):
            lines.append(f"  {edge_type.value}: {count}")

        return "\n".join(lines)


# Helper function for creating edges
def create_edge(from_node: ArgumentNode,
                to_node: ArgumentNode,
                edge_type: EdgeType,
                description: Optional[str] = None,
                confidence: float = 1.0) -> Edge:
    """Helper to create an edge between two nodes"""
    return Edge(
        from_node_id=from_node.node_id,
        to_node_id=to_node.node_id,
        edge_type=edge_type,
        description=description,
        confidence=confidence
    )


if __name__ == "__main__":
    # Quick test
    print("Testing Phase 3 DAG data structures...")

    # Create a DAG
    dag = DebateDAG()

    # Create some nodes
    node1 = ArgumentNode.create(
        node_type=NodeType.EXPLORATION,
        topic="Zarathustra's departure at thirty",
        resolution="Three interpretations emerged: literal, symbolic, structural. Unresolved tension about where meaning resides.",
        passage="When Zarathustra was thirty years old...",
        theme_tags={"departure", "transformation", "meaning"},
        key_claims=[
            "Literalist: Departure is biographical fact",
            "Symbolist: Mountains represent higher consciousness",
            "Structuralist: Deploys archetypal withdrawal motif"
        ]
    )

    node2 = ArgumentNode.create(
        node_type=NodeType.SYNTHESIS,
        topic="Meaning of 'thirty years'",
        resolution="Branch resolved that 'thirty' functions simultaneously as biographical fact, psychological threshold, and genre marker.",
        branch_question="What does thirty years signify?",
        theme_tags={"age", "threshold", "maturity"},
        key_claims=[
            "Not mutually exclusive readings",
            "Age serves multiple functions"
        ]
    )

    # Add nodes
    dag.add_node(node1)
    dag.add_node(node2)

    # Create edge
    edge = create_edge(
        from_node=node1,
        to_node=node2,
        edge_type=EdgeType.BRANCHES_FROM,
        description="Branch debate on age significance"
    )
    dag.add_edge(edge)

    # Test operations
    print(f"\n{dag}")
    print(f"\nNode 1: {node1}")
    print(f"Node 2: {node2}")
    print(f"Edge: {edge}")

    # Test queries
    print(f"\nNodes about 'meaning': {dag.find_nodes_by_topic('meaning')}")
    print(f"Nodes with tag 'threshold': {dag.find_nodes_by_tags({'threshold'})}")
    print(f"Synthesis nodes: {dag.find_nodes_by_type(NodeType.SYNTHESIS)}")

    # Test save/load
    test_path = Path("/tmp/test_dag.json")
    dag.save(test_path)
    print(f"\n✓ Saved to {test_path}")

    loaded_dag = DebateDAG.load(test_path)
    print(f"✓ Loaded: {loaded_dag}")
    print(f"\n{loaded_dag.summary()}")

    print("\n✅ All tests passed!")
