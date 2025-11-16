#!/usr/bin/env python3
"""
Phase 3: Node Creation Logic

Detects when debates reach semantic completion and creates ArgumentNodes.
"""

import sys
from pathlib import Path

# Add parent directory to path to import dialectic_poc
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import DebateTurn, llm_call
from phase3_dag import ArgumentNode, NodeType
from typing import List, Tuple, Optional, Set
import re


class NodeCreationDetector:
    """Detects when a debate reaches semantic completion"""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns

        # Explicit completion markers
        self.synthesis_markers = [
            "we agree",
            "consensus emerges",
            "resolved",
            "synthesis",
            "converge on",
            "common ground"
        ]

        self.impasse_markers = [
            "fundamental disagreement",
            "irreconcilable",
            "cannot be resolved",
            "remains in tension",
            "unresolved",
            "incompatible"
        ]

    def check_completion(self,
                        transcript: List[DebateTurn],
                        branch_question: Optional[str] = None) -> Tuple[bool, Optional[NodeType]]:
        """
        Check if debate has reached semantic completion

        Returns: (is_complete, node_type)
        """

        if len(transcript) == 0:
            return False, None

        # Method 1: Explicit markers in recent turns
        recent_text = " ".join([t.content for t in transcript[-2:]]).lower()

        # Check impasse markers first (they're more specific)
        for marker in self.impasse_markers:
            if marker in recent_text:
                return True, NodeType.IMPASSE

        for marker in self.synthesis_markers:
            if marker in recent_text:
                return True, NodeType.SYNTHESIS

        # Method 2: Q&A completion (for branch debates)
        if branch_question and self._question_answered(transcript, branch_question):
            return True, NodeType.SYNTHESIS

        # Method 3: Repetition detection
        if self._detect_repetition(transcript):
            return True, NodeType.IMPASSE

        # Method 4: Max turns fallback
        if len(transcript) >= self.max_turns:
            return True, NodeType.EXPLORATION

        return False, None

    def _question_answered(self,
                          transcript: List[DebateTurn],
                          question: str) -> bool:
        """
        Check if a question has been answered in the debate

        Heuristic: Look for synthesis-like language in later turns
        """
        if len(transcript) < 3:
            return False

        # Check last few turns for resolution language
        recent_text = " ".join([t.content for t in transcript[-3:]]).lower()

        answer_indicators = [
            "the answer",
            "resolves to",
            "we find that",
            "synthesis",
            "what emerged",
            "resolution"
        ]

        return any(indicator in recent_text for indicator in answer_indicators)

    def _detect_repetition(self, transcript: List[DebateTurn]) -> bool:
        """
        Detect if agents are repeating themselves (circular arguments)

        Heuristic: Check if vocabulary of recent turns is very similar
        """
        if len(transcript) < 6:
            return False

        # Compare last 3 turns to previous 3 turns
        recent_turns = transcript[-3:]
        previous_turns = transcript[-6:-3]

        # Extract words
        recent_words = set()
        for turn in recent_turns:
            words = set(turn.content.lower().split())
            recent_words.update(words)

        previous_words = set()
        for turn in previous_turns:
            words = set(turn.content.lower().split())
            previous_words.update(words)

        # Jaccard similarity
        if len(recent_words) == 0 or len(previous_words) == 0:
            return False

        overlap = len(recent_words & previous_words)
        total = len(recent_words | previous_words)
        similarity = overlap / total

        # High similarity suggests repetition
        return similarity > 0.75


class NodeFactory:
    """Creates ArgumentNodes from debate transcripts using LLM"""

    @staticmethod
    def create_node_from_transcript(
        node_type: NodeType,
        transcript: List[DebateTurn],
        passage: Optional[str] = None,
        branch_question: Optional[str] = None
    ) -> ArgumentNode:
        """
        Create an ArgumentNode from a debate transcript

        Uses LLM to generate:
        - topic (1-2 sentence summary)
        - resolution (paragraph summary)
        - theme_tags (key concepts)
        - key_claims (main assertions)
        """

        # Convert transcript to text
        transcript_text = "\n\n".join([
            f"**{turn.agent_name}** (Round {turn.round_num}):\n{turn.content}"
            for turn in transcript
        ])

        # Generate topic (1-2 sentences)
        topic = NodeFactory._generate_topic(transcript_text, passage, branch_question)

        # Generate resolution (paragraph)
        resolution = NodeFactory._generate_resolution(
            transcript_text, node_type, passage, branch_question
        )

        # Extract theme tags
        theme_tags = NodeFactory._extract_theme_tags(transcript_text, topic)

        # Extract key claims
        key_claims = NodeFactory._extract_key_claims(transcript_text)

        # Convert turns to serializable dicts
        turns_data = [
            {
                'agent_name': turn.agent_name,
                'content': turn.content,
                'round_num': turn.round_num
            }
            for turn in transcript
        ]

        return ArgumentNode.create(
            node_type=node_type,
            topic=topic,
            resolution=resolution,
            passage=passage,
            branch_question=branch_question,
            theme_tags=theme_tags,
            key_claims=key_claims,
            turns_data=turns_data
        )

    @staticmethod
    def _generate_topic(
        transcript_text: str,
        passage: Optional[str],
        branch_question: Optional[str]
    ) -> str:
        """Generate 1-2 sentence topic summary"""

        system_prompt = "You generate concise topic summaries for philosophical debates. Output 1-2 sentences maximum."

        context = ""
        if passage:
            context += f"Original passage: {passage}\n\n"
        if branch_question:
            context += f"Question discussed: {branch_question}\n\n"

        user_prompt = f"""{context}Debate transcript:
{transcript_text[:1000]}...

Generate a 1-2 sentence topic summary:"""

        topic = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        return topic.strip()

    @staticmethod
    def _generate_resolution(
        transcript_text: str,
        node_type: NodeType,
        passage: Optional[str],
        branch_question: Optional[str]
    ) -> str:
        """Generate paragraph resolution summary"""

        system_prompt = f"""You summarize philosophical debates. Focus on:
- What positions emerged
- What got resolved (if anything)
- What remains in tension

The debate resulted in: {node_type.value}

Output a single paragraph (3-5 sentences)."""

        context = ""
        if passage:
            context += f"Original passage: {passage}\n\n"
        if branch_question:
            context += f"Question discussed: {branch_question}\n\n"

        user_prompt = f"""{context}Debate transcript:
{transcript_text}

Paragraph summary:"""

        resolution = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.4,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        return resolution.strip()

    @staticmethod
    def _extract_theme_tags(transcript_text: str, topic: str) -> Set[str]:
        """Extract theme tags using LLM"""

        system_prompt = """Extract 3-5 key thematic concepts from this debate as single-word or hyphenated tags.

Examples: "free-will", "causation", "agency", "transformation", "meaning"

Output as comma-separated list."""

        user_prompt = f"""Topic: {topic}

Transcript (excerpt):
{transcript_text[:800]}...

Key theme tags (comma-separated):"""

        tags_text = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse comma-separated tags
        tags = set()
        for tag in tags_text.split(','):
            tag = tag.strip().lower()
            # Remove quotes if present
            tag = tag.strip('"').strip("'")
            if tag:
                tags.add(tag)

        return tags

    @staticmethod
    def _extract_key_claims(transcript_text: str) -> List[str]:
        """Extract key claims using LLM"""

        system_prompt = """Extract the 3-5 most important claims or assertions from this debate.

Format each as: "Speaker: Claim"

Example: "Literalist: Departure is biographical fact"
"""

        user_prompt = f"""Debate transcript:
{transcript_text}

Key claims (one per line):"""

        claims_text = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"
        )

        # Parse line-separated claims
        claims = []
        for line in claims_text.split('\n'):
            line = line.strip()
            # Remove leading numbers/bullets
            line = re.sub(r'^\d+[\.)]\s*', '', line)
            line = re.sub(r'^[-*•]\s*', '', line)
            if line:
                claims.append(line)

        return claims[:5]  # Max 5 claims


if __name__ == "__main__":
    # Test with mock data
    print("Testing NodeCreationDetector and NodeFactory...")

    # Create mock turns
    mock_turns = [
        DebateTurn("The Literalist", "This is a literal fact.", 1),
        DebateTurn("The Symbolist", "This is symbolic meaning.", 1),
        DebateTurn("The Structuralist", "This follows narrative patterns.", 1),
        DebateTurn("The Literalist", "We fundamentally disagree here.", 2),
        DebateTurn("The Symbolist", "The tension remains unresolved.", 2),
    ]

    # Test detector
    detector = NodeCreationDetector(max_turns=10)

    # Should detect impasse
    is_complete, node_type = detector.check_completion(mock_turns)
    print(f"\nDetection result: complete={is_complete}, type={node_type}")

    if is_complete:
        print(f"✓ Detected completion: {node_type.value}")
    else:
        print("✗ No completion detected")

    # Test repetition detection
    repetitive_turns = mock_turns * 2  # Repeat same turns
    is_complete, node_type = detector.check_completion(repetitive_turns)
    print(f"\nRepetition test: complete={is_complete}, type={node_type}")

    # Test max turns
    many_turns = mock_turns * 3
    is_complete, node_type = detector.check_completion(many_turns)
    print(f"\nMax turns test: complete={is_complete}, type={node_type}")

    print("\n✅ NodeCreationDetector tests complete!")

    # Note: NodeFactory tests require actual LLM calls, skip for now
    print("\n(NodeFactory tests skipped - require LLM access)")
