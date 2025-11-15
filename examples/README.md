# Example Outputs

This directory contains sample outputs from Phases 0, 1, and 2.

## Multi-Observer Report

**File:** `multi_observer_report_20251115_092509.md`

**What it shows:**
- Kafka's Metamorphosis opening passage
- 5 auto-generated observers (Bureaucratic Logistics Analyst, Somatic Memory Archaeologist, etc.)
- Each observer's unique branch question
- Diversity metrics (89.5% average differentiation)
- Full synthesis of each branch debate

**Key result:** Demonstrates that automated observer generation produces genuinely diverse perspectives.

## Phase 1 Comparison

**File:** `comparison_20251115_090325.md`

**What it shows:**
- Nietzsche's Zarathustra passage
- Generic branch detection vs. Phenomenologist observer
- Question differentiation: 0.95
- Both branch debates and enriched understandings

**Key result:** Proves that biased observers ask structurally different questions than generic detection.

## Observer Ensemble

**File:** `ensemble_20251115_092509.json`

**What it shows:**
- JSON export of 5 generated observers for Kafka passage
- Each observer's name, bias, focus, and blind spots
- Diversity analysis (0.928 avg pairwise distance)
- Metadata (generation timestamp)

**Key result:** Example of the data structure for observer ensembles.

## Usage

These files serve as:
1. **Validation examples** - Compare your output to these
2. **Documentation** - Show what the system produces
3. **Test fixtures** - Use for regression testing

## Generating Your Own

```bash
# Phase 0: Basic debate
cd ../src
python dialectic_poc.py
# Output: dialectic_log_TIMESTAMP.md

# Phase 1: Comparison
python phase1_comparison.py
# Output: comparison_TIMESTAMP.md, generic_TIMESTAMP.md, observer_TIMESTAMP.md

# Phase 2: Multi-observer
python multi_observer_test.py
# Output: multi_observer_report_TIMESTAMP.md, ensemble_TIMESTAMP.json, branch_*.md
```
