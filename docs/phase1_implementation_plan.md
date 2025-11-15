# Phase 1 Implementation Plan: Observer-Driven Branch Detection

**Date:** 2025-11-15
**Status:** Planning Document
**Goal:** Add ONE biased observer to identify non-obvious branch points in dialectical debates

---

## Executive Summary

Phase 0 successfully demonstrated branch-and-merge debate mechanics using 3 hard-coded agents (Literalist, Symbolist, Structuralist) with generic branch detection ("what's the most important unresolved question?"). Phase 1 will test whether a **biased observer** with a specific perspective can identify more interesting branch points than generic meta-analysis.

**Key Insight:** Observers need strong perspectives and biases, not neutrality. Instead of asking "what's unresolved?", we ask "from MY specific lens, what are they missing?"

---

## 1. Technical Changes Required

### 1.1 Model Selection Implementation

Currently, `dialectic_poc.py` uses a single model via `llm_call()`. We need to support different models for different roles.

**Current Implementation:**
```python
def llm_call(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    result = subprocess.run(
        ['llm', '-s', system_prompt, '-o', 'temperature', str(temperature)],
        input=user_prompt,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
```

**Phase 1 Enhancement:**
```python
def llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    model: str = "electronhub/claude-sonnet-4-5-20250929"  # Default to sonnet
) -> str:
    """Call llm with model selection"""
    result = subprocess.run(
        ['llm', '-m', model, '-s', system_prompt, '-o', 'temperature', str(temperature)],
        input=user_prompt,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
```

**Model Assignment Strategy:**
- **Debate agents** (Literalist, Symbolist, Structuralist): `electronhub/claude-sonnet-4-5-20250929`
- **Observer** (new): `electronhub/claude-haiku-4-5-20251001`
- **Summaries/Compression**: `electronhub/claude-haiku-4-5-20251001`

**Rationale:**
- Sonnet 4.5 provides deep philosophical reasoning for primary debate agents
- Haiku 4.5 is fast and cheap for meta-analysis tasks (observation, summarization)
- Keeps costs reasonable while maintaining quality where it matters

### 1.2 Observer Class Design

```python
class Observer:
    """Represents a biased perspective that identifies branch points"""

    def __init__(self, name: str, bias: str, focus: str, blind_spots: List[str] = None):
        self.name = name
        self.bias = bias  # What this observer ALWAYS looks for
        self.focus = focus  # Specific angle of vision
        self.blind_spots = blind_spots or []  # What they systematically miss

    def get_system_prompt(self) -> str:
        blind_spot_text = ""
        if self.blind_spots:
            blind_spot_text = f"\n\nYou tend to overlook: {', '.join(self.blind_spots)}"

        return f"""You are {self.name}, an observer of philosophical debates.

Your bias: {self.bias}
Your focus: {self.focus}{blind_spot_text}

Your job is NOT to be neutral. Your job is to identify what the debaters are missing FROM YOUR SPECIFIC PERSPECTIVE.

Look for:
- Questions that your bias makes obvious but others ignore
- Angles related to your focus that aren't being explored
- Tensions that only someone with your perspective would notice

Output ONLY a single precise question that deserves its own focused discussion. Make it specific and concrete."""

    def identify_branch(
        self,
        transcript: List[DebateTurn],
        passage: str,
        temperature: float = 0.5
    ) -> str:
        """Identify a branch point from this observer's biased perspective"""
        debate_text = "\n".join(str(t) for t in transcript)

        user_prompt = f"""Original passage:
"{passage}"

Debate transcript:
{debate_text}

From YOUR perspective ({self.bias}), what is the single most important question they're NOT asking?"""

        return llm_call(
            self.get_system_prompt(),
            user_prompt,
            temperature=temperature,
            model="electronhub/claude-haiku-4-5-20251001"  # Use Haiku for observers
        )
```

### 1.3 Integration Points in `dialectic_poc.py`

**Minimal Changes Needed:**

1. **Add model parameter to `llm_call()`** - see section 1.1
2. **Add Observer class** - see section 1.2
3. **Modify `identify_branch_point()`** to accept an optional observer:

```python
def identify_branch_point(
    transcript: List[DebateTurn],
    passage: str,
    observer: Optional[Observer] = None,
    logger: Optional[Logger] = None
) -> str:
    """Identify branch point - generic or observer-driven"""

    if observer:
        # Observer-driven branch detection
        branch_question = observer.identify_branch(transcript, passage)

        if logger:
            logger.log_section(f"BRANCH POINT IDENTIFIED (via {observer.name})")
            logger.log(f"Observer bias: {observer.bias}")
            logger.log(f"Question: {branch_question}\n")
    else:
        # Original generic detection (kept for comparison)
        debate_text = "\n".join(str(t) for t in transcript)
        system_prompt = """You are an observer of philosophical debates..."""
        # ... existing generic logic

    return branch_question
```

4. **Update `summarize_turn()` and `summarize_debate_phase()` to use Haiku:**

```python
def summarize_turn(self, agent_name: str, content: str) -> str:
    """Generate a one-line summary of an agent's turn"""
    # ... existing logic but add model parameter
    summary = llm_call(
        system_prompt,
        user_prompt,
        temperature=0.3,
        model="electronhub/claude-haiku-4-5-20251001"  # Use Haiku
    )
    return summary
```

---

## 2. Observer Design Specification

### 2.1 What Makes a Good Observer?

**A good observer has:**

1. **Strong, clear bias** - Not "I try to see all sides" but "I ALWAYS look for X"
2. **Specific domain expertise** - Deep knowledge in a particular area
3. **Predictable blind spots** - Acknowledging what they systematically miss makes the bias authentic
4. **Actionable focus** - Generates concrete, specific questions, not vague musings
5. **Complementary to debate agents** - Sees things the primary agents don't

**Anti-patterns to avoid:**
- "Balanced" or "neutral" observers (defeats the purpose)
- Vague focuses like "deeper meaning" (not actionable)
- Observers that duplicate what debate agents already do
- Meta-observers that just reformulate obvious questions

### 2.2 Suggested Observer Personas for Phase 1

#### Option A: The Materialist Historian
```python
Observer(
    name="The Materialist Historian",
    bias="Everything is shaped by material conditions and power structures",
    focus="Economic, political, and social contexts that produce texts and ideas",
    blind_spots=["Internal phenomenology", "Aesthetic considerations", "Logical validity independent of context"]
)
```

**Why this works:**
- Radically different lens from Literalist/Symbolist/Structuralist
- Will ask: "Who benefits from this interpretation? What material conditions made Nietzsche write this?"
- Forces grounding abstract philosophy in concrete historical context
- Clear, strong bias that generates novel questions

#### Option B: The Pragmatist Engineer
```python
Observer(
    name="The Pragmatist Engineer",
    bias="Ideas only matter insofar as they have practical consequences",
    focus="Actionable implications, implementability, real-world effects",
    blind_spots=["Pure theory", "Historical context", "Aesthetic beauty"]
)
```

**Why this works:**
- Asks "So what? What can you DO with this?"
- Will identify when debate gets lost in abstract hair-splitting
- Forces connection to lived experience and decision-making
- Generates questions about application and consequences

#### Option C: The Phenomenologist (RECOMMENDED)
```python
Observer(
    name="The Phenomenologist",
    bias="Only first-person lived experience is primary; everything else is derivative",
    focus="What this passage feels like from the inside, subjective states, qualia",
    blind_spots=["Objective structures", "Historical contexts", "Logical consistency"]
)
```

**Why this works best:**
- **Maximum orthogonality** to existing agents (Literalist focuses on facts, Symbolist on archetypes, Structuralist on patterns - none focus on first-person experience)
- Will ask questions like: "What is it like to BE Zarathustra at this moment? What phenomenal state corresponds to 'leaving home'?"
- Grounds abstract debate in embodied experience
- Most likely to identify truly novel branch points

### 2.3 Observer Prompt Engineering Approach

**Core Principles:**

1. **Make the bias explicit and strong** - "You ALWAYS interpret through lens X"
2. **Provide concrete examples** - "For instance, when others discuss 'meaning', you ask about 'felt sense'"
3. **Acknowledge blind spots** - Makes the observer more authentic and trustworthy
4. **Focus on generative questions** - "What question would only YOU ask?"
5. **Discourage reformulation** - "Don't ask what they're already arguing about in different words"

**Template Structure:**
```
You are [NAME], an observer with a specific perspective.

Your core bias: [ONE SENTENCE DESCRIBING FUNDAMENTAL ORIENTATION]
Your focus: [WHAT YOU ALWAYS LOOK FOR]
You systematically overlook: [BLIND SPOTS]

When observing debates, you identify gaps and tensions that ONLY SOMEONE WITH YOUR BIAS would notice.

Good questions from your perspective:
- [EXAMPLE 1]
- [EXAMPLE 2]

Bad questions (too generic or reformulations):
- [ANTI-EXAMPLE 1]
- [ANTI-EXAMPLE 2]

Output a single, concrete question that the debaters are missing from your angle.
```

### 2.4 Observer Output Format

**Desired output:** A single, well-formed question (one sentence)

**Examples of good observer outputs:**

From Phenomenologist:
> "What is the qualitative difference in Zarathustra's first-person experience between being beside the lake versus being in the mountains?"

From Materialist Historian:
> "What economic conditions in 1880s Basel enabled Nietzsche to have the leisure to philosophize about mountain solitude?"

From Pragmatist Engineer:
> "If someone actually tried to implement 'leaving home at thirty to seek mountains,' what concrete decision procedure would they use?"

**Examples of bad observer outputs (to avoid):**

Too generic:
> "What does this passage really mean?"

Reformulation of existing debate:
> "Is this literal or symbolic?" (Already being argued)

Too vague:
> "What are the deeper implications here?"

---

## 3. Comparison Strategy

### 3.1 How to Validate Observer-Found Branches

**Hypothesis:** Observer-driven branches should be:
1. **Non-obvious** - Not something generic meta-analysis would find
2. **Productive** - Generate interesting debate content
3. **Perspective-specific** - Clearly traceable to observer's bias

**Validation Approach:**

**Run each debate twice:**

1. **Control run:** Generic branch detection (existing Phase 0 method)
2. **Experimental run:** Observer-driven branch detection

**For each passage, compare:**
- What question did generic detection find?
- What question did observer find?
- Are they different?
- Which led to more interesting branch debate?

### 3.2 Metrics and Heuristics for Success

**Quantitative Metrics:**

```python
class BranchComparison:
    """Compare generic vs observer-driven branches"""

    def __init__(self, passage: str):
        self.passage = passage
        self.generic_question = None
        self.observer_question = None
        self.generic_branch_transcript = None
        self.observer_branch_transcript = None

    def measure_differentiation(self) -> Dict[str, Any]:
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
            'question_similarity': similarity,
            'question_differentiation': 1 - similarity,
            'new_concepts_generic': len(new_concepts_generic),
            'new_concepts_observer': len(new_concepts_observer),
            'introduces_more_novelty': len(new_concepts_observer) > len(new_concepts_generic)
        }

    def measure_depth(self) -> Dict[str, Any]:
        """Which branch led to deeper exploration?"""

        # Proxy metrics for depth
        generic_turns = len(self.generic_branch_transcript)
        observer_turns = len(self.observer_branch_transcript)

        # Count unique substantive terms (nouns, verbs > 4 chars)
        # This is crude but gives signal

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
            'vocabulary_ratio': observer_vocabulary_richness / max(generic_vocabulary_richness, 1)
        }
```

**Qualitative Heuristics:**

Manual evaluation questions:
1. **Traceability:** Can you clearly see the observer's bias in the question?
2. **Surprise:** Would you have thought of this question without the observer's lens?
3. **Productivity:** Did the branch debate generate insights the main debate missed?
4. **Integration:** Did merging the branch back actually enrich understanding?

**Success Criteria (in order of importance):**

1. **PRIMARY:** Observer question is substantively different from generic question (Jaccard < 0.4)
2. **SECONDARY:** Observer question traces clearly to stated bias (manual check)
3. **TERTIARY:** Observer branch leads to different insights than generic branch (manual comparison)
4. **ASPIRATIONAL:** Observer branch provides clearer enrichment when merged back

### 3.3 Comparison Output Format

```python
def generate_comparison_report(
    passage: str,
    generic_run: Dict[str, Any],
    observer_run: Dict[str, Any],
    comparison: BranchComparison,
    output_file: str
):
    """Generate markdown report comparing both approaches"""

    with open(output_file, 'w') as f:
        f.write(f"""# Branch Detection Comparison Report

## Passage
{passage}

## Branch Questions

### Generic Detection
{generic_run['branch_question']}

### Observer Detection ({observer_run['observer_name']})
Bias: {observer_run['observer_bias']}
Question: {observer_run['branch_question']}

## Differentiation Metrics

{json.dumps(comparison.measure_differentiation(), indent=2)}

## Qualitative Assessment

1. **Traceability:** [Does question reflect observer bias? Manual assessment]
2. **Surprise:** [Would generic method find this? Manual assessment]
3. **Productivity:** [Compare branch transcripts - manual assessment]

## Branch Debate Previews

### Generic Branch (first 500 chars)
{generic_run['branch_transcript'][:500]}...

### Observer Branch (first 500 chars)
{observer_run['branch_transcript'][:500]}...

## Conclusion

[Manual writeup of which approach worked better and why]
""")
```

---

## 4. Implementation Sequence

### Step 1: Add Model Selection (30 min)
**What:** Modify `llm_call()` to accept model parameter
**Test:** Run existing Phase 0 with explicit model="sonnet" - should work identically
**Files:** `dialectic_poc.py`
**Validation:** `python dialectic_poc.py` produces same quality output as before

### Step 2: Add Observer Class (45 min)
**What:** Implement Observer class with bias, focus, blind_spots
**Test:** Create Phenomenologist observer and call `identify_branch()` manually
**Files:** `dialectic_poc.py`
**Validation:** Observer generates a question that clearly reflects its bias

### Step 3: Update Summary Functions to Use Haiku (15 min)
**What:** Modify `summarize_turn()`, `summarize_debate_phase()` to use Haiku
**Test:** Compare quality of summaries (should be nearly as good, much faster)
**Files:** `dialectic_poc.py`
**Validation:** Summaries are coherent and capture essence

### Step 4: Integrate Observer into Main Flow (30 min)
**What:** Modify `identify_branch_point()` to optionally use observer
**Test:** Run main() with observer=Phenomenologist, ensure it works end-to-end
**Files:** `dialectic_poc.py`
**Validation:** Full debate runs with observer-identified branch point

### Step 5: Add Comparison Mode (60 min)
**What:** Create script that runs both generic and observer detection for same passage
**Test:** Run on Zarathustra passage, generate comparison report
**Files:** New file `phase1_comparison.py`
**Validation:** Produces markdown report with both approaches

### Step 6: Run Multiple Passages (variable)
**What:** Test observer on 3-5 different philosophical passages
**Test:** Generate comparison reports for each
**Files:** Multiple `comparison_*.md` output files
**Validation:** Observer consistently generates different questions than generic

### Step 7: Iterate on Observer Design (variable)
**What:** Based on comparison results, refine observer prompts/biases
**Test:** Re-run passages with refined observer
**Files:** `dialectic_poc.py` (observer definitions)
**Validation:** Refined observer generates more useful questions

**Total estimated time:** 3-4 hours for basic implementation + testing time

---

## 5. Risk Mitigation

### Risk 1: Observer Just Reformulates Obvious Questions

**Symptom:** Observer question has high Jaccard similarity (>0.6) to generic question
**Detection:** Automated via BranchComparison metrics
**Mitigation:**
- Strengthen bias in system prompt ("You ALWAYS interpret through...")
- Add explicit anti-examples ("Don't ask questions like...")
- Increase observer temperature (0.5 → 0.7) for more creative questions
- Try different observer persona with more orthogonal bias

**Fallback:** If observer consistently duplicates generic detection across multiple passages, this suggests the observer bias isn't strong/specific enough - return to design phase with different perspective

### Risk 2: Observer Bias Too Narrow/Unproductive

**Symptom:** Observer questions are traceable to bias but don't generate interesting debate
**Detection:** Manual review of branch debate quality
**Mitigation:**
- Ensure observer focus is concrete, not abstract
- Test observer on multiple passage types (narrative, argumentative, aphoristic)
- Widen blind spots to prevent over-constraint
- Add examples of "good questions from your perspective" to prompt

**Fallback:** Have 2-3 observer personas ready to test (Phenomenologist, Materialist Historian, Pragmatist) - if one doesn't work, try another

### Risk 3: Haiku Not Smart Enough for Observation

**Symptom:** Observer questions are generic, confused, or off-topic
**Detection:** Manual review of observer outputs
**Mitigation:**
- Provide more structured output format (JSON with fields)
- Give observer more examples in system prompt
- Reduce ambiguity in observer task definition
- Try temperature tuning (0.3-0.7 range)

**Fallback:** If Haiku consistently fails, try Sonnet for observer (sacrifices speed/cost but maintains quality) - this is acceptable for Phase 1 validation

### Risk 4: Branch Debates Too Short to Evaluate

**Symptom:** Both generic and observer branches only run 2 rounds, not enough signal
**Detection:** Manual review shows debates barely get started
**Mitigation:**
- Increase branch debate rounds (2 → 3 or 4)
- Add explicit instruction to agents to engage with branch question deeply
- Use higher temperature for branch debates to encourage exploration

**Fallback:** If short debates persist, this may indicate branch questions themselves are too narrow - need better question generation

### Risk 5: Can't Distinguish "Better" Branches

**Symptom:** Both branches seem equally interesting/uninteresting
**Detection:** Comparison reports show no clear winner
**Mitigation:**
- This is actually OK for Phase 1 - differentiation is success
- Focus on whether observer generates DIFFERENT questions (primary goal)
- Defer judgment about "better" to Phase 2 (multi-observer comparison)

**Fallback:** If truly can't differentiate quality, focus Phase 1 analysis on:
- Question differentiation metrics
- Traceability of observer bias
- Vocabulary/concept novelty

---

## Appendix A: Code Snippets

### Complete Observer Implementation

```python
from typing import List, Optional

class Observer:
    """Represents a biased perspective that identifies branch points"""

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
        transcript: List[DebateTurn],
        passage: str,
        temperature: float = 0.5
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
            model="electronhub/claude-haiku-4-5-20251001"
        )

# Example instantiation
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
```

### Comparison Script Template

```python
#!/usr/bin/env python3
"""
Phase 1 Comparison: Generic vs Observer-Driven Branch Detection
"""

from dialectic_poc import *
from datetime import datetime

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

{json.dumps(comparison.measure_differentiation(), indent=2)}

## Depth Analysis

{json.dumps(comparison.measure_depth(), indent=2)}

## Full Logs

- Generic run: `{generic_logger.output_file}`
- Observer run: `{observer_logger.output_file}`

## Manual Assessment

### Traceability
Can you clearly see the observer's bias ({observer.bias}) in the question?

[TODO: Manual assessment]

### Surprise
Would generic detection have found this question?

[TODO: Manual assessment]

### Productivity
Which branch debate generated more interesting insights?

[TODO: Manual assessment after reading both logs]

## Conclusion

[TODO: Which approach worked better for this passage and why?]
""")

    print(f"\nComparison report written to: {report_file}")
    return report_file

if __name__ == "__main__":
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

    # Test with Phenomenologist observer
    observer = PHENOMENOLOGIST

    run_comparison(passage, agents, observer)
```

---

## Appendix B: Example Expected Outputs

### Generic Branch Question (Phase 0 style)
> "Does the meaning of 'thirty years' and 'mountains' reside in the text's explicit content, in universal psychological symbols, or in literary-historical conventions—and can these three sources of meaning be definitively separated?"

**Analysis:** This is a meta-question about the debate itself. It reformulates the existing tension between the three agents' interpretive frameworks.

### Phenomenologist Branch Question (Expected Phase 1 style)
> "What is the qualitative difference in the first-person felt sense between being-beside-a-lake and being-in-mountains, and how does this phenomenological shift constitute the meaning of 'leaving' beyond any symbolic or structural reading?"

**Analysis:** This is NOT about the debate's structure but about a specific experiential dimension the agents weren't addressing. Only someone with phenomenological bias would ask this.

### Materialist Historian Branch Question (Alternative Phase 1)
> "What concrete economic and institutional privileges made it possible for a thirty-year-old male to 'leave home' for philosophical solitude in 19th century Europe, and how does recognizing this privilege change our interpretation of the text's implied universality?"

**Analysis:** Introduces political economy dimension completely absent from original debate. Traces directly to materialist bias.

---

## Success Definition for Phase 1

Phase 1 succeeds if:

1. **Observer implementation works technically** - Can run debates with observer-driven branch detection without errors
2. **Observer generates different questions** - Jaccard similarity < 0.4 between observer and generic questions across 3+ passages
3. **Difference is traceable to bias** - Manual review confirms observer questions reflect stated bias
4. **System produces clear comparison data** - Can generate reports comparing both approaches

Phase 1 provides learning for Phase 2 if:

- We understand which observer biases generate most interesting branches
- We have metrics/heuristics for evaluating branch quality
- We know whether observer approach is worth scaling (multiple observers, observer ensembles, etc.)

**Phase 1 does NOT need to prove observer branches are "better"** - it only needs to prove they are **different and traceable to specific perspectives**. Quality comparison can wait for Phase 2.
