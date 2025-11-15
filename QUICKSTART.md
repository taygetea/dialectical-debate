# Quick Start Guide

Get up and running with the Dialectical Debate System in 10 minutes.

## Installation

### 1. Install Dependencies

```bash
# Install simonw/llm CLI tool
pip install llm
```

### 2. Configure LLM Provider

```bash
# Set API key (using ElectronHub as example)
llm keys set electronhub
# Paste your API key when prompted

# Set default model
llm models default electronhub/claude-sonnet-4-5-20250929

# Test it works
echo "What is 2+2?" | llm
# Should output: 4
```

### 3. Clone/Extract Project

```bash
cd dialectical-debate
ls
# Should see: README.md  src/  docs/  examples/  tests/  data/
```

## Your First Debate

### Phase 0: Basic Debate

```bash
cd src
python dialectic_poc.py
```

**What happens:**
1. Three agents debate Zarathustra passage (3 rounds)
2. Generic observer identifies branch point
3. Branch debate on that question (2 rounds)
4. Synthesis and merge-back
5. Outputs to `dialectic_log_TIMESTAMP.md`

**Output:** ~20KB markdown file with full transcript, summaries, and insights

**Duration:** ~3-4 minutes

### Phase 2: Multi-Observer

```bash
python multi_observer_test.py
```

**What happens:**
1. Generates 5 diverse observers for Kafka's Metamorphosis
2. Runs one main debate
3. Each observer identifies a different branch
4. Creates comparison report

**Output:**
- `multi_observer_report_TIMESTAMP.md` - Comparison report
- `ensemble_TIMESTAMP.json` - Generated observers
- `branch_1.md` through `branch_5.md` - Individual branch debates

**Duration:** ~8-10 minutes

**Diversity achieved:** Typically 0.90-0.95 (very high)

## Understanding the Output

### Debate Log Structure

```markdown
# Dialectical Debate Log
Started: TIMESTAMP

## MAIN DEBATE
Passage: [your text]

### ROUND 1
**The Literalist** (Round 1):
_Summary: [one-line LLM summary]_

[Full response]

**The Symbolist** (Round 1):
_Summary: [one-line LLM summary]_

[Full response]

... (repeat for all agents)

### ROUND 2
... (repeat)

## PHASE SUMMARY
[2-3 sentence summary of what emerged]

## BRANCH POINT IDENTIFIED
Question: [identified branch question]

## BRANCH DEBATE
... (same structure as main debate)

## BRANCH SYNTHESIS
[What got resolved, what remains in tension]

## ENRICHED UNDERSTANDING (MERGE-BACK)
[How the branch changed understanding of original passage]

## SESSION COMPLETE
Duration: X seconds
```

### Observer Ensemble JSON

```json
{
  "perspectives": [
    {
      "name": "The X Observer",
      "bias": "Core orientation statement",
      "focus": "Specific angles explored",
      "blind_spots": ["Thing 1", "Thing 2", "Thing 3"]
    },
    ...
  ],
  "diversity_analysis": {
    "num_perspectives": 5,
    "avg_pairwise_distance": 0.928,
    "diversity_score": 0.928
  }
}
```

## Customization

### Use Your Own Passage

Edit `dialectic_poc.py` or `multi_observer_test.py`:

```python
# Change this line
passage = """Your text here."""
```

### Adjust Debate Length

```python
# In main():
main_transcript = run_debate(passage, agents,
    rounds=3,  # Change this (default: 3)
    logger=logger
)

branch_transcript = run_branch_debate(question, agents,
    rounds=2,  # Change this (default: 2)
    logger=logger
)
```

### Generate More/Fewer Observers

```python
# In multi_observer_test.py or phase2_observer_generation.py:
perspectives = generate_observer_ensemble(
    passage,
    num_perspectives=5,  # Change this (default: 5)
    temperature=0.85
)
```

### Change Temperature

Higher temperature = more creative/diverse, lower = more focused/consistent

```python
# Observer generation
perspectives = generate_observer_ensemble(
    passage,
    temperature=0.85  # Range: 0.0-1.0 (default: 0.85)
)

# Debate generation (in llm_call)
llm_call(system_prompt, user_prompt,
    temperature=0.7  # Default for debates
)
```

## Common Issues

### LLM Call Fails

```
Error calling llm: ...
```

**Fix:**
1. Check API key: `llm keys list`
2. Test model: `echo "test" | llm`
3. Check model name: `llm models list | grep electronhub`

### Empty Branch Questions

If branch questions come back empty, this means the model timed out or returned nothing.

**Fix:**
- Already using Sonnet fallback (Haiku had issues)
- Try increasing timeout (though unlikely to help)
- Check API status

### JSON Parse Errors

```
Failed to parse JSON: ...
```

**Fix:**
- Observer generation sometimes returns markdown-wrapped JSON
- Code already handles ````json` wrappers
- If it persists, check the raw response in error message

### ModuleNotFoundError

```
ModuleNotFoundError: No module named 'dialectic_poc'
```

**Fix:**
```bash
# Make sure you're in src/ directory
cd dialectical-debate/src
python multi_observer_test.py

# Or run from project root with PYTHONPATH
cd dialectical-debate
PYTHONPATH=src python src/multi_observer_test.py
```

## Next Steps

### Explore Examples

```bash
cd ../examples
ls
# multi_observer_report_*.md - Full multi-observer comparison
# comparison_*.md - Phase 1 generic vs. observer comparison
# ensemble_*.json - Auto-generated observer perspectives
```

### Read the Docs

1. **ARCHITECTURE.md** - Understand how everything fits together
2. **docs/PHASE_0_1_2_COMPLETE.md** - What's been built so far
3. **docs/PHASE_3_NEXT.md** - What to build next

### Start Phase 3

If you're ready to build the graph structure:

1. Read `docs/PHASE_3_NEXT.md`
2. Review `docs/phase3_implementation_plan.md`
3. Start with Week 1: Data structures

## Tips

### Faster Iteration

For development, reduce rounds:
```python
run_debate(passage, agents, rounds=2)  # Instead of 3
run_branch_debate(question, agents, rounds=1)  # Instead of 2
```

### Cost Management

Each debate costs approximately:
- Phase 0 (single passage): ~$0.10-0.20 with Sonnet
- Phase 2 (5 observers): ~$1.00-1.50 with Sonnet

To reduce costs:
- Use fewer rounds
- Use fewer observers
- Try Haiku (if it works for your use case)

### Batch Processing

To process multiple passages:

```python
passages = [
    "Passage 1...",
    "Passage 2...",
    "Passage 3..."
]

for i, passage in enumerate(passages):
    print(f"\nProcessing passage {i+1}/{len(passages)}...")
    # Run your debate code here
    # Logs will be timestamped separately
```

## Getting Help

1. Check `docs/DESIGN_DECISIONS.md` for rationale behind choices
2. Review example outputs in `examples/`
3. Read Phase 3 planning docs if continuing development

---

**Ready to start?** Run `python src/dialectic_poc.py` and explore the output!
