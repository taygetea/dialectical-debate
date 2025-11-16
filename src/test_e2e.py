#!/usr/bin/env python3
"""
End-to-End Integration Test

Tests the complete graph-building workflow with real LLM debates.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import Agent, Logger
from session import DebateSession

# Suppress verbose output
import os
os.environ['PYTHONUNBUFFERED'] = '1'

def main():
    """Run end-to-end test"""

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"e2e_test_{timestamp}"

    print(f"Starting end-to-end test: {session_name}")
    print("=" * 60)

    # Create agents
    agents = [
        Agent(
            "The Literalist",
            "You interpret text literally and factually, focusing on what is explicitly stated.",
            "Concrete claims and logical consistency"
        ),
        Agent(
            "The Symbolist",
            "You see deeper symbolic and archetypal meanings beneath the surface.",
            "Metaphorical significance and universal patterns"
        ),
        Agent(
            "The Structuralist",
            "You analyze underlying structures, patterns, and formal relationships.",
            "Systems, frameworks, and organizational principles"
        )
    ]

    # Create session
    session = DebateSession(session_name)

    # Create logger
    log_path = session.session_dir / f"debate_log.md"
    logger = Logger(log_path)

    # Test passage (from user)
    passage = """the teeming chaos of willful being has knowable structure. humans, fully cast as limited animals, have a much maligned conception towards structure in the void, but we are not mistaken about the shape we feel in the dark. the facets at our fingers are partial images to blind men."""

    print(f"\n1. Processing main passage...")
    print(f"   Passage: {passage[:80]}...")

    node1 = session.process_passage(
        passage=passage,
        agents=agents,
        logger=logger,
        max_rounds=3
    )

    print(f"   ✓ Created node: {node1.node_id[:8]}")
    print(f"   Topic: {node1.topic}")
    print(f"   Type: {node1.node_type.value}")

    # Process a branch
    print(f"\n2. Processing branch question...")
    branch_question = "What does 'partial images to blind men' suggest about the nature of human knowledge?"

    node2 = session.process_branch(
        branch_question=branch_question,
        parent_node_id=node1.node_id,
        agents=agents,
        logger=logger,
        max_rounds=2
    )

    print(f"   ✓ Created branch: {node2.node_id[:8]}")
    print(f"   Topic: {node2.topic}")
    print(f"   Type: {node2.node_type.value}")

    # Get stats
    print(f"\n3. Session Statistics:")
    stats = session.get_stats()
    print(f"   Nodes: {stats['total_nodes']}")
    print(f"   Edges: {stats['total_edges']}")
    print(f"   Node types: {stats['node_types']}")
    print(f"   Edge types: {stats['edge_types']}")

    # Export narrative
    print(f"\n4. Exporting narrative...")
    narrative_path = session.session_dir / "narrative.md"
    session.export_narrative(narrative_path)
    print(f"   ✓ Narrative saved to: {narrative_path}")

    # Export summary
    summary_path = session.session_dir / "summary.txt"
    session.export_summary(summary_path)
    print(f"   ✓ Summary saved to: {summary_path}")

    # Show file sizes
    print(f"\n5. Output files:")
    for file in session.session_dir.iterdir():
        if file.is_file():
            size = file.stat().st_size
            print(f"   {file.name}: {size:,} bytes")

    print(f"\n{'=' * 60}")
    print(f"✅ End-to-end test complete!")
    print(f"\nOutput directory: {session.session_dir}")
    print(f"View narrative: cat {narrative_path}")
    print(f"View log: cat {log_path}")

    return session

if __name__ == "__main__":
    session = main()
