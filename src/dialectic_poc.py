#!/usr/bin/env python3
"""
Phase 0: Proof of Core Mechanism
Minimal branching debate system with hand-crafted agents
"""

import subprocess
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

class Logger:
    """Handles logging to both console and file with LLM-powered summarization"""
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.log_entries = []
        self.start_time = datetime.now()

        # Create/clear the output file
        with open(output_file, 'w') as f:
            f.write(f"# Dialectical Debate Log\n")
            f.write(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    def log(self, text: str, to_console: bool = True, to_file: bool = True):
        """Log text to console and/or file"""
        if to_console:
            print(text)
        if to_file:
            with open(self.output_file, 'a') as f:
                f.write(text + '\n')
        self.log_entries.append(text)

    def log_section(self, title: str):
        """Log a major section header"""
        separator = "=" * 80
        self.log(f"\n{separator}")
        self.log(title)
        self.log(f"{separator}\n")

    def log_subsection(self, title: str):
        """Log a subsection header"""
        self.log(f"\n{'-' * 80}")
        self.log(title)
        self.log(f"{'-' * 80}\n")

    def summarize_turn(self, agent_name: str, content: str) -> str:
        """Generate a one-line summary of an agent's turn"""
        system_prompt = """Generate a single-sentence summary (max 15 words) capturing the core argument or move made."""

        user_prompt = f"""Agent: {agent_name}
Content: {content}

One-sentence summary:"""

        summary = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.3,
            model="electronhub/claude-sonnet-4-5-20250929"  # Fallback to Sonnet (Haiku had issues)
        )
        return summary

    def log_turn_with_summary(self, turn: 'DebateTurn'):
        """Log a debate turn with a summary"""
        summary = self.summarize_turn(turn.agent_name, turn.content)

        self.log(f"\n**{turn.agent_name}** (Round {turn.round_num}):")
        self.log(f"_Summary: {summary}_")
        self.log(f"\n{turn.content}\n")

    def log_phase_summary(self, phase_name: str, description: str):
        """Log a summary of what happened in a phase"""
        self.log_subsection(f"PHASE SUMMARY: {phase_name}")
        self.log(description)
        self.log("")

    def finalize(self):
        """Write final timestamp and summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        self.log_section("SESSION COMPLETE")
        self.log(f"Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Duration: {duration.total_seconds():.1f} seconds")
        self.log(f"\nOutput saved to: {self.output_file}")

class Agent:
    """Represents a debate participant with a specific perspective"""
    def __init__(self, name: str, stance: str, focus: str):
        self.name = name
        self.stance = stance
        self.focus = focus

    def get_system_prompt(self) -> str:
        return f"""You are {self.name}, a participant in a philosophical debate.

Your stance: {self.stance}
Your focus: {self.focus}

Be concise but substantive. Stay true to your perspective. Engage with other viewpoints but maintain your interpretive lens."""

class Observer:
    """Represents a biased perspective that identifies branch points in debates"""

    def __init__(
        self,
        name: str,
        bias: str,
        focus: str,
        blind_spots: Optional[List[str]] = None,
        example_questions: Optional[List[str]] = None,
        anti_examples: Optional[List[str]] = None
    ):
        self.name = name
        self.bias = bias
        self.focus = focus
        self.blind_spots = blind_spots or []
        self.example_questions = example_questions or []
        self.anti_examples = anti_examples or []

    def get_system_prompt(self) -> str:
        """Generate system prompt for this observer"""

        prompt = f"""You are {self.name}, an observer of philosophical debates with a specific perspective.

Your core bias: {self.bias}
Your focus: {self.focus}"""

        if self.blind_spots:
            prompt += f"\n\nYou systematically overlook: {', '.join(self.blind_spots)}"

        prompt += """

Your job is NOT to be neutral. Your job is to identify what the debaters are missing FROM YOUR SPECIFIC PERSPECTIVE.

Look for:
- Questions that your bias makes obvious but others ignore
- Angles related to your focus that aren't being explored
- Tensions that only someone with your perspective would notice"""

        if self.example_questions:
            prompt += "\n\nGood questions from your perspective:"
            for ex in self.example_questions:
                prompt += f"\n- {ex}"

        if self.anti_examples:
            prompt += "\n\nBad questions (too generic or reformulations):"
            for anti in self.anti_examples:
                prompt += f"\n- {anti}"

        prompt += "\n\nOutput ONLY a single precise question that deserves its own focused discussion."

        return prompt

    def identify_branch(
        self,
        transcript: List['DebateTurn'],
        passage: str,
        temperature: float = 0.6
    ) -> str:
        """Identify a branch point from this observer's biased perspective"""

        debate_text = "\n".join(str(t) for t in transcript)

        user_prompt = f"""Original passage:
"{passage}"

Debate transcript:
{debate_text}

From YOUR perspective ({self.bias}), what is the single most important question they're NOT asking?

Question:"""

        return llm_call(
            self.get_system_prompt(),
            user_prompt,
            temperature=temperature,
            model="electronhub/claude-sonnet-4-5-20250929"  # Fallback to Sonnet (Haiku had issues)
        )

class DebateTurn:
    """A single turn in the debate"""
    def __init__(self, agent_name: str, content: str, round_num: int):
        self.agent_name = agent_name
        self.content = content
        self.round_num = round_num

    def __str__(self):
        return f"**{self.agent_name}** (Round {self.round_num}):\n{self.content}\n"

def llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    model: str = "electronhub/claude-sonnet-4-5-20250929"
) -> str:
    """Call the llm CLI tool with model selection

    Args:
        system_prompt: System prompt for the model
        user_prompt: User prompt/input
        temperature: Sampling temperature (0.0-1.0)
        model: Model ID (default: Sonnet 4.5)
    """
    try:
        # Using llm with model, system prompt, and temperature
        result = subprocess.run(
            ['llm', '-m', model, '-s', system_prompt, '-o', 'temperature', str(temperature)],
            input=user_prompt,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error calling llm: {e}")
        print(f"stderr: {e.stderr}")
        raise

def summarize_debate_phase(transcript: List[DebateTurn], phase_name: str) -> str:
    """Generate a summary of what happened in a debate phase"""
    debate_text = "\n".join(f"{t.agent_name}: {t.content}" for t in transcript)

    system_prompt = """Summarize what happened in this debate phase in 2-3 sentences. Focus on:
- What positions emerged
- What tensions developed
- What remained unresolved"""

    user_prompt = f"""Phase: {phase_name}

Transcript:
{debate_text}

Summary:"""

    return llm_call(
        system_prompt,
        user_prompt,
        temperature=0.4,
        model="electronhub/claude-sonnet-4-5-20250929"  # Fallback to Sonnet (Haiku had issues)
    )

def run_debate(passage: str, agents: List[Agent], rounds: int = 3, temperature: float = 0.7, logger: Optional[Logger] = None) -> List[DebateTurn]:
    """Run a multi-round debate between agents"""
    transcript: List[DebateTurn] = []

    if logger:
        logger.log_section("MAIN DEBATE ON PASSAGE")
        logger.log(f"Passage:\n{passage}\n")
    else:
        print(f"\n{'='*80}")
        print(f"DEBATE ON PASSAGE")
        print(f"{'='*80}\n")
        print(f"Passage:\n{passage}\n")
        print(f"{'-'*80}\n")

    for round_num in range(1, rounds + 1):
        if logger:
            logger.log(f"\n--- ROUND {round_num} ---\n")
        else:
            print(f"\n--- ROUND {round_num} ---\n")

        for agent in agents:
            # Build context from previous turns
            context = ""
            if transcript:
                context = "\n\nPrevious discussion:\n" + "\n".join(
                    f"{t.agent_name}: {t.content}" for t in transcript
                )

            user_prompt = f"""Passage under discussion:
"{passage}"
{context}

Provide your interpretation and engage with the discussion. Be concise (2-3 sentences)."""

            response = llm_call(agent.get_system_prompt(), user_prompt, temperature)

            turn = DebateTurn(agent.name, response, round_num)
            transcript.append(turn)

            if logger:
                logger.log_turn_with_summary(turn)
            else:
                print(turn)

    # Generate phase summary
    if logger:
        debate_summary = summarize_debate_phase(transcript, "main debate")
        logger.log_phase_summary("Main Debate", debate_summary)

    return transcript

def identify_branch_point(
    transcript: List[DebateTurn],
    passage: str,
    observer: Optional[Observer] = None,
    logger: Optional[Logger] = None
) -> str:
    """Identify branch point - generic or observer-driven

    Args:
        transcript: Debate transcript to analyze
        passage: Original passage being discussed
        observer: Optional observer with biased perspective
        logger: Optional logger for output
    """

    if observer:
        # Observer-driven branch detection
        branch_question = observer.identify_branch(transcript, passage)

        if logger:
            logger.log_section(f"BRANCH POINT IDENTIFIED (via {observer.name})")
            logger.log(f"Observer bias: {observer.bias}")
            logger.log(f"Question: {branch_question}\n")
        else:
            print(f"\n{'='*80}")
            print(f"BRANCH POINT IDENTIFIED (via {observer.name})")
            print(f"{'='*80}")
            print(f"Observer bias: {observer.bias}")
            print(f"Question: {branch_question}\n")
    else:
        # Generic detection (Phase 0 style)
        debate_text = "\n".join(str(t) for t in transcript)

        system_prompt = """You are an observer of philosophical debates. Your job is to identify the single most important unresolved question or tension that deserves its own focused discussion.

Be specific. Not vague questions like "what does this mean?" but precise ones like "Does X refer to Y or Z?" or "Is this claiming A or B?"

Output ONLY the question, nothing else."""

        user_prompt = f"""Original passage:
"{passage}"

Debate transcript:
{debate_text}

What is the single most important unresolved question that deserves its own discussion?"""

        branch_question = llm_call(
            system_prompt,
            user_prompt,
            temperature=0.5,
            model="electronhub/claude-sonnet-4-5-20250929"  # Fallback to Sonnet (Haiku had issues)
        )

        if logger:
            logger.log_section("BRANCH POINT IDENTIFIED (Generic)")
            logger.log(f"Question: {branch_question}\n")
        else:
            print(f"\n{'='*80}")
            print(f"BRANCH POINT IDENTIFIED (Generic)")
            print(f"{'='*80}\n")
            print(f"Question: {branch_question}\n")

    return branch_question

def run_branch_debate(branch_question: str, agents: List[Agent], rounds: int = 2, logger: Optional[Logger] = None) -> List[DebateTurn]:
    """Run a focused debate on a specific branch question"""
    transcript: List[DebateTurn] = []

    if logger:
        logger.log_section("BRANCH DEBATE")
        logger.log(f"Question: {branch_question}\n")
    else:
        print(f"\n{'='*80}")
        print(f"BRANCH DEBATE")
        print(f"{'='*80}\n")
        print(f"Question: {branch_question}\n")
        print(f"{'-'*80}\n")

    for round_num in range(1, rounds + 1):
        if logger:
            logger.log(f"\n--- ROUND {round_num} ---\n")
        else:
            print(f"\n--- ROUND {round_num} ---\n")

        for agent in agents:
            context = ""
            if transcript:
                context = "\n\nPrevious discussion:\n" + "\n".join(
                    f"{t.agent_name}: {t.content}" for t in transcript
                )

            user_prompt = f"""Question under discussion:
"{branch_question}"
{context}

Provide your answer from your specific interpretive lens. Be concise (2-3 sentences)."""

            response = llm_call(agent.get_system_prompt(), user_prompt, temperature=0.7)

            turn = DebateTurn(agent.name, response, round_num)
            transcript.append(turn)

            if logger:
                logger.log_turn_with_summary(turn)
            else:
                print(turn)

    # Generate phase summary
    if logger:
        branch_summary = summarize_debate_phase(transcript, "branch debate")
        logger.log_phase_summary("Branch Debate", branch_summary)

    return transcript

def synthesize_branch_resolution(branch_question: str, branch_transcript: List[DebateTurn], logger: Optional[Logger] = None) -> str:
    """Synthesize the branch debate into a resolution"""
    branch_text = "\n".join(str(t) for t in branch_transcript)

    system_prompt = """You synthesize philosophical debates. Create a concise summary that captures:
1. What perspectives emerged
2. What got resolved (if anything)
3. What remains in tension

Be neutral. Show the landscape, don't pick winners."""

    user_prompt = f"""Question discussed:
"{branch_question}"

Discussion:
{branch_text}

Provide a synthesis (3-4 sentences)."""

    synthesis = llm_call(system_prompt, user_prompt, temperature=0.5)

    if logger:
        logger.log_section("BRANCH SYNTHESIS")
        logger.log(synthesis)
        logger.log("")
    else:
        print(f"\n{'='*80}")
        print(f"BRANCH SYNTHESIS")
        print(f"{'='*80}\n")
        print(synthesis)
        print()

    return synthesis

def merge_branch_back(main_transcript: List[DebateTurn], branch_question: str, branch_synthesis: str, original_passage: str, logger: Optional[Logger] = None) -> str:
    """Generate an enriched understanding that incorporates the branch"""
    main_text = "\n".join(str(t) for t in main_transcript)

    system_prompt = """You create enriched interpretations. Show how the focused discussion (branch) deepens our understanding of the original debate.

Don't just concatenate. Show how the branch resolution changes or illuminates the main discussion."""

    user_prompt = f"""Original passage:
"{original_passage}"

Main debate:
{main_text}

We then explored this question in depth:
"{branch_question}"

And found:
{branch_synthesis}

How does this branch resolution enrich our understanding of the original passage? (4-5 sentences)"""

    enriched = llm_call(system_prompt, user_prompt, temperature=0.6)

    if logger:
        logger.log_section("ENRICHED UNDERSTANDING (MERGE-BACK)")
        logger.log(enriched)
        logger.log("")
    else:
        print(f"\n{'='*80}")
        print(f"ENRICHED UNDERSTANDING")
        print(f"{'='*80}\n")
        print(enriched)
        print()

    return enriched

# ============================================================================
# Observer Personas
# ============================================================================

PHENOMENOLOGIST = Observer(
    name="The Phenomenologist",
    bias="Only first-person lived experience is primary; everything else is derivative",
    focus="What this passage feels like from the inside, subjective states, qualia of experience",
    blind_spots=[
        "Objective structures and patterns",
        "Historical and cultural contexts",
        "Logical consistency",
        "Literary conventions"
    ],
    example_questions=[
        "What is the qualitative character of Zarathustra's experience at the moment of leaving?",
        "What does it feel like, from the inside, to be thirty years old in this narrative?",
        "What first-person certainties or uncertainties define the phenomenal state of 'going into mountains'?"
    ],
    anti_examples=[
        "What does this passage mean?",
        "Is this literal or symbolic?",
        "What are the deeper implications?"
    ]
)

MATERIALIST_HISTORIAN = Observer(
    name="The Materialist Historian",
    bias="All ideas are products of material conditions, power relations, and historical forces",
    focus="Economic base, class dynamics, institutional contexts, who benefits from specific interpretations",
    blind_spots=[
        "Pure phenomenology",
        "Aesthetic considerations",
        "Formal logical validity",
        "Transhistorical truths"
    ],
    example_questions=[
        "What class position enabled Nietzsche to valorize solitary mountain retreats over productive labor?",
        "Who had access to thirty years of life preparation before 'leaving home' in 1880s Europe?",
        "What economic structures made philosophical wandering possible for this figure?"
    ],
    anti_examples=[
        "What is the historical context of this work?",
        "What does this mean?",
        "How should we interpret this passage?"
    ]
)

PRAGMATIST_ENGINEER = Observer(
    name="The Pragmatist Engineer",
    bias="Ideas only matter insofar as they have measurable, practical consequences in the world",
    focus="Actionable implications, decision procedures, implementability, testable predictions",
    blind_spots=[
        "Pure theoretical elegance",
        "Historical context without present relevance",
        "Aesthetic or emotional resonance",
        "Abstract metaphysical claims"
    ],
    example_questions=[
        "If someone wanted to replicate 'leaving home for mountains,' what concrete steps differentiate it from vacation?",
        "What observable behavior change would indicate someone successfully adopted this framework?",
        "What prediction does this passage make that could be falsified?"
    ],
    anti_examples=[
        "What does this mean in practice?",
        "How do we apply this?",
        "What are the implications?"
    ]
)

def main():
    # Create output file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"dialectic_log_{timestamp}.md"

    # Initialize logger
    logger = Logger(output_file)

    # The passage to analyze - using the Zarathustra example from the document
    passage = """When Zarathustra was thirty years old, he left his home and the lake of his home, and went into the mountains."""

    # Hand-craft three maximally different agents
    agents = [
        Agent(
            "The Literalist",
            "Focus on what literally happened in the text",
            "Biographical and historical details, concrete actions, literal meanings"
        ),
        Agent(
            "The Symbolist",
            "Everything is metaphor for internal psychological states",
            "Symbolic meanings, archetypal patterns, emotional/spiritual transformations"
        ),
        Agent(
            "The Structuralist",
            "This follows universal narrative patterns",
            "Story structures, literary conventions, intertextual references"
        )
    ]

    # Phase 0 proof of concept
    logger.log_section("DIALECTICAL DEBATE SYSTEM - Phase 0 Proof of Concept")
    logger.log(f"Passage: {passage}")
    logger.log(f"\nAgents: {', '.join(a.name for a in agents)}")

    # Step 1: Run main debate
    logger.log("\n[Step 1/5] Running main debate...")
    main_transcript = run_debate(passage, agents, rounds=3, temperature=0.7, logger=logger)

    # Step 2: Identify branch point
    logger.log("\n[Step 2/5] Identifying branch point...")
    branch_question = identify_branch_point(main_transcript, passage, logger=logger)

    # Step 3: Run branch debate
    logger.log("\n[Step 3/5] Running branch debate...")
    branch_transcript = run_branch_debate(branch_question, agents, rounds=2, logger=logger)

    # Step 4: Synthesize branch resolution
    logger.log("\n[Step 4/5] Synthesizing branch resolution...")
    branch_synthesis = synthesize_branch_resolution(branch_question, branch_transcript, logger=logger)

    # Step 5: Merge back
    logger.log("\n[Step 5/5] Merging branch back to main debate...")
    enriched_understanding = merge_branch_back(main_transcript, branch_question, branch_synthesis, passage, logger=logger)

    # Final summary
    logger.log_section("EVALUATION")
    logger.log("Success criteria: Did the branch resolution change how we understand the main debate?")
    logger.log("\nReview the enriched understanding above to evaluate.")

    # Finalize logger
    logger.finalize()

if __name__ == "__main__":
    main()
