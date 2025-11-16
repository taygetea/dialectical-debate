#!/usr/bin/env python3
"""
Agent Generation - Two-Phase Initialization

Phase 1: Initialize agents with independent philosophical commitments (passage-blind)
Phase 2: Agents encounter passage and form interpretations from their commitments

This creates genuine philosophical disagreement rather than orchestrated diversity.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import llm_call, Agent
from philosophical_traditions import (
    TRADITIONS,
    PhilosophicalTradition,
    get_maximally_incompatible_traditions
)

# Model pool for diversity
DEFAULT_MODELS = [
    "electronhub/claude-sonnet-4-5-20250929",
    "electronhub/gpt-5.1",
    "electronhub/gemini-2.5-flash"
]


def initialize_philosophical_agent(
    tradition: Optional[PhilosophicalTradition] = None,
    model: str = "electronhub/claude-sonnet-4-5-20250929",
    temperature: float = 0.95
) -> Dict[str, any]:
    """Phase 1: Initialize agent with independent commitments (passage-blind)

    Creates a 'philosophical person' with genuine commitments, NOT optimized
    for any particular passage.

    Args:
        tradition: Philosophical tradition to ground in, or None for wild card
        model: LLM model to use for generation
        temperature: High temp for genuine variety

    Returns:
        Agent profile dict with:
        - name: Agent's name
        - core_beliefs: Fundamental commitments
        - intellectual_lineage: Who influenced them
        - methodology: How they approach texts
        - blindspots: What they systematically miss
        - voice_style: How they argue
        - tradition_name: Name of tradition (if any)
        - model: Model that will be used for debate
    """

    system_prompt = """You are creating a philosophical agent with INDEPENDENT commitments.

CRITICAL INSTRUCTIONS:
1. You will NOT see the passage they'll debate. Don't optimize for any particular text.
2. Output MUST be valid JSON with the exact structure shown below
3. Be concise but substantive in each field
4. This should be a REAL philosophical personality, not a debate-generating device

Create a philosopher with:

1. CORE BELIEFS (2-3 sentences)
   - What do they believe about reality, knowledge, meaning?
   - What are their non-negotiable principles?

2. INTELLECTUAL LINEAGE (1-2 sentences)
   - Who influenced them? (specific thinkers)
   - What tradition(s) do they come from?

3. METHODOLOGY (1-2 sentences)
   - How do they approach texts?
   - What counts as a good argument for them?

4. BLINDSPOTS (2-3 brief items)
   - What do they systematically miss or dismiss?
   - What types of arguments don't move them?

5. VOICE/STYLE (1 sentence)
   - Are they careful or provocative?
   - How do they engage with disagreement?

OUTPUT FORMAT (strict JSON):
{
  "name": "A name reflecting core orientation (e.g., 'A Committed Naturalist', 'The Process Metaphysician')",
  "core_beliefs": "2-3 sentences on fundamental commitments",
  "intellectual_lineage": "Who influenced them, what tradition",
  "methodology": "How they read texts and evaluate arguments",
  "blindspots": ["What they miss", "What they dismiss", "What doesn't move them"],
  "voice_style": "How they sound when arguing"
}

OUTPUT ONLY THE JSON. NO MARKDOWN FORMATTING. NO EXPLANATORY TEXT."""

    if tradition:
        user_prompt = f"""Create a philosopher grounded in {tradition.name}.

Core commitments of this tradition:
{chr(10).join(f"- {c}" for c in tradition.core_commitments)}

Key figures: {", ".join(tradition.key_figures)}

Methodological principles:
{chr(10).join(f"- {m}" for m in tradition.methodological_principles)}

BUT: Make this a SPECIFIC person within that tradition, not a generic representative.
Give them individual quirks, emphases, and preoccupations.

OUTPUT ONLY VALID JSON:"""
    else:
        user_prompt = """Create a philosopher with independent commitments.

They can draw on any tradition(s) or be genuinely original.
Make them specific and distinctive.

OUTPUT ONLY VALID JSON:"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model=model
    )

    # Parse JSON
    try:
        # Clean response of any markdown or extra text
        response = response.strip()

        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        # Remove any text before first { or after last }
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            response = response[start:end+1]

        agent_profile = json.loads(response)

        # Add metadata
        agent_profile['tradition_name'] = tradition.name if tradition else "Independent"
        agent_profile['model'] = model

        return agent_profile

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response}")
        raise


def agent_encounters_passage(
    agent_profile: Dict[str, any],
    passage: str,
    temperature: float = 0.7
) -> Dict[str, any]:
    """Phase 2: Agent with pre-existing commitments encounters passage

    The agent interprets the passage FROM their pre-existing commitments,
    not optimized for interesting debate.

    Args:
        agent_profile: Profile from Phase 1
        passage: Text to interpret
        temperature: Medium temp for interpretation

    Returns:
        Enhanced profile with:
        - initial_reading: First interpretation of passage
        - focus_areas: What they'll emphasize
        - likely_disputes: Where they expect disagreement
    """

    system_prompt = f"""You are a philosophical agent with these pre-existing commitments:

Core beliefs: {agent_profile['core_beliefs']}
Intellectual lineage: {agent_profile['intellectual_lineage']}
Methodology: {agent_profile['methodology']}
Blindspots: {', '.join(agent_profile['blindspots'])}

You are encountering a passage for the FIRST TIME.

CRITICAL INSTRUCTIONS:
1. Interpret this passage FROM YOUR COMMITMENTS, not to create interesting debate
2. You may have a boring or forced reading - that's authentic
3. You may miss things others would find obvious - that's your blindspots
4. Output MUST be valid JSON with exact structure below

Given YOUR commitments, generate:
1. Your immediate interpretation (what this passage means to YOU)
2. What you'll focus on (what matters given your commitments)
3. What you'll likely dispute (what you expect others to get wrong)

OUTPUT FORMAT (strict JSON):
{{
  "initial_reading": "Your first take on what this passage means (2-3 sentences)",
  "focus_areas": "What you'll emphasize given your commitments (1-2 sentences)",
  "likely_disputes": "Where you expect to disagree with others (1-2 sentences)"
}}

OUTPUT ONLY THE JSON. NO MARKDOWN. NO EXTRA TEXT."""

    user_prompt = f"""Passage:

{passage}

What is your reading, from YOUR philosophical commitments?

OUTPUT ONLY VALID JSON:"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model=agent_profile['model']
    )

    # Parse JSON
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

        encounter_data = json.loads(response)

        # Merge with profile
        enhanced_profile = {**agent_profile, **encounter_data}

        return enhanced_profile

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response}")
        raise


def generate_agent_ensemble(
    passage: str,
    num_agents: int = 3,
    temperature: float = 0.95,
    verbose: bool = True,
    models: Optional[List[str]] = None
) -> List[Agent]:
    """Generate ensemble of agents using two-phase initialization

    Phase 1: Initialize agents with independent commitments (passage-blind)
    Phase 2: Agents encounter passage and form interpretations

    Args:
        passage: Text to debate (only used in Phase 2)
        num_agents: Number of agents to generate
        temperature: Sampling temperature for Phase 1
        verbose: Print progress
        models: List of models to use (cycles through them)

    Returns:
        List of Agent objects ready to debate
    """

    if models is None:
        models = DEFAULT_MODELS

    if verbose:
        print(f"\n{'='*80}")
        print(f"TWO-PHASE AGENT GENERATION ({num_agents} agents)")
        print(f"{'='*80}\n")

    # Phase 1: Initialize agents (passage-blind)
    if verbose:
        print("PHASE 1: Initializing philosophical agents (passage-blind)...")
        print()

    # Select maximally incompatible traditions
    traditions = get_maximally_incompatible_traditions(num_agents)

    agent_profiles = []
    for i, tradition in enumerate(traditions):
        # Cycle through models for diversity
        model = models[i % len(models)]

        if verbose:
            print(f"[{i+1}/{num_agents}] Generating agent from {tradition.name} using {model.split('/')[-1]}...")

        profile = initialize_philosophical_agent(
            tradition=tradition,
            model=model,
            temperature=temperature
        )

        agent_profiles.append(profile)

        if verbose:
            print(f"  ✓ {profile['name']}")
            print(f"    Beliefs: {profile['core_beliefs'][:100]}...")
            print()

    # Phase 2: Agents encounter passage
    if verbose:
        print("\n" + "="*80)
        print("PHASE 2: Agents encounter passage...")
        print("="*80 + "\n")
        print(f"Passage: {passage[:100]}...\n")

    agents = []
    for i, profile in enumerate(agent_profiles):
        if verbose:
            print(f"[{i+1}/{num_agents}] {profile['name']} encounters passage...")

        enhanced_profile = agent_encounters_passage(profile, passage, temperature=0.7)

        # Create Agent object
        agent = Agent(
            name=enhanced_profile['name'],
            stance=enhanced_profile['core_beliefs'],
            focus=enhanced_profile['focus_areas'],
            model=enhanced_profile['model']
        )

        # Store additional fields for rich system prompt
        agent.intellectual_lineage = enhanced_profile['intellectual_lineage']
        agent.methodology = enhanced_profile['methodology']
        agent.blindspots = enhanced_profile['blindspots']
        agent.voice_style = enhanced_profile['voice_style']
        agent.initial_reading = enhanced_profile['initial_reading']
        agent.likely_disputes = enhanced_profile.get('likely_disputes', '')
        agent.tradition_name = enhanced_profile['tradition_name']

        agents.append(agent)

        if verbose:
            print(f"  ✓ Reading: {enhanced_profile['initial_reading'][:80]}...")
            print()

    if verbose:
        print("\n" + "="*80)
        print(f"✅ Generated {num_agents} agents with independent commitments!")
        print("="*80 + "\n")

    return agents


if __name__ == "__main__":
    # Test with example passage
    test_passage = """the teeming chaos of willful being has knowable structure. humans, fully cast as limited animals, have a much maligned conception towards structure in the void, but we are not mistaken about the shape we feel in the dark. the facets at our fingers are partial images to blind men."""

    print("Testing two-phase agent generation...")
    agents = generate_agent_ensemble(
        test_passage,
        num_agents=3,
        verbose=True,
        models=DEFAULT_MODELS
    )

    print("\nGenerated Agents:")
    print("=" * 80)
    for i, agent in enumerate(agents, 1):
        print(f"\n{i}. {agent.name}")
        print(f"   Tradition: {agent.tradition_name}")
        print(f"   Model: {agent.model}")
        print(f"   Stance: {agent.stance[:100]}...")
        print(f"   Initial reading: {agent.initial_reading[:100]}...")

    print("\n✅ Two-phase agent generation test complete!")
