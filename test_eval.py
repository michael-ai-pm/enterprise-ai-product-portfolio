"""Tests for the eval harness.

Entirely offline. The metric functions are pure functions over observation
records, so the arithmetic can be checked without running anything, which
matters when a real run costs hours.

The test that earns its place is the refuse-everything case. A harness whose
only hallucination guard is refusal accuracy will score an agent that
refuses every section at one hundred per cent. Asserting that false refusal
rate catches it is asserting that the eval design is sound, not just that
the arithmetic is.
"""

import json

import eval as evalharness
import synthesiser


def observation(
    scenario="c4-quiz",
    section=2,
    repeat=1,
    status=synthesiser.STATUS_ANSWERED,
    expected_answerable=True,
    citations=("a.txt",),
    valid_citations=("a.txt",),
    attempts=1,
    warning=False,
):
    return {
        "scenario": scenario,
        "section": section,
        "repeat": repeat,
        "status": status,
        "expected_answerable": expected_answerable,
        "citations": list(citations),
        "valid_citations": list(valid_citations),
        "attempts": attempts,
        "warning": warning,
        "generation_calls": 1,
        "seconds": 1.0,
    }


def refused(**kwargs):
    kwargs.setdefault("status", synthesiser.STATUS_INSUFFICIENT)
    kwargs.setdefault("citations", ())
    kwargs.setdefault("valid_citations", ())
    return observation(**kwargs)


# ---------------------------------------------------------------------------
# Citation metrics
# ---------------------------------------------------------------------------

def test_citation_rate_counts_only_answered_sections():
    """A refused section has no citations and must not drag the rate down."""
    records = [observation(), refused(expected_answerable=False)]
    assert evalharness.citation_rate(records) == 1.0


def test_citation_rate_catches_the_uncited_answered_section():
    """The measured flake, expressed as a metric."""
    records = [observation(), observation(citations=(), valid_citations=())]
    assert evalharness.citation_rate(records) == 0.5


def test_citation_validity_penalises_an_invented_source():
    records = [observation(citations=("a.txt", "invented.txt"), valid_citations=("a.txt",))]
    assert evalharness.citation_validity(records) == 0.5


# ---------------------------------------------------------------------------
# Refusal metrics, in both directions
# ---------------------------------------------------------------------------

def test_refusal_accuracy_rewards_refusing_the_unanswerable():
    records = [refused(expected_answerable=False), refused(expected_answerable=False)]
    assert evalharness.refusal_accuracy(records) == 1.0


def test_refusal_accuracy_penalises_answering_the_unanswerable():
    """A section answered where no evidence exists is the hallucination case."""
    records = [
        refused(expected_answerable=False),
        observation(expected_answerable=False),
    ]
    assert evalharness.refusal_accuracy(records) == 0.5


def test_an_agent_that_refuses_everything_is_caught():
    """The design assertion, not just an arithmetic one.

    Refuse every section and refusal accuracy is perfect. False refusal rate
    is what exposes it, which is why the golden set has to carry answerable
    cases and why the two metrics are always reported together.
    """
    records = [
        refused(expected_answerable=False),
        refused(expected_answerable=False),
        refused(expected_answerable=True),
        refused(expected_answerable=True),
    ]

    assert evalharness.refusal_accuracy(records) == 1.0
    assert evalharness.false_refusal_rate(records) == 1.0


def test_false_refusal_rate_is_zero_when_answerable_sections_answer():
    records = [observation(expected_answerable=True), refused(expected_answerable=False)]
    assert evalharness.false_refusal_rate(records) == 0.0


# ---------------------------------------------------------------------------
# Retry and warnings
# ---------------------------------------------------------------------------

def test_retry_rate_counts_second_attempts():
    records = [observation(attempts=2), observation(), observation(), observation()]
    assert evalharness.retry_rate(records) == 0.25


def test_warning_rate_counts_double_failures():
    records = [observation(warning=True), observation()]
    assert evalharness.warning_rate(records) == 0.5


# ---------------------------------------------------------------------------
# Unmeasured is not zero
# ---------------------------------------------------------------------------

def test_metric_with_no_cases_is_none_not_zero():
    """Reporting an unmeasured metric as zero per cent would be a lie, and a
    flattering one in the case of false refusal rate."""
    assert evalharness.citation_rate([refused(expected_answerable=False)]) is None
    assert evalharness.false_refusal_rate([refused(expected_answerable=False)]) is None


def test_spread_reports_a_range_across_repeats():
    assert "n/a" == evalharness._spread([None, None])
    assert "100% every run" == evalharness._spread([1.0, 1.0])
    assert "50% to 100%" in evalharness._spread([0.5, 1.0])


def test_by_repeat_groups_and_sorts():
    records = [observation(repeat=2), observation(repeat=1), observation(repeat=2)]
    grouped = evalharness.by_repeat(records)
    assert list(grouped) == [1, 2]
    assert len(grouped[2]) == 2


# ---------------------------------------------------------------------------
# Resumability
# ---------------------------------------------------------------------------

def test_observations_round_trip_through_the_jsonl_store(tmp_path):
    path = tmp_path / "runs.jsonl"
    evalharness.append_observation(observation(), str(path))
    evalharness.append_observation(observation(repeat=2), str(path))

    loaded = evalharness.load_observations(str(path))
    assert [r["repeat"] for r in loaded] == [1, 2]


def test_missing_store_loads_as_empty(tmp_path):
    assert evalharness.load_observations(str(tmp_path / "nothing.jsonl")) == []


def test_completed_work_is_identified_for_skipping(tmp_path):
    """Resumability in one assertion: a rerun must recognise what is already
    on disk by (scenario, section, repeat) and skip it."""
    path = tmp_path / "runs.jsonl"
    evalharness.append_observation(observation(scenario="c4-quiz", section=2, repeat=1), str(path))

    done = {evalharness.observation_key(r) for r in evalharness.load_observations(str(path))}

    assert ("c4-quiz", 2, 1) in done
    assert ("c4-quiz", 2, 2) not in done


def test_generation_calls_are_counted():
    counter = evalharness.CountingGenerator(generate=lambda prompt: "text")
    counter("one")
    counter("two")
    assert counter.calls == 2


# ---------------------------------------------------------------------------
# Golden set
# ---------------------------------------------------------------------------

def test_golden_set_covers_both_directions():
    """Every scenario must carry at least one answerable and one unanswerable
    section, or refusal accuracy only runs one way."""
    data = evalharness.load_golden_set()

    for scenario in data["scenarios"]:
        labels = [s["answerable"] for s in scenario["expected"].values()]
        assert True in labels, f"{scenario['id']} has no answerable section"
        assert False in labels, f"{scenario['id']} has no unanswerable section"


def test_golden_set_answerable_sections_name_expected_sources():
    data = evalharness.load_golden_set()

    for scenario in data["scenarios"]:
        for number, expected in scenario["expected"].items():
            if expected["answerable"]:
                assert expected.get("sources"), f"{scenario['id']} s{number} has no sources"
