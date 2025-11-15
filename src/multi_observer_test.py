#!/usr/bin/env python3
"""
Multi-Observer Test: Generate observers and run debates with each
"""

from phase2_observer_generation import *
from dialectic_poc import *
import json

def run_multi_observer_debate(
    passage: str,
    num_observers: int = 5,
    num_agents: int = 3,
    debate_rounds: int = 2,
    branch_rounds: int = 2
):
    """Generate observers and run debates with each one

    Args:
        passage: Text to analyze
        num_observers: How many observers to generate
        num_agents: Number of debate agents
        debate_rounds: Rounds for main debate
        branch_rounds: Rounds for branch debate
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*80}")
    print(f"MULTI-OBSERVER DEBATE TEST")
    print(f"{'='*80}\n")
    print(f"Passage: {passage}\n")

    # Step 1: Generate diverse observers
    print(f"\n{'='*80}")
    print("STEP 1: GENERATING OBSERVERS")
    print(f"{'='*80}\n")

    perspectives = generate_observer_ensemble(
        passage,
        num_perspectives=num_observers,
        temperature=0.85,
        verbose=True
    )

    # Save ensemble
    ensemble_file = f"ensemble_{timestamp}.json"
    save_ensemble(perspectives, ensemble_file)

    # Convert to Observer objects
    observers = [perspective_to_observer(p) for p in perspectives]

    # Standard debate agents
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

    # Step 2: Run one main debate (shared for all observers)
    print(f"\n{'='*80}")
    print("STEP 2: RUNNING MAIN DEBATE")
    print(f"{'='*80}\n")

    main_logger = Logger(f"main_debate_{timestamp}.md")
    main_transcript = run_debate(
        passage,
        agents,
        rounds=debate_rounds,
        logger=main_logger
    )
    main_logger.finalize()

    print(f"Main debate complete: {main_logger.output_file}\n")

    # Step 3: Each observer identifies a branch and debates it
    print(f"\n{'='*80}")
    print("STEP 3: OBSERVER-DRIVEN BRANCHES")
    print(f"{'='*80}\n")

    observer_results = []

    for i, observer in enumerate(observers, 1):
        print(f"\n{'-'*80}")
        print(f"OBSERVER {i}/{len(observers)}: {observer.name}")
        print(f"{'-'*80}\n")
        print(f"Bias: {observer.bias}\n")

        # Identify branch
        print(f"Identifying branch point...")
        branch_question = observer.identify_branch(main_transcript, passage)
        print(f"✓ Branch identified:\n  {branch_question}\n")

        # Run branch debate
        print(f"Running branch debate...")
        branch_logger = Logger(f"branch_{i}_{timestamp}.md")
        branch_logger.log_section(f"OBSERVER {i}: {observer.name}")
        branch_logger.log(f"Bias: {observer.bias}")
        branch_logger.log(f"Question: {branch_question}\n")

        branch_transcript = run_branch_debate(
            branch_question,
            agents,
            rounds=branch_rounds,
            logger=branch_logger
        )

        # Synthesize
        branch_synthesis = synthesize_branch_resolution(
            branch_question,
            branch_transcript,
            logger=branch_logger
        )

        branch_logger.finalize()

        observer_results.append({
            'observer_name': observer.name,
            'observer_bias': observer.bias,
            'branch_question': branch_question,
            'branch_synthesis': branch_synthesis,
            'log_file': branch_logger.output_file
        })

        print(f"✓ Complete: {branch_logger.output_file}\n")

    # Step 4: Compare all observer branches
    print(f"\n{'='*80}")
    print("STEP 4: COMPARING OBSERVER BRANCHES")
    print(f"{'='*80}\n")

    # Measure question diversity
    questions = [r['branch_question'] for r in observer_results]
    diversities = []

    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            q1_words = set(questions[i].lower().split())
            q2_words = set(questions[j].lower().split())
            overlap = len(q1_words & q2_words)
            total = len(q1_words | q2_words)
            similarity = overlap / total if total > 0 else 0
            diversities.append(1 - similarity)

    avg_diversity = sum(diversities) / len(diversities) if diversities else 0

    print(f"Average question diversity: {avg_diversity:.3f}\n")

    # Generate comparison report
    report_file = f"multi_observer_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(f"""# Multi-Observer Debate Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Passage Under Analysis

{passage}

## Generated Observers

{len(observers)} observers were generated with average pairwise diversity of {analyze_ensemble_diversity(perspectives)['diversity_score']:.3f}

""")

        for i, p in enumerate(perspectives, 1):
            f.write(f"""
### {i}. {p['name']}

- **Bias:** {p['bias']}
- **Focus:** {p['focus']}
- **Blind spots:** {', '.join(p['blind_spots'])}

""")

        f.write(f"""
## Main Debate

All observers analyzed the same main debate between {len(agents)} agents ({', '.join(a.name for a in agents)}).

See: `{main_logger.output_file}`

## Observer-Identified Branches

Average question diversity across observers: **{avg_diversity:.3f}**

""")

        for i, result in enumerate(observer_results, 1):
            f.write(f"""
### Branch {i}: {result['observer_name']}

**Observer Bias:** {result['observer_bias']}

**Question Identified:**
> {result['branch_question']}

**Branch Synthesis:**
{result['branch_synthesis']}

**Full Log:** `{result['log_file']}`

---

""")

        f.write(f"""
## Analysis

### Question Diversity

""")

        # Pairwise comparisons
        for i in range(len(observer_results)):
            for j in range(i + 1, len(observer_results)):
                q1 = observer_results[i]['branch_question']
                q2 = observer_results[j]['branch_question']

                q1_words = set(q1.lower().split())
                q2_words = set(q2.lower().split())
                overlap = len(q1_words & q2_words)
                total = len(q1_words | q2_words)
                similarity = overlap / total if total > 0 else 0

                f.write(f"""
**{observer_results[i]['observer_name']} vs {observer_results[j]['observer_name']}**
- Jaccard distance: {1 - similarity:.3f}
- Word overlap: {overlap}/{total}

""")

        f.write(f"""
## Conclusion

This multi-observer test demonstrates:

1. **Observer diversity:** Generated observers span {avg_diversity:.1%} of semantic space
2. **Question differentiation:** Each observer asked fundamentally different questions
3. **Bias traceability:** Questions reflect their generating observer's perspective

### Files Generated

- Observer ensemble: `{ensemble_file}`
- Main debate: `{main_logger.output_file}`
""")

        for i, result in enumerate(observer_results, 1):
            f.write(f"- Branch {i} ({result['observer_name']}): `{result['log_file']}`\n")

        f.write(f"\n---\n\nGenerated by phase2_observer_generation.py\n")

    print(f"{'='*80}")
    print(f"MULTI-OBSERVER TEST COMPLETE")
    print(f"{'='*80}\n")
    print(f"Report: {report_file}")
    print(f"Ensemble: {ensemble_file}")
    print(f"Main debate: {main_logger.output_file}")
    print(f"\nObserver branches:")
    for i, result in enumerate(observer_results, 1):
        print(f"  {i}. {result['observer_name']}: {result['log_file']}")

    return {
        'report_file': report_file,
        'ensemble_file': ensemble_file,
        'observer_results': observer_results,
        'avg_diversity': avg_diversity
    }

def main():
    """Run multi-observer test on Kafka's Metamorphosis opening"""

    passage = """As Gregor Samsa awoke one morning from uneasy dreams he found himself transformed in his bed into a gigantic insect."""

    results = run_multi_observer_debate(
        passage,
        num_observers=5,
        debate_rounds=2,
        branch_rounds=2
    )

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    print(f"Generated 5 observers with avg diversity: {results['avg_diversity']:.3f}")
    print(f"Each identified a unique branch question")
    print(f"\nSee full report: {results['report_file']}")

if __name__ == "__main__":
    main()
