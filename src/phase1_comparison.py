#!/usr/bin/env python3
"""
Phase 1 Comparison: Generic vs Observer-Driven Branch Detection
Runs the same passage through both approaches and compares results
"""

from dialectic_poc import *
from datetime import datetime
import json

class BranchComparison:
    """Compare generic vs observer-driven branches"""

    def __init__(self, passage: str):
        self.passage = passage
        self.generic_question = None
        self.observer_question = None
        self.generic_branch_transcript = None
        self.observer_branch_transcript = None

    def measure_differentiation(self) -> Dict[str, any]:
        """How different are the two approaches?"""

        # Jaccard similarity of question words (lower = more different)
        generic_words = set(self.generic_question.lower().split())
        observer_words = set(self.observer_question.lower().split())

        overlap = len(generic_words & observer_words)
        total = len(generic_words | observer_words)
        similarity = overlap / total if total > 0 else 0

        # Novelty: does observer question introduce new concepts?
        passage_words = set(self.passage.lower().split())
        new_concepts_generic = generic_words - passage_words
        new_concepts_observer = observer_words - passage_words

        return {
            'question_similarity': round(similarity, 3),
            'question_differentiation': round(1 - similarity, 3),
            'new_concepts_generic': len(new_concepts_generic),
            'new_concepts_observer': len(new_concepts_observer),
            'introduces_more_novelty': len(new_concepts_observer) > len(new_concepts_generic)
        }

    def measure_depth(self) -> Dict[str, any]:
        """Which branch led to deeper exploration?"""

        # Proxy metrics for depth
        generic_turns = len(self.generic_branch_transcript)
        observer_turns = len(self.observer_branch_transcript)

        # Count unique substantive terms (words > 4 chars)
        def count_substantive_terms(transcript):
            text = " ".join(t.content for t in transcript)
            words = [w for w in text.split() if len(w) > 4]
            return len(set(words))

        generic_vocabulary_richness = count_substantive_terms(self.generic_branch_transcript)
        observer_vocabulary_richness = count_substantive_terms(self.observer_branch_transcript)

        return {
            'generic_turns': generic_turns,
            'observer_turns': observer_turns,
            'generic_vocabulary': generic_vocabulary_richness,
            'observer_vocabulary': observer_vocabulary_richness,
            'vocabulary_ratio': round(observer_vocabulary_richness / max(generic_vocabulary_richness, 1), 2)
        }

def run_comparison(passage: str, agents: List[Agent], observer: Observer):
    """Run both generic and observer-driven detection, compare results"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Run 1: Generic detection
    print("="*80)
    print("RUN 1: GENERIC BRANCH DETECTION")
    print("="*80)

    generic_logger = Logger(f"generic_{timestamp}.md")
    generic_main = run_debate(passage, agents, rounds=3, logger=generic_logger)
    generic_question = identify_branch_point(generic_main, passage, observer=None, logger=generic_logger)
    generic_branch = run_branch_debate(generic_question, agents, rounds=2, logger=generic_logger)
    generic_synthesis = synthesize_branch_resolution(generic_question, generic_branch, logger=generic_logger)
    generic_enriched = merge_branch_back(generic_main, generic_question, generic_synthesis, passage, logger=generic_logger)
    generic_logger.finalize()

    # Run 2: Observer-driven detection
    print("\n" + "="*80)
    print(f"RUN 2: OBSERVER-DRIVEN DETECTION ({observer.name})")
    print("="*80)

    observer_logger = Logger(f"observer_{timestamp}.md")
    observer_main = run_debate(passage, agents, rounds=3, logger=observer_logger)
    observer_question = identify_branch_point(observer_main, passage, observer=observer, logger=observer_logger)
    observer_branch = run_branch_debate(observer_question, agents, rounds=2, logger=observer_logger)
    observer_synthesis = synthesize_branch_resolution(observer_question, observer_branch, logger=observer_logger)
    observer_enriched = merge_branch_back(observer_main, observer_question, observer_synthesis, passage, logger=observer_logger)
    observer_logger.finalize()

    # Compare
    comparison = BranchComparison(passage)
    comparison.generic_question = generic_question
    comparison.observer_question = observer_question
    comparison.generic_branch_transcript = generic_branch
    comparison.observer_branch_transcript = observer_branch

    # Generate report
    report_file = f"comparison_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(f"""# Phase 1 Comparison Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Passage Under Analysis

{passage}

## Branch Questions

### Generic Detection
**Question:** {generic_question}

### Observer Detection: {observer.name}
**Bias:** {observer.bias}
**Question:** {observer_question}

## Differentiation Analysis

```json
{json.dumps(comparison.measure_differentiation(), indent=2)}
```

**Interpretation:**
- Jaccard similarity < 0.4 = substantively different questions ✓
- Jaccard similarity 0.4-0.6 = somewhat different
- Jaccard similarity > 0.6 = similar questions (observer may be reformulating)

## Depth Analysis

```json
{json.dumps(comparison.measure_depth(), indent=2)}
```

## Full Logs

- Generic run: `{generic_logger.output_file}`
- Observer run: `{observer_logger.output_file}`

## Manual Assessment Checklist

### 1. Traceability
Can you clearly see the observer's bias ("{observer.bias}") in the question?

- [ ] Yes, the question directly reflects the observer's bias
- [ ] Partially, some elements of the bias are present
- [ ] No, the question doesn't reflect the stated bias

**Notes:**


### 2. Surprise
Would generic detection have found this question?

- [ ] No, this is a genuinely different angle
- [ ] Maybe, it's related but distinct
- [ ] Yes, it's essentially a reformulation

**Notes:**


### 3. Productivity
Which branch debate generated more interesting insights?

- [ ] Observer branch was more interesting
- [ ] Generic branch was more interesting
- [ ] Both equally interesting
- [ ] Both equally uninteresting

**Notes:**


### 4. Integration
Which merge-back enrichment was more valuable?

**Generic enrichment excerpt:**
{generic_enriched[:200]}...

**Observer enrichment excerpt:**
{observer_enriched[:200]}...

- [ ] Observer enrichment added more value
- [ ] Generic enrichment added more value
- [ ] Both comparable

**Notes:**


## Conclusion

**Success Criteria Check (Phase 1):**
- [ ] Observer question is substantively different (Jaccard < 0.4)
- [ ] Observer question traces to stated bias (manual check)
- [ ] Technical functionality works without errors

**Recommendation:**
- [ ] Observer approach is promising, proceed with testing other personas
- [ ] Observer needs refinement (strengthen bias, adjust examples)
- [ ] Try different observer persona for this passage type
""")

    print(f"\n{'='*80}")
    print(f"COMPARISON COMPLETE")
    print(f"{'='*80}")
    print(f"\nComparison report: {report_file}")
    print(f"Generic log:       {generic_logger.output_file}")
    print(f"Observer log:      {observer_logger.output_file}")
    print(f"\nDifferentiation:   {comparison.measure_differentiation()['question_differentiation']}")
    print(f"(Target: > 0.6 for substantive difference)")

    return report_file

def main():
    """Run comparison with default passage and Phenomenologist observer"""

    passage = """When Zarathustra was thirty years old, he left his home and the lake of his home, and went into the mountains."""

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

    # Test with Phenomenologist observer (recommended)
    print(f"\nTesting with observer: {PHENOMENOLOGIST.name}")
    print(f"Bias: {PHENOMENOLOGIST.bias}\n")

    run_comparison(passage, agents, PHENOMENOLOGIST)

if __name__ == "__main__":
    main()
