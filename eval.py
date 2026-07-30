"""Offline eval harness. The artefact the rest of the portfolio argues for.

The strategy and architecture documents both claim eval-first discipline.
Until this file existed the repo argued for that discipline without
demonstrating it. This closes that gap.

Three design decisions, all forced by the constraint that a single
generation call on the free tier takes minutes.

One. Optimised for variance, not coverage. Three scenarios run five times
each says far more about the citation flake than ten scenarios run once, and
costs less than half. The flake was only visible in the first place because
one section happened to run twice.

Two. Resumable, because a twelve-hour unattended run that dies at hour seven
is a real risk at this speed rather than a theoretical one. Every section
observation is appended to a JSONL file and flushed immediately. A rerun
reads what is already on disk and skips it.

Three. Section evaluation is decoupled from full briefings. The plan is
generated once per scenario and committed into the golden set, then
individual sections are synthesised and reviewed against it repeatedly.

That third one deserves defending rather than asserting. The section is the
unit the contract actually applies to: one synthesis call per section, one
review per section, retries per section. So citation rate, citation
validity, refusal accuracy and retry rate are section-level properties and
measuring them per section is more honest than averaging them into a
briefing score.

What decoupling genuinely excludes is plan-stage variance. That is a real
limitation, it is stated in the summary output rather than buried here, and
it belongs to a planner eval that does not exist yet. The two metrics that
do need the whole loop, generation calls per briefing and end-to-end
latency, are measured by a separate full-loop mode that runs rarely, because
they are also the two that need the fewest repeats.

On latency and cost. This harness does NOT report either against the Gate 4
thresholds in the architecture document. Those thresholds stay framed as
targets. A single generation call on the free tier runs into minutes against
a ninety-second end-to-end P95 target, so a measurement here would be a
statement about the tier and not about the design. The numbers are recorded
as observations and labelled as such.

Usage:
    python eval.py --plans          generate and commit the cached plans
    python eval.py --run            run the section-level eval, resumable
    python eval.py --loop           run the full loop, for calls and latency
    python eval.py --summarise      write the committed results summary
"""

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone

import planner
import reviewer
import synthesiser


GOLDEN_SET_PATH = os.path.join("eval", "golden_set.json")
RESULTS_DIR = "results"
RUNS_PATH = os.path.join(RESULTS_DIR, "eval_runs.jsonl")
LOOP_PATH = os.path.join(RESULTS_DIR, "eval_loop.jsonl")
SUMMARY_PATH = os.path.join(RESULTS_DIR, "eval_summary.md")

DEFAULT_REPEATS = 5

# Sections the plan declares but that carry no retrieval work of their own.
SKIPPED_SECTIONS = {7}


# ---------------------------------------------------------------------------
# Golden set
# ---------------------------------------------------------------------------

def load_golden_set(path=GOLDEN_SET_PATH):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_golden_set(data, path=GOLDEN_SET_PATH):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def build_plans(path=GOLDEN_SET_PATH):
    """Generate one plan per scenario and write it into the golden set.

    Run once. The plans are committed so that every repeat is measured
    against the same plan and no run pays for the planner.
    """
    data = load_golden_set(path)

    for scenario in data["scenarios"]:
        if scenario.get("plan"):
            print(f"{scenario['id']}: plan already cached, skipping")
            continue

        print(f"{scenario['id']}: planning...")
        plan = planner.plan(
            format_name=scenario["format"],
            broadcaster=scenario["broadcaster"],
            territory=scenario["territory"],
        )
        problems = planner.validate_plan(plan)
        if problems:
            print(f"  plan INVALID, not cached: {problems}")
            continue

        scenario["plan"] = plan
        save_golden_set(data, path)
        print(f"  cached, {sum(len(s['sub_queries']) for s in plan['sections'])} sub-queries")

    return data


# ---------------------------------------------------------------------------
# Observation store, append-only and resumable
# ---------------------------------------------------------------------------

def observation_key(record):
    return (record["scenario"], record["section"], record["repeat"])


def load_observations(path=RUNS_PATH):
    if not os.path.exists(path):
        return []

    records = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_observation(record, path=RUNS_PATH):
    """Append and flush immediately. The flush is the whole point: an
    unattended run that is killed loses one section, not the run."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


class CountingGenerator:
    """Wraps the live generation call and counts it.

    Generation calls are the FinOps signal, and counting them at the point
    of the call is the only way to catch the calls the deterministic gates
    avoided making.
    """

    def __init__(self, generate=None):
        self._generate = generate or synthesiser._generate
        self.calls = 0

    def __call__(self, prompt):
        self.calls += 1
        return self._generate(prompt)


# ---------------------------------------------------------------------------
# The section-level run
# ---------------------------------------------------------------------------

def evaluate_section(scenario, plan_section, repeat):
    """Synthesise and review one section once, and return the observation."""
    plan = scenario["plan"]
    number = plan_section["number"]
    expected = scenario["expected"].get(str(number), {})

    counter = CountingGenerator()
    started = time.time()

    section = synthesiser.synthesise_section(plan_section, plan, generate=counter)
    section = reviewer.review_section(section, plan, plan_section, generate=counter)

    elapsed = time.time() - started
    review = section["review"]
    citations = section.get("citations", [])
    available = reviewer.kept_sources(section)

    return {
        "scenario": scenario["id"],
        "section": number,
        "section_name": plan_section["name"],
        "repeat": repeat,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": section["status"],
        "reason": section.get("reason"),
        "expected_answerable": expected.get("answerable"),
        "citations": citations,
        "valid_citations": [c for c in citations if c in available],
        "review_verdict": review["verdict"],
        "review_failures": review["failures"],
        "first_attempt_failures": review.get("first_attempt_failures", []),
        "attempts": review["attempts"],
        "warning": review["warning"],
        "generation_calls": counter.calls,
        "seconds": round(elapsed, 1),
    }


def run(repeats=DEFAULT_REPEATS, path=RUNS_PATH, golden_set_path=GOLDEN_SET_PATH):
    """Run the section-level eval, skipping anything already on disk."""
    data = load_golden_set(golden_set_path)
    done = {observation_key(record) for record in load_observations(path)}

    for repeat in range(1, repeats + 1):
        for scenario in data["scenarios"]:
            if not scenario.get("plan"):
                print(f"{scenario['id']}: no cached plan, run --plans first")
                continue

            for plan_section in scenario["plan"]["sections"]:
                number = plan_section["number"]
                if number in SKIPPED_SECTIONS or plan_section.get("derived"):
                    continue

                key = (scenario["id"], number, repeat)
                if key in done:
                    print(f"skip {key}, already recorded")
                    continue

                record = evaluate_section(scenario, plan_section, repeat)
                append_observation(record, path)
                print(
                    f"{scenario['id']} s{number} r{repeat}: "
                    f"{record['status']} calls={record['generation_calls']} "
                    f"cites={len(record['citations'])} "
                    f"attempts={record['attempts']} {record['seconds']}s"
                )


def run_loop(repeats=2, path=LOOP_PATH, golden_set_path=GOLDEN_SET_PATH):
    """Run the whole loop end to end, for the two metrics that need it.

    Generation calls per briefing and wall-clock latency cannot be measured
    section by section, because the point of both is what the full request
    does. These run rarely, which is affordable precisely because they need
    the fewest repeats.
    """
    data = load_golden_set(golden_set_path)
    done = {(r["scenario"], r["repeat"]) for r in load_observations(path)}

    for repeat in range(1, repeats + 1):
        for scenario in data["scenarios"]:
            if not scenario.get("plan") or (scenario["id"], repeat) in done:
                continue

            plan = scenario["plan"]
            counter = CountingGenerator()
            started = time.time()

            briefing = synthesiser.synthesise(plan, generate=counter)
            briefing = reviewer.review(briefing, plan, generate=counter)

            record = {
                "scenario": scenario["id"],
                "repeat": repeat,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "generation_calls": counter.calls,
                "seconds": round(time.time() - started, 1),
                "summary": briefing["review_summary"],
                # The planner call is excluded: the plan is cached. A live
                # request would add one call and its latency on top.
                "planner_call_excluded": True,
            }
            append_observation(record, path)
            print(f"{scenario['id']} r{repeat}: calls={record['generation_calls']} {record['seconds']}s")


# ---------------------------------------------------------------------------
# Metrics. Pure functions over observations, so the arithmetic is testable
# without running anything.
# ---------------------------------------------------------------------------

def _rate(numerator, denominator):
    """None rather than zero when there is nothing to divide by. A metric
    with no cases is unmeasured, and reporting it as zero would be a lie."""
    if not denominator:
        return None
    return numerator / denominator


def citation_rate(records):
    """Share of answered sections carrying at least one citation."""
    answered = [r for r in records if r["status"] == synthesiser.STATUS_ANSWERED]
    return _rate(sum(1 for r in answered if r["citations"]), len(answered))


def citation_validity(records):
    """Share of cited filenames that were actually in the section's evidence."""
    cited = sum(len(r["citations"]) for r in records)
    valid = sum(len(r["valid_citations"]) for r in records)
    return _rate(valid, cited)


def refusal_accuracy(records):
    """Correct refusals over the cases where refusal was the correct answer."""
    should_refuse = [r for r in records if r["expected_answerable"] is False]
    correct = sum(
        1 for r in should_refuse if r["status"] == synthesiser.STATUS_INSUFFICIENT
    )
    return _rate(correct, len(should_refuse))


def false_refusal_rate(records):
    """Sections refused where the evidence was in fact present.

    The counterweight to refusal accuracy. Without this a harness that
    refuses everything scores perfectly, which is the failure mode this
    metric exists to catch.
    """
    answerable = [r for r in records if r["expected_answerable"] is True]
    refused = sum(
        1 for r in answerable if r["status"] == synthesiser.STATUS_INSUFFICIENT
    )
    return _rate(refused, len(answerable))


def retry_rate(records):
    """Share of sections that needed a Reviewer retry."""
    return _rate(sum(1 for r in records if r["attempts"] > 1), len(records))


def warning_rate(records):
    """Share of sections that failed review twice and surfaced a warning."""
    return _rate(sum(1 for r in records if r["warning"]), len(records))


METRICS = {
    "Citation rate": citation_rate,
    "Citation validity": citation_validity,
    "Refusal accuracy": refusal_accuracy,
    "False refusal rate": false_refusal_rate,
    "Retry rate": retry_rate,
    "Quality warning rate": warning_rate,
}


def by_repeat(records):
    """Group observations by repeat, so spread across runs is visible.

    A single mean would hide exactly the thing the citation finding
    depended on. Variance is the finding, so variance is what gets shown.
    """
    grouped = {}
    for record in records:
        grouped.setdefault(record["repeat"], []).append(record)
    return dict(sorted(grouped.items()))


def _format_rate(value):
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _spread(values):
    """Range across repeats, and the standard deviation where it is defined."""
    present = [v for v in values if v is not None]
    if not present:
        return "n/a"
    if len(present) == 1:
        return _format_rate(present[0])

    low, high = min(present), max(present)
    if low == high:
        return f"{_format_rate(low)} every run"
    return (
        f"{_format_rate(low)} to {_format_rate(high)}, "
        f"sd {statistics.stdev(present) * 100:.0f}pp"
    )


def summarise(runs_path=RUNS_PATH, loop_path=LOOP_PATH, out_path=SUMMARY_PATH):
    records = load_observations(runs_path)
    loop_records = load_observations(loop_path)

    if not records:
        print("no observations recorded, run --run first")
        return

    grouped = by_repeat(records)
    lines = []

    lines.append("# Evaluation results")
    lines.append("")
    lines.append(
        f"Generated {datetime.now(timezone.utc).strftime('%d %B %Y')} from "
        f"`{runs_path}`. {len(records)} section observations across "
        f"{len(grouped)} repeats."
    )
    lines.append("")
    lines.append(
        "Every number here was produced on the OpenRouter free tier, which is a "
        "development path and not the production model. Treat the rates as "
        "measurements of this configuration, not of the design."
    )
    lines.append("")

    lines.append("## Metrics, overall and by repeat")
    lines.append("")
    # The per-run observation count is in the header on purpose. A run cut
    # short by a rate limit is still real data, but it must not read as
    # carrying the same weight as a complete one.
    header = (
        "| Metric | Overall | "
        + " | ".join(f"Run {r} (n={len(rows)})" for r, rows in grouped.items())
        + " | Spread |"
    )
    lines.append(header)
    lines.append("|" + "---|" * (len(grouped) + 3))

    for name, fn in METRICS.items():
        overall = _format_rate(fn(records))
        per_run = [fn(rows) for rows in grouped.values()]
        cells = " | ".join(_format_rate(v) for v in per_run)
        lines.append(f"| {name} | {overall} | {cells} | {_spread(per_run)} |")

    lines.append("")
    lines.append(
        "Spread is what this harness was built for. A single pass would have "
        "reported one number per metric and told you nothing about whether it "
        "holds. Three scenarios run repeatedly was chosen over ten scenarios run "
        "once for exactly that reason."
    )
    lines.append("")

    lines.append("## Where the failures actually are")
    lines.append("")
    lines.append(
        "The aggregate rates above hide the shape of the problem, which is the "
        "reason this breakdown exists. Failures are not spread evenly across "
        "sections, they are concentrated."
    )
    lines.append("")
    lines.append("| Scenario | Section | Expected answerable | Answered |")
    lines.append("|---|---|---|---|")

    per_section = {}
    for record in records:
        key = (record["scenario"], record["section"], record["section_name"])
        answered, total = per_section.get(key, (0, 0))
        per_section[key] = (
            answered + (record["status"] == synthesiser.STATUS_ANSWERED),
            total + 1,
        )

    for (scenario, number, name), (answered, total) in sorted(per_section.items()):
        expected = next(
            (
                r["expected_answerable"]
                for r in records
                if r["scenario"] == scenario and r["section"] == number
            ),
            None,
        )
        lines.append(
            f"| {scenario} | {number}. {name} | {expected} | {answered}/{total} |"
        )

    lines.append("")

    retried = [r for r in records if r["attempts"] > 1]
    if retried:
        lines.append("### What the Reviewer caught")
        lines.append("")
        for record in retried:
            lines.append(
                f"- `{record['scenario']}` section {record['section']}, repeat "
                f"{record['repeat']}: first attempt failed on "
                f"{', '.join(record['first_attempt_failures'])}, retry produced "
                f"`{record['status']}` with {len(record['citations'])} citation(s)."
            )
        lines.append("")

    lines.append("## Refusal accuracy runs in both directions")
    lines.append("")
    lines.append(
        "Refusal accuracy and false refusal rate are reported together on "
        "purpose. An agent that refuses every section scores one hundred per "
        "cent on the first and is useless. The golden set carries both "
        "answerable and unanswerable sections so that the second metric can "
        "catch that."
    )
    lines.append("")

    if loop_records:
        lines.append("## Full-loop observations")
        lines.append("")
        calls = [r["generation_calls"] for r in loop_records]
        seconds = [r["seconds"] for r in loop_records]
        lines.append(
            f"{len(loop_records)} end-to-end runs. Generation calls per briefing: "
            f"{min(calls)} to {max(calls)} against a six-section plan. "
            f"Wall clock: {min(seconds) / 60:.0f} to {max(seconds) / 60:.0f} minutes."
        )
        lines.append("")
        lines.append(
            "The call count is the number worth reading. A six-section plan does "
            "not cost six calls, because sections with no retrievable evidence "
            "are refused by a deterministic gate before any model call is made."
        )
        lines.append("")
        lines.append(
            "The wall clock is an observation about the free tier and is "
            "deliberately NOT reported against the ninety-second P95 target in "
            "section 10 of the architecture document. That target, and the cost "
            "per briefing target beside it, remain targets. Measuring them "
            "requires the production model, and doing so is the honest "
            "precondition for claiming either."
        )
        lines.append("")
        lines.append("The planner call is excluded, because the plans are cached.")
        lines.append("")

    lines.append("## What this harness does not measure")
    lines.append("")
    lines.append(
        "Plan quality. The plans are generated once and committed, so every "
        "repeat runs against the same plan and plan-stage variance is excluded "
        "by construction. That is a deliberate trade for repeat observations "
        "within the time available, and it means a planning regression would "
        "not show up here. A planner eval is a separate instrument and it does "
        "not exist yet."
    )
    lines.append("")
    lines.append(
        "Claim support. The Reviewer's tier-two check, whether a cited source "
        "actually backs the claim, is off in these runs because it would break "
        "the twelve-call cap in section 7. Citation validity here confirms that "
        "a cited file was among the retrieved evidence, which is a weaker claim "
        "than the source supporting the sentence."
    )
    lines.append("")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    print("\n".join(lines))
    print(f"\nwritten to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Offline eval harness")
    parser.add_argument("--plans", action="store_true", help="cache one plan per scenario")
    parser.add_argument("--run", action="store_true", help="run the section-level eval")
    parser.add_argument("--loop", action="store_true", help="run the full loop")
    parser.add_argument("--summarise", action="store_true", help="write the results summary")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    args = parser.parse_args()

    if args.plans:
        build_plans()
    if args.run:
        run(repeats=args.repeats)
    if args.loop:
        run_loop(repeats=2)
    if args.summarise:
        summarise()

    if not any([args.plans, args.run, args.loop, args.summarise]):
        parser.print_help()


if __name__ == "__main__":
    main()
