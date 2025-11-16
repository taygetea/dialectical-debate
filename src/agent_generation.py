#!/usr/bin/env python3
"""
Agent Generation

Dynamically generates debate agents tuned to specific passages.

Similar to observer generation, but creates debate participants
rather than question-askers.
"""

import sys
from pathlib import Path
from typing import List, Dict
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dialectic_poc import llm_call, Agent


def generate_first_agent(passage: str, temperature: float = 0.85) -> Dict[str, str]:
    """Generate the first debate agent for a passage

    High temperature for creative exploration
    """

    system_prompt = """You are a meta-analyst designing debate agents for philosophical analysis.

Your task: Generate ONE useful debate agent perspective for analyzing the given passage.

A good debate agent has:
- A clear INTERPRETIVE STANCE (how they read texts)
- A focused ANALYTICAL LENS (what they pay attention to)
- Consistency in their argumentative style

This agent will PARTICIPATE in debates, making arguments and responding to other perspectives.

Output in JSON format:
{
  "name": "The [Type] [Role]",
  "stance": "One-sentence core interpretive orientation that drives all arguments",
  "focus": "Specific aspects this agent emphasizes in debates"
}

Be creative. Think about what THIS passage needs."""

    user_prompt = f"""Passage to analyze:

{passage}

Generate one useful debate agent perspective (JSON only):"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Parse JSON
    try:
        # Extract JSON if wrapped in markdown
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        agent_data = json.loads(response)
        return agent_data
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response}")
        raise


def generate_contrasting_agent(
    passage: str,
    existing_agents: List[Dict[str, str]],
    temperature: float = 0.85
) -> Dict[str, str]:
    """Generate an agent maximally different from existing ones

    High temperature for creative divergence
    """

    existing_summary = "\n\n".join([
        f"**{a['name']}**\n- Stance: {a['stance']}\n- Focus: {a['focus']}"
        for a in existing_agents
    ])

    system_prompt = """You are a meta-analyst designing debate agents for philosophical analysis.

Your task: Generate ONE debate agent that is MAXIMALLY DIFFERENT from the existing agents, while still being relevant to the passage.

Maximize difference by:
- Choosing a completely different interpretive framework
- Focusing on aspects the others ignore
- Using a contrasting argumentative style
- Coming from a different intellectual tradition

Output in JSON format:
{
  "name": "The [Type] [Role]",
  "stance": "One-sentence core interpretive orientation that drives all arguments",
  "focus": "Specific aspects this agent emphasizes in debates"
}

Make it as orthogonal as possible to existing agents."""

    user_prompt = f"""Passage to analyze:

{passage}

Existing agents (BE MAXIMALLY DIFFERENT):

{existing_summary}

Generate a contrasting agent (JSON only):"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Parse JSON
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        agent_data = json.loads(response)
        return agent_data
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response}")
        raise


def generate_agent_ensemble(
    passage: str,
    num_agents: int = 3,
    temperature: float = 0.85,
    verbose: bool = True,
    default_model: str = "electronhub/claude-sonnet-4-5-20250929"
) -> List[Agent]:
    """Generate an ensemble of diverse debate agents tuned to passage

    Args:
        passage: Text to analyze
        num_agents: How many agents to generate (default 3)
        temperature: Sampling temperature for generation
        verbose: Print progress
        default_model: Default model to assign to all generated agents

    Returns:
        List of Agent objects
    """

    agent_data_list = []

    if verbose:
        print(f"\n{'='*80}")
        print(f"GENERATING {num_agents} DIVERSE DEBATE AGENTS")
        print(f"{'='*80}\n")
        print(f"Passage: {passage[:100]}...\n")

    # Generate first agent
    if verbose:
        print(f"[1/{num_agents}] Generating first agent...")

    first = generate_first_agent(passage, temperature)
    agent_data_list.append(first)

    if verbose:
        print(f"✓ Generated: {first['name']}")
        print(f"  Stance: {first['stance']}")
        print()

    # Generate remaining agents (maximally different)
    for i in range(2, num_agents + 1):
        if verbose:
            print(f"[{i}/{num_agents}] Generating contrasting agent...")

        contrasting = generate_contrasting_agent(passage, agent_data_list, temperature)
        agent_data_list.append(contrasting)

        if verbose:
            print(f"✓ Generated: {contrasting['name']}")
            print(f"  Stance: {contrasting['stance']}")
            print()

    # Convert to Agent objects
    agents = [
        Agent(
            name=data['name'],
            stance=data['stance'],
            focus=data['focus'],
            model=default_model
        )
        for data in agent_data_list
    ]

    if verbose:
        print(f"\n{'='*80}")
        print(f"✅ Generated {num_agents} diverse agents!")
        print(f"{'='*80}\n")

    return agents


if __name__ == "__main__":
    # Test with example passage
    test_passage = """the teeming chaos of willful being has knowable structure. humans, fully cast as limited animals, have a much maligned conception towards structure in the void, but we are not mistaken about the shape we feel in the dark. the facets at our fingers are partial images to blind men."""

    print("Testing agent generation...")
    agents = generate_agent_ensemble(test_passage, num_agents=3, verbose=True)

    print("\nGenerated Agents:")
    print("=" * 80)
    for i, agent in enumerate(agents, 1):
        print(f"\n{i}. {agent.name}")
        print(f"   Stance: {agent.stance}")
        print(f"   Focus: {agent.focus}")

    print("\n✅ Agent generation test complete!")
