#!/usr/bin/env python3
"""
Branch Stubs - Unexplored Tension Preservation

Stubs represent flagged tensions that were NOT selected for immediate exploration.
They're preserved and can be revisited later when context makes them relevant.

"Discontinuity as strength": Coming back to questions with new perspective.

Part of Phase 4: Computational DAG Architecture
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import llm_call


@dataclass
class BranchStub:
    """An unexplored tension preserved for potential later exploration

    Stubs represent "roads not taken" - tensions that were flagged but not
    immediately explored. As the DAG grows and context changes, stubs may
    become relevant and get revisited.

    Lifecycle:
    1. Created - Tension flagged but not selected
    2. Stubbed - Stored in DAG.stubs
    3. Checked - Periodically checked for relevance
    4. Explored - If relevant, becomes a new branch
    5. Superseded - If another node addresses it
    """

    # Core identification
    stub_id: str
    question: str
    parent_node_id: str

    # Origin tracking
    flagged_at_turn: int
    observer_name: str
    urgency: float  # Original urgency when flagged

    # Status tracking
    status: str = "stub"  # "stub", "explored", "superseded"
    created_at: datetime = field(default_factory=datetime.now)

    # Revisit tracking
    revisit_checks: List[Dict] = field(default_factory=list)

    # Optional metadata
    rationale: str = ""
    context_excerpt: str = ""

    def __str__(self) -> str:
        status_emoji = {
            "stub": "📌",
            "explored": "✓",
            "superseded": "⊘"
        }
        emoji = status_emoji.get(self.status, "?")
        return f"{emoji} [{self.status.upper()}] {self.question} (urgency: {self.urgency:.2f})"

    def should_revisit(
        self,
        current_dag: 'DebateDAG',
        threshold: float = 0.6
    ) -> tuple[bool, str]:
        """Check if this stub becomes relevant given current DAG state

        Uses LLM to compare stub question to current nodes/branches.
        Returns (should_explore, reason).

        Args:
            current_dag: Current state of the debate DAG
            threshold: Relevance score threshold (0.0-1.0)

        Returns:
            (bool, str): (should_explore, reason)
        """

        if self.status != "stub":
            return (False, f"Already {self.status}")

        # Get context from current DAG
        node_summaries = []
        for node_id, node in list(current_dag.nodes.items())[:10]:  # Limit to recent nodes
            summary = f"- {node.concise_summary or node.topic[:100]}"
            node_summaries.append(summary)

        dag_context = "\n".join(node_summaries) if node_summaries else "No nodes yet"

        system_prompt = """You are evaluating if an unexplored question (stub) has become relevant.

A stub should be explored if:
- Current debates now provide context that makes it important
- New nodes create tension with the stub question
- The DAG has evolved in a way that makes this question central

A stub should stay stubbed if:
- Still tangential to current discussions
- Already addressed by existing nodes
- Not yet relevant given current context

Output JSON:
{
  "relevance_score": 0.0-1.0,
  "should_explore": true/false,
  "reason": "Why this stub is/isn't relevant now"
}"""

        user_prompt = f"""Stub question (from turn {self.flagged_at_turn}):
"{self.question}"

Original rationale: {self.rationale}
Original urgency: {self.urgency:.2f}

Current DAG state ({len(current_dag.nodes)} nodes):
{dag_context}

Has this stub become relevant?

JSON:"""

        response = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.4,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse response
        try:
            # Clean response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                response = response[start:end+1]

            data = json.loads(response)

            relevance = data.get('relevance_score', 0.0)
            should_explore = data.get('should_explore', False)
            reason = data.get('reason', 'Relevance check complete')

            # Record this check
            self.revisit_checks.append({
                'timestamp': datetime.now().isoformat(),
                'relevance_score': relevance,
                'should_explore': should_explore,
                'reason': reason,
                'dag_size': len(current_dag.nodes)
            })

            # Return decision
            if should_explore and relevance >= threshold:
                return (True, reason)
            else:
                return (False, reason)

        except (json.JSONDecodeError, KeyError) as e:
            # On error, default to not exploring
            self.revisit_checks.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'dag_size': len(current_dag.nodes)
            })
            return (False, f"Error evaluating relevance: {e}")

    def mark_explored(self, node_id: str):
        """Mark this stub as explored"""
        self.status = "explored"
        self.revisit_checks.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'explored',
            'node_id': node_id
        })

    def mark_superseded(self, reason: str):
        """Mark this stub as superseded by other nodes"""
        self.status = "superseded"
        self.revisit_checks.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'superseded',
            'reason': reason
        })

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'stub_id': self.stub_id,
            'question': self.question,
            'parent_node_id': self.parent_node_id,
            'flagged_at_turn': self.flagged_at_turn,
            'observer_name': self.observer_name,
            'urgency': self.urgency,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'revisit_checks': self.revisit_checks,
            'rationale': self.rationale,
            'context_excerpt': self.context_excerpt
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BranchStub':
        """Deserialize from dictionary"""
        data_copy = data.copy()
        if 'created_at' in data_copy and isinstance(data_copy['created_at'], str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        return cls(**data_copy)

    @classmethod
    def from_tension_flag(
        cls,
        tension_flag: 'TensionFlag',
        parent_node_id: str
    ) -> 'BranchStub':
        """Create stub from a TensionFlag that wasn't selected for exploration"""
        return cls(
            stub_id=f"stub_{tension_flag.flag_id}",
            question=tension_flag.question,
            parent_node_id=parent_node_id,
            flagged_at_turn=tension_flag.turn_number,
            observer_name=tension_flag.observer_name,
            urgency=tension_flag.urgency,
            rationale=tension_flag.rationale,
            context_excerpt=tension_flag.context_excerpt
        )


if __name__ == "__main__":
    # Test stub creation and lifecycle
    print("Testing BranchStub...")

    # Create a mock stub
    stub = BranchStub(
        stub_id="stub_test_1",
        question="What is the ontological status of 'structure' itself?",
        parent_node_id="node_main",
        flagged_at_turn=3,
        observer_name="Dialectical Observer",
        urgency=0.7,
        rationale="This question addresses a fundamental assumption in the debate",
        context_excerpt="...structure in the void..."
    )

    print(f"\nCreated: {stub}")
    print(f"Status: {stub.status}")

    # Test serialization
    data = stub.to_dict()
    print(f"\nSerialized: {len(data)} fields")

    restored = BranchStub.from_dict(data)
    print(f"Restored: {restored}")
    assert restored.question == stub.question

    # Test status changes
    stub.mark_superseded("Addressed by node B2")
    print(f"\nAfter superseding: {stub}")
    print(f"Revisit checks: {len(stub.revisit_checks)}")

    # Test from_tension_flag (mock)
    class MockTensionFlag:
        def __init__(self):
            self.flag_id = "flag_123"
            self.question = "Mock question"
            self.turn_number = 5
            self.observer_name = "Mock Observer"
            self.urgency = 0.6
            self.rationale = "Mock rationale"
            self.context_excerpt = "Mock context"

    mock_flag = MockTensionFlag()
    stub2 = BranchStub.from_tension_flag(mock_flag, "node_parent")
    print(f"\nFrom tension flag: {stub2}")

    print("\n✅ BranchStub test complete!")
