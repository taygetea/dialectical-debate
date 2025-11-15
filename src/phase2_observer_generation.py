#!/usr/bin/env python3
"""
Phase 2: Automated Observer Generation
Iteratively generate diverse perspectives for a passage
"""

from dialectic_poc import *
from typing import List, Dict
import json

def generate_first_perspective(passage: str, temperature: float = 0.8) -> Dict[str, str]:
    """Generate the first observer perspective for a passage

    High temperature for creative exploration
    """

    system_prompt = """You are a meta-observer designing perspectives for analyzing philosophical texts.

Your task: Generate ONE useful interpretive perspective for analyzing the given passage.

A good perspective has:
- A clear, specific BIAS (what it always looks for)
- A focused DOMAIN (its area of expertise)
- Acknowledged BLIND SPOTS (what it systematically misses)

Output your perspective in JSON format:
{
  "name": "The [Type] [Role]",
  "bias": "One-sentence core orientation that drives all interpretation",
  "focus": "Specific angles and questions this perspective explores",
  "blind_spots": ["Thing 1 it misses", "Thing 2 it misses", "Thing 3 it misses"]
}

Be creative and specific. Avoid generic perspectives like "balanced reader" or "context-aware analyst"."""

    user_prompt = f"""Passage to analyze:
"{passage}"

Generate ONE useful interpretive perspective for this passage.

JSON:"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Parse JSON response
    try:
        # Try to extract JSON if wrapped in markdown
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        perspective = json.loads(json_str)
        return perspective
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Response: {response}")
        raise

def generate_contrasting_perspective(
    passage: str,
    existing_perspectives: List[Dict[str, str]],
    temperature: float = 0.8
) -> Dict[str, str]:
    """Generate a perspective maximally different from existing ones

    High temperature for creative divergence
    """

    existing_summary = "\n\n".join([
        f"**{p['name']}**\n- Bias: {p['bias']}\n- Focus: {p['focus']}\n- Blind spots: {', '.join(p['blind_spots'])}"
        for p in existing_perspectives
    ])

    system_prompt = """You are a meta-observer designing perspectives for analyzing philosophical texts.

Your task: Generate ONE useful interpretive perspective that is MAXIMALLY DIFFERENT from the existing perspectives, while still being relevant to the passage.

Maximize difference by:
- Choosing a completely different domain/discipline
- Focusing on aspects the existing perspectives ignore
- Having opposite methodological commitments
- Asking questions that would never occur to existing perspectives

A good perspective has:
- A clear, specific BIAS (what it always looks for)
- A focused DOMAIN (its area of expertise)
- Acknowledged BLIND SPOTS (what it systematically misses)

Output your perspective in JSON format:
{
  "name": "The [Type] [Role]",
  "bias": "One-sentence core orientation that drives all interpretation",
  "focus": "Specific angles and questions this perspective explores",
  "blind_spots": ["Thing 1 it misses", "Thing 2 it misses", "Thing 3 it misses"]
}

Be creative and specific. Aim for maximum orthogonality to existing perspectives."""

    user_prompt = f"""Passage to analyze:
"{passage}"

EXISTING PERSPECTIVES (generate something maximally different):
{existing_summary}

Generate ONE new perspective that explores angles the existing perspectives completely miss.

JSON:"""

    response = llm_call(
        system_prompt,
        user_prompt,
        temperature=temperature,
        model="electronhub/claude-sonnet-4-5-20250929"
    )

    # Parse JSON response
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        perspective = json.loads(json_str)
        return perspective
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Response: {response}")
        raise

def measure_perspective_diversity(p1: Dict[str, str], p2: Dict[str, str]) -> Dict[str, float]:
    """Measure how different two perspectives are

    Returns metrics for semantic distance
    """

    # Jaccard similarity on key terms
    def get_words(text: str) -> set:
        return set(text.lower().split())

    p1_words = get_words(p1['bias'] + " " + p1['focus'])
    p2_words = get_words(p2['bias'] + " " + p2['focus'])

    overlap = len(p1_words & p2_words)
    total = len(p1_words | p2_words)
    jaccard_sim = overlap / total if total > 0 else 0

    return {
        'jaccard_similarity': round(jaccard_sim, 3),
        'jaccard_distance': round(1 - jaccard_sim, 3),
        'word_overlap': overlap,
        'unique_to_p1': len(p1_words - p2_words),
        'unique_to_p2': len(p2_words - p1_words)
    }

def generate_observer_ensemble(
    passage: str,
    num_perspectives: int = 5,
    temperature: float = 0.8,
    verbose: bool = True
) -> List[Dict[str, str]]:
    """Generate an ensemble of diverse observer perspectives

    Args:
        passage: Text to analyze
        num_perspectives: How many perspectives to generate
        temperature: Sampling temperature for generation
        verbose: Print progress

    Returns:
        List of perspective dictionaries
    """

    perspectives = []

    if verbose:
        print(f"\n{'='*80}")
        print(f"GENERATING {num_perspectives} DIVERSE OBSERVER PERSPECTIVES")
        print(f"{'='*80}\n")
        print(f"Passage: {passage}\n")

    # Generate first perspective
    if verbose:
        print(f"[1/{num_perspectives}] Generating first perspective...")

    first = generate_first_perspective(passage, temperature)
    perspectives.append(first)

    if verbose:
        print(f"✓ Generated: {first['name']}")
        print(f"  Bias: {first['bias']}")
        print()

    # Generate remaining perspectives with maximum differentiation
    for i in range(2, num_perspectives + 1):
        if verbose:
            print(f"[{i}/{num_perspectives}] Generating perspective maximally different from existing {len(perspectives)}...")

        new_perspective = generate_contrasting_perspective(passage, perspectives, temperature)
        perspectives.append(new_perspective)

        if verbose:
            print(f"✓ Generated: {new_perspective['name']}")
            print(f"  Bias: {new_perspective['bias']}")

            # Measure diversity from previous perspectives
            avg_distance = sum(
                measure_perspective_diversity(new_perspective, p)['jaccard_distance']
                for p in perspectives[:-1]
            ) / len(perspectives[:-1])

            print(f"  Avg distance from existing: {avg_distance:.2f}")
            print()

    if verbose:
        print(f"{'='*80}")
        print(f"GENERATED {len(perspectives)} PERSPECTIVES")
        print(f"{'='*80}\n")

    return perspectives

def perspective_to_observer(perspective: Dict[str, str]) -> Observer:
    """Convert a generated perspective dict to an Observer object

    This "locks in" the perspective at low temperature for execution
    """

    return Observer(
        name=perspective['name'],
        bias=perspective['bias'],
        focus=perspective['focus'],
        blind_spots=perspective.get('blind_spots', [])
    )

def analyze_ensemble_diversity(perspectives: List[Dict[str, str]]) -> Dict:
    """Analyze overall diversity of a perspective ensemble"""

    n = len(perspectives)
    all_distances = []

    # Pairwise diversity
    for i in range(n):
        for j in range(i + 1, n):
            dist = measure_perspective_diversity(perspectives[i], perspectives[j])
            all_distances.append(dist['jaccard_distance'])

    if all_distances:
        avg_distance = sum(all_distances) / len(all_distances)
        min_distance = min(all_distances)
        max_distance = max(all_distances)
    else:
        avg_distance = min_distance = max_distance = 0

    return {
        'num_perspectives': n,
        'avg_pairwise_distance': round(avg_distance, 3),
        'min_pairwise_distance': round(min_distance, 3),
        'max_pairwise_distance': round(max_distance, 3),
        'diversity_score': round(avg_distance, 3)  # Simple metric: avg distance
    }

def save_ensemble(perspectives: List[Dict[str, str]], output_file: str):
    """Save generated perspectives to a JSON file"""

    with open(output_file, 'w') as f:
        json.dump({
            'perspectives': perspectives,
            'diversity_analysis': analyze_ensemble_diversity(perspectives),
            'generated_at': datetime.now().isoformat()
        }, f, indent=2)

    print(f"Saved ensemble to: {output_file}")

def main():
    """Generate and test an observer ensemble"""

    passage = """When Zarathustra was thirty years old, he left his home and the lake of his home, and went into the mountains."""

    # Generate ensemble
    perspectives = generate_observer_ensemble(
        passage,
        num_perspectives=5,
        temperature=0.85,  # Higher temp for more creative divergence
        verbose=True
    )

    # Analyze diversity
    diversity = analyze_ensemble_diversity(perspectives)
    print("\nDIVERSITY ANALYSIS:")
    print(json.dumps(diversity, indent=2))

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"observer_ensemble_{timestamp}.json"
    save_ensemble(perspectives, output_file)

    # Display all perspectives
    print(f"\n{'='*80}")
    print("GENERATED OBSERVER PERSPECTIVES")
    print(f"{'='*80}\n")

    for i, p in enumerate(perspectives, 1):
        print(f"{i}. {p['name']}")
        print(f"   Bias: {p['bias']}")
        print(f"   Focus: {p['focus']}")
        print(f"   Blind spots: {', '.join(p['blind_spots'])}")
        print()

    # Test: Convert first perspective to Observer and use it
    print(f"\n{'='*80}")
    print("TESTING FIRST GENERATED OBSERVER")
    print(f"{'='*80}\n")

    test_observer = perspective_to_observer(perspectives[0])

    # Create agents
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

    # Run a quick debate
    logger = Logger(f"test_generated_observer_{timestamp}.md")
    main_transcript = run_debate(passage, agents, rounds=2, logger=logger)

    # Test observer's branch detection
    branch_question = test_observer.identify_branch(main_transcript, passage)

    print(f"Generated observer ({test_observer.name}) identified this branch:")
    print(f"\n{branch_question}\n")

    logger.log_section(f"TEST: Generated Observer Branch Detection")
    logger.log(f"Observer: {test_observer.name}")
    logger.log(f"Bias: {test_observer.bias}")
    logger.log(f"Question: {branch_question}")
    logger.finalize()

    print(f"Full test log: {logger.output_file}")

if __name__ == "__main__":
    main()
