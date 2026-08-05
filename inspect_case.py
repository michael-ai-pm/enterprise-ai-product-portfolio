"""Run one section and print the text, to inspect what the agent actually wrote.

The eval harness records citations, status and verdict, but not the section
text itself. That gap is why this exists: an answered section that should
have been refused cannot be judged from its metadata alone.

Defaults to c4-quiz section 5 (Format fit), one of seven observations where
the agent answered a section the golden set marks unanswerable, with three
valid citations and a passing review.

Usage:
    python inspect_case.py                  # c4-quiz section 5
    python inspect_case.py bbc-drama 5      # any scenario and section
"""

import json
import sys

import synthesiser


SCENARIO = sys.argv[1] if len(sys.argv) > 1 else "c4-quiz"
SECTION_NUMBER = int(sys.argv[2]) if len(sys.argv) > 2 else 5


def find_scenarios(golden):
    """The golden set may hold scenarios under a key or at the top level."""
    scenarios = golden.get("scenarios", golden)
    if isinstance(scenarios, dict):
        scenarios = list(scenarios.values())
    return [s for s in scenarios if isinstance(s, dict) and "plan" in s]


def main():
    with open("eval/golden_set.json", "r", encoding="utf-8") as f:
        golden = json.load(f)

    scenarios = find_scenarios(golden)

    scenario = None
    for candidate in scenarios:
        label = candidate.get("id") or candidate.get("name") or candidate.get("scenario")
        if label == SCENARIO:
            scenario = candidate
            break

    if scenario is None:
        print(f"Scenario '{SCENARIO}' not found. Available:")
        for candidate in scenarios:
            print("  ", candidate.get("id") or candidate.get("name") or candidate.get("scenario"))
        return

    plan = scenario["plan"]
    section = next(s for s in plan["sections"] if s["number"] == SECTION_NUMBER)

    print(f"Scenario:    {SCENARIO}")
    print(f"Section:     {SECTION_NUMBER}. {section['name']}")
    print("Sub-queries:")
    for sub_query in section["sub_queries"]:
        print(f"  - {sub_query}")
    print()
    print("Running synthesis, one generation call...")
    print()

    result = synthesiser.synthesise_section(section, plan)

    print("=" * 70)
    print(f"STATUS:    {result.get('status')}")
    print(f"REASON:    {result.get('reason')}")
    print(f"CITATIONS: {result.get('citations')}")
    print("=" * 70)
    print()
    print(result.get("text") or "(no text)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
