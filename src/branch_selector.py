#!/usr/bin/env python3
"""
Branch Selector - Automatic Branch Prioritization

Decides which flagged tensions to explore immediately vs. stub for later.
Supports multiple selection strategies to maximize coverage or urgency.

Part of Phase 4: Computational DAG Architecture
"""

import sys
from pathlib import Path
from typing import List, Tuple
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from debate_monitor import TensionFlag
from dialectic_poc import llm_call


class BranchSelector:
    """Selects which flagged tensions to explore vs. stub

    Given multiple flagged tensions, decides which subset to explore
    based on strategy (diverse, urgent, deep, meta).

    Unexplored tensions become stubs for potential later revisiting.
    """

    def __init__(self, verbose: bool = True):
        """Initialize selector

        Args:
            verbose: Print selection reasoning
        """
        self.verbose = verbose

    def select_branches(
        self,
        flagged_tensions: List[TensionFlag],
        max_branches: int = 3,
        strategy: str = "diverse"
    ) -> Tuple[List[TensionFlag], List[TensionFlag]]:
        """Select which tensions to explore vs. stub

        Args:
            flagged_tensions: All tensions flagged by observers
            max_branches: Maximum number to explore (rest become stubs)
            strategy: Selection strategy
                - "diverse": Maximize difference between selected questions (default)
                - "urgent": Highest urgency scores first
                - "deep": Prioritize questions likely to spawn sub-branches
                - "meta": Prioritize questions about the debate itself

        Returns:
            (selected, stubbed): Tuple of two lists
        """

        if len(flagged_tensions) == 0:
            return ([], [])

        if len(flagged_tensions) <= max_branches:
            # All tensions can be explored
            return (flagged_tensions, [])

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"BRANCH SELECTION: {len(flagged_tensions)} tensions, selecting {max_branches}")
            print(f"Strategy: {strategy}")
            print(f"{'='*80}\n")

        # Dispatch to strategy
        if strategy == "urgent":
            selected = self._select_urgent(flagged_tensions, max_branches)
        elif strategy == "deep":
            selected = self._select_deep(flagged_tensions, max_branches)
        elif strategy == "meta":
            selected = self._select_meta(flagged_tensions, max_branches)
        else:  # "diverse" is default
            selected = self._select_diverse(flagged_tensions, max_branches)

        # Everything else becomes a stub
        stubbed = [t for t in flagged_tensions if t not in selected]

        if self.verbose:
            print(f"\nSELECTED {len(selected)} for exploration:")
            for i, tension in enumerate(selected, 1):
                print(f"  {i}. {tension.question[:80]}...")
                print(f"     Observer: {tension.observer_name}, Urgency: {tension.urgency:.2f}")

            print(f"\nSTUBBED {len(stubbed)} for later:")
            for i, tension in enumerate(stubbed, 1):
                print(f"  {i}. {tension.question[:80]}...")
                print(f"     Observer: {tension.observer_name}, Urgency: {tension.urgency:.2f}")

        return (selected, stubbed)

    def _select_urgent(
        self,
        tensions: List[TensionFlag],
        max_branches: int
    ) -> List[TensionFlag]:
        """Select tensions with highest urgency scores"""
        sorted_tensions = sorted(tensions, key=lambda t: t.urgency, reverse=True)
        return sorted_tensions[:max_branches]

    def _select_diverse(
        self,
        tensions: List[TensionFlag],
        max_branches: int
    ) -> List[TensionFlag]:
        """Select tensions that are maximally different from each other

        Uses LLM to compute semantic distance and greedily selects
        diverse questions to maximize coverage.
        """

        if len(tensions) <= max_branches:
            return tensions

        # Start with highest urgency
        selected = [max(tensions, key=lambda t: t.urgency)]
        remaining = [t for t in tensions if t != selected[0]]

        # Greedily add most different from already selected
        while len(selected) < max_branches and remaining:
            # Find tension most different from selected set
            best_tension = None
            best_score = -1

            for candidate in remaining:
                # Compute diversity score (how different from selected)
                diversity = self._compute_diversity(candidate, selected)

                if diversity > best_score:
                    best_score = diversity
                    best_tension = candidate

            if best_tension:
                selected.append(best_tension)
                remaining = [t for t in remaining if t != best_tension]

        return selected

    def _compute_diversity(
        self,
        candidate: TensionFlag,
        selected: List[TensionFlag]
    ) -> float:
        """Compute how different candidate is from selected set

        Returns average semantic distance from all selected questions.
        """

        if not selected:
            return 1.0

        # Use LLM to compute semantic similarity
        selected_questions = "\n".join([
            f"- {t.question}"
            for t in selected
        ])

        system_prompt = """You are comparing questions for semantic diversity.

Output a diversity score from 0.0 to 1.0:
- 0.0: Questions are nearly identical or address same angle
- 0.5: Questions are related but distinct angles
- 1.0: Questions are completely orthogonal/different

Output ONLY the number."""

        user_prompt = f"""Candidate question:
"{candidate.question}"

Already selected questions:
{selected_questions}

How different is the candidate from the selected set?

Diversity score (0.0-1.0):"""

        response = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse score
        try:
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0', response)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))
            else:
                return 0.5  # Default medium diversity
        except ValueError:
            return 0.5

    def _select_deep(
        self,
        tensions: List[TensionFlag],
        max_branches: int
    ) -> List[TensionFlag]:
        """Select tensions likely to spawn sub-branches

        Prioritizes questions that will generate rich sub-debates.
        """

        # Score each tension for "depth potential"
        scored = []
        for tension in tensions:
            depth_score = self._compute_depth_potential(tension)
            scored.append((depth_score, tension))

        # Sort by depth score descending
        scored.sort(reverse=True, key=lambda x: x[0])

        return [t for _, t in scored[:max_branches]]

    def _compute_depth_potential(self, tension: TensionFlag) -> float:
        """Estimate how likely this question is to spawn sub-branches"""

        system_prompt = """You are evaluating how "deep" a philosophical question is.

A deep question:
- Opens up multiple sub-questions
- Touches fundamental assumptions
- Could branch into many directions

A shallow question:
- Has a straightforward answer
- Unlikely to generate follow-up debates
- Narrow in scope

Output ONLY a depth score from 0.0 to 1.0."""

        user_prompt = f"""Question: "{tension.question}"

Rationale: {tension.rationale}

How likely is this question to spawn rich sub-debates?

Depth score (0.0-1.0):"""

        response = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse score
        try:
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0', response)
            if numbers:
                return float(numbers[0])
            else:
                return 0.5
        except ValueError:
            return 0.5

    def _select_meta(
        self,
        tensions: List[TensionFlag],
        max_branches: int
    ) -> List[TensionFlag]:
        """Select tensions about the debate itself (meta-level)

        Prioritizes questions that question assumptions or framing.
        """

        # Score each tension for "meta-ness"
        scored = []
        for tension in tensions:
            meta_score = self._compute_meta_level(tension)
            scored.append((meta_score, tension))

        # Sort by meta score descending
        scored.sort(reverse=True, key=lambda x: x[0])

        return [t for _, t in scored[:max_branches]]

    def _compute_meta_level(self, tension: TensionFlag) -> float:
        """Estimate how meta-level this question is"""

        system_prompt = """You are evaluating how "meta" a question is.

A meta question:
- Questions the debate's assumptions or framing
- Asks about the debate process itself
- Challenges what's being taken for granted

A non-meta question:
- Asks within the debate's framework
- Accepts the debate's assumptions
- Object-level rather than meta-level

Output ONLY a meta-level score from 0.0 to 1.0."""

        user_prompt = f"""Question: "{tension.question}"

How meta-level is this question?

Meta score (0.0-1.0):"""

        response = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse score
        try:
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0', response)
            if numbers:
                return float(numbers[0])
            else:
                return 0.5
        except ValueError:
            return 0.5


if __name__ == "__main__":
    # Test with mock tensions
    print("Testing BranchSelector...")

    # Create mock tensions
    from debate_monitor import TensionFlag

    mock_tensions = [
        TensionFlag(
            turn_number=2,
            question="What is the ontological status of 'structure' itself?",
            observer_name="Ontological Observer",
            urgency=0.8,
            context_excerpt="...structure in the void...",
            rationale="Fundamental question about the nature of structure"
        ),
        TensionFlag(
            turn_number=3,
            question="How does temporality affect our 'feeling' of structure?",
            observer_name="Temporal Observer",
            urgency=0.6,
            context_excerpt="...we feel in the dark...",
            rationale="Time dimension missing from discussion"
        ),
        TensionFlag(
            turn_number=5,
            question="Can we distinguish chaos from complexity?",
            observer_name="Complexity Observer",
            urgency=0.7,
            context_excerpt="...teeming chaos...",
            rationale="'Chaos' may be mischaracterized"
        ),
        TensionFlag(
            turn_number=5,
            question="Is 'willful being' redundant or meaningful?",
            observer_name="Linguistic Observer",
            urgency=0.5,
            context_excerpt="...willful being...",
            rationale="Possible redundancy in phrasing"
        ),
        TensionFlag(
            turn_number=7,
            question="What role does language play in accessing structure?",
            observer_name="Linguistic Observer",
            urgency=0.4,
            context_excerpt="...conception towards structure...",
            rationale="Language mediates access to structure"
        )
    ]

    selector = BranchSelector(verbose=True)

    # Test urgent strategy
    print("\n" + "="*80)
    print("TEST: Urgent Strategy")
    print("="*80)
    selected, stubbed = selector.select_branches(mock_tensions, max_branches=3, strategy="urgent")
    assert len(selected) == 3
    assert len(stubbed) == 2

    # Test diverse strategy
    print("\n" + "="*80)
    print("TEST: Diverse Strategy")
    print("="*80)
    selected, stubbed = selector.select_branches(mock_tensions, max_branches=2, strategy="diverse")
    assert len(selected) == 2
    assert len(stubbed) == 3

    # Test with fewer tensions than max
    print("\n" + "="*80)
    print("TEST: Fewer tensions than max")
    print("="*80)
    selected, stubbed = selector.select_branches(mock_tensions[:2], max_branches=5, strategy="diverse")
    assert len(selected) == 2
    assert len(stubbed) == 0

    print("\n✅ BranchSelector test complete!")
