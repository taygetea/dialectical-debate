#!/usr/bin/env python3
"""
Debate Monitor - Real-Time Observer Tension Flagging

Observers watch debates as they happen and flag tensions/branch points
in real-time, rather than waiting for debate completion.

Part of Phase 4: Computational DAG Architecture
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import Observer, DebateTurn


@dataclass
class TensionFlag:
    """A potential branch point identified by an observer during a debate

    Represents a tension, gap, assumption, or unexplored angle that could
    warrant further investigation through a branch debate.
    """

    # Core identification
    turn_number: int  # Which turn triggered this flag
    question: str  # The branch question to explore
    observer_name: str  # Which observer flagged this

    # Scoring and context
    urgency: float  # 0.0 to 1.0, how important is this tension
    context_excerpt: str  # Relevant excerpt from the turn that triggered it
    rationale: str  # Why the observer flagged this

    # Metadata
    flagged_at: datetime = field(default_factory=datetime.now)
    flag_id: str = field(default_factory=lambda: f"flag_{datetime.now().timestamp()}")

    def __str__(self) -> str:
        return f"[Turn {self.turn_number}] {self.observer_name}: {self.question} (urgency: {self.urgency:.2f})"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'turn_number': self.turn_number,
            'question': self.question,
            'observer_name': self.observer_name,
            'urgency': self.urgency,
            'context_excerpt': self.context_excerpt,
            'rationale': self.rationale,
            'flagged_at': self.flagged_at.isoformat(),
            'flag_id': self.flag_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TensionFlag':
        """Create from dictionary"""
        data_copy = data.copy()
        if 'flagged_at' in data_copy and isinstance(data_copy['flagged_at'], str):
            data_copy['flagged_at'] = datetime.fromisoformat(data_copy['flagged_at'])
        return cls(**data_copy)


class DebateMonitor:
    """Watches debates in real-time and collects tension flags from observers

    Observers process each turn as it happens, flagging potential branch points.
    Not all turns generate flags - observers have thresholds for significance.

    This enables:
    - Multiple branch points identified throughout debate (not just at end)
    - Flags at specific turn numbers (can trace where tension emerged)
    - Prioritization based on urgency scores
    - Selection of which tensions to explore vs. stub
    """

    def __init__(self, observers: List[Observer], verbose: bool = True):
        """Initialize monitor with observers

        Args:
            observers: List of Observer instances to watch the debate
            verbose: Print flags as they're generated
        """
        self.observers = observers
        self.verbose = verbose
        self.flagged_tensions: List[TensionFlag] = []

    def process_turn(
        self,
        turn: DebateTurn,
        full_transcript: List[DebateTurn]
    ) -> List[TensionFlag]:
        """Process a debate turn and check if observers flag any tensions

        Called after each turn in the debate. Each observer examines the turn
        and full transcript to see if a tension worth branching has emerged.

        Args:
            turn: The turn that just happened
            full_transcript: Full debate history including this turn

        Returns:
            List of TensionFlag objects created this turn (may be empty)
        """
        new_flags = []
        turn_number = len(full_transcript)

        for observer in self.observers:
            # Check if this observer sees a tension
            tension_data = observer.check_for_tension(turn, full_transcript)

            if tension_data:
                # Observer flagged something - create TensionFlag
                urgency = observer.rate_urgency(tension_data, full_transcript)

                flag = TensionFlag(
                    turn_number=turn_number,
                    question=tension_data['question'],
                    observer_name=observer.name,
                    urgency=urgency,
                    context_excerpt=tension_data.get('context', turn.content[:200]),
                    rationale=tension_data.get('rationale', 'Observer identified tension')
                )

                new_flags.append(flag)
                self.flagged_tensions.append(flag)

                if self.verbose:
                    print(f"\n⚠ TENSION FLAGGED at turn {turn_number}")
                    print(f"   Observer: {observer.name}")
                    print(f"   Question: {flag.question}")
                    print(f"   Urgency: {urgency:.2f}")
                    print(f"   Rationale: {flag.rationale[:100]}...")

        return new_flags

    def get_flags_by_urgency(self, min_urgency: float = 0.0) -> List[TensionFlag]:
        """Get all flags above a certain urgency threshold, sorted by urgency

        Args:
            min_urgency: Minimum urgency score (0.0 to 1.0)

        Returns:
            List of flags sorted by urgency (highest first)
        """
        filtered = [f for f in self.flagged_tensions if f.urgency >= min_urgency]
        return sorted(filtered, key=lambda f: f.urgency, reverse=True)

    def get_flags_by_observer(self, observer_name: str) -> List[TensionFlag]:
        """Get all flags from a specific observer

        Args:
            observer_name: Name of the observer

        Returns:
            List of flags from this observer
        """
        return [f for f in self.flagged_tensions if f.observer_name == observer_name]

    def get_flags_at_turn(self, turn_number: int) -> List[TensionFlag]:
        """Get all flags that were triggered at a specific turn

        Args:
            turn_number: Turn number to query

        Returns:
            List of flags from this turn
        """
        return [f for f in self.flagged_tensions if f.turn_number == turn_number]

    def summary(self) -> str:
        """Generate summary of monitoring session

        Returns:
            Multi-line string summarizing all flagged tensions
        """
        if not self.flagged_tensions:
            return "No tensions flagged during debate."

        lines = [
            f"\n{'='*80}",
            f"MONITORING SUMMARY: {len(self.flagged_tensions)} tensions flagged",
            f"{'='*80}\n"
        ]

        # Group by observer
        observer_counts = {}
        for flag in self.flagged_tensions:
            observer_counts[flag.observer_name] = observer_counts.get(flag.observer_name, 0) + 1

        lines.append("By observer:")
        for observer, count in observer_counts.items():
            lines.append(f"  {observer}: {count} tensions")

        # List all flags
        lines.append("\nAll flagged tensions:")
        for i, flag in enumerate(self.flagged_tensions, 1):
            lines.append(f"\n{i}. {flag}")
            lines.append(f"   Rationale: {flag.rationale[:100]}...")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serialize monitor state to dictionary

        Returns:
            Dictionary containing all flagged tensions
        """
        return {
            'flagged_tensions': [f.to_dict() for f in self.flagged_tensions],
            'observer_names': [o.name for o in self.observers]
        }

    @classmethod
    def from_dict(cls, data: Dict, observers: List[Observer]) -> 'DebateMonitor':
        """Reconstruct monitor from dictionary

        Args:
            data: Dictionary from to_dict()
            observers: List of Observer instances

        Returns:
            DebateMonitor with restored state
        """
        monitor = cls(observers, verbose=False)
        monitor.flagged_tensions = [
            TensionFlag.from_dict(f) for f in data['flagged_tensions']
        ]
        return monitor


if __name__ == "__main__":
    # Test with mock data
    print("Testing DebateMonitor...")

    # Create mock observer (without full LLM integration for now)
    class MockObserver:
        def __init__(self, name: str):
            self.name = name
            self.call_count = 0

        def check_for_tension(self, turn, transcript):
            self.call_count += 1
            # Flag on turns 3 and 5
            if len(transcript) in [3, 5]:
                return {
                    'question': f"Mock question at turn {len(transcript)}",
                    'context': turn.content[:100],
                    'rationale': f"This is turn {len(transcript)}, which triggers the mock observer"
                }
            return None

        def rate_urgency(self, tension_data, transcript):
            # Higher urgency at later turns
            return min(1.0, len(transcript) / 10.0)

    # Create mock turns
    mock_turns = [
        DebateTurn("Agent A", f"Argument {i}", (i // 3) + 1)
        for i in range(1, 7)
    ]

    # Create monitor
    observer = MockObserver("Mock Observer")
    monitor = DebateMonitor([observer], verbose=True)

    # Process turns
    print("\nProcessing turns...")
    for i, turn in enumerate(mock_turns, 1):
        transcript = mock_turns[:i]
        new_flags = monitor.process_turn(turn, transcript)

    # Print summary
    print(monitor.summary())

    # Test querying
    print(f"\nFlags with urgency > 0.4: {len(monitor.get_flags_by_urgency(0.4))}")
    print(f"Flags at turn 3: {len(monitor.get_flags_at_turn(3))}")

    # Test serialization
    data = monitor.to_dict()
    print(f"\nSerialized {len(data['flagged_tensions'])} flags")

    print("\n✅ DebateMonitor test complete!")
