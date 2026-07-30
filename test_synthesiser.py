"""Tests for the Synthesiser stage.

Most of these run offline against fake hits, with the generation function
injected. That is deliberate. The behaviour that matters most here, refusing
a section with no evidence, has to be provable without a live call, because
a gate that only works when the model cooperates is not a gate.

The last test is live. It runs a real plan through real retrieval and real
synthesis against the 20-document corpus, and asserts the split the corpus
actually supports: broadcaster slate and competing formats answer, and at
least one of the four sections with nothing behind them refuses.
"""

import pytest

import query
import synthesiser


class FakeHit:
    """Minimal stand-in for a Qdrant point, with the payload keys the
    Synthesiser and build_context read."""

    def __init__(self, id, source, text):
        self.id = id
        self.payload = {"source": source, "text": text}


def fake_retrieve(scored_by_query):
    """Build a query.retrieve replacement returning fixed (hit, score) pairs."""

    def _retrieve(question, k=3, candidate_k=10, with_scores=False):
        results = scored_by_query.get(question, [])
        if with_scores:
            return results
        return [hit for hit, score in results]

    return _retrieve


def never_called(_prompt):
    raise AssertionError("generation was called when it should not have been")


PLAN_STUB = {
    "format": "The Golden Elevators",
    "broadcaster": "Channel 4",
    "territory": "United Kingdom",
}


# ---------------------------------------------------------------------------
# Gate one: the deterministic evidence floor
# ---------------------------------------------------------------------------

def test_gather_evidence_drops_hits_below_threshold(monkeypatch):
    """A chunk scoring below the floor is considered but not kept."""
    strong = FakeHit(1, "a.txt", "strong match")
    weak = FakeHit(2, "b.txt", "weak match")
    monkeypatch.setattr(
        query, "retrieve", fake_retrieve({"q": [(strong, 4.2), (weak, -6.1)]})
    )

    kept, considered = gather(["q"])

    assert [hit.id for hit, score in kept] == [1]
    assert len(considered) == 2


def test_gather_evidence_deduplicates_across_sub_queries(monkeypatch):
    """The same chunk found by two sub-queries appears once, at its best score."""
    hit = FakeHit(1, "a.txt", "text")
    monkeypatch.setattr(
        query,
        "retrieve",
        fake_retrieve({"q1": [(hit, 1.0)], "q2": [(hit, 5.0)]}),
    )

    kept, considered = gather(["q1", "q2"])

    assert len(kept) == 1
    assert kept[0][1] == 5.0


def test_section_with_no_evidence_refuses_without_generating(monkeypatch):
    """The whole point. No evidence means insufficient_sources, and no LLM call."""
    weak = FakeHit(1, "a.txt", "unrelated")
    monkeypatch.setattr(query, "retrieve", fake_retrieve({"q": [(weak, -8.0)]}))

    section = {"number": 1, "name": "Territory snapshot", "sub_queries": ["q"]}
    result = synthesiser.synthesise_section(section, PLAN_STUB, generate=never_called)

    assert result["status"] == synthesiser.STATUS_INSUFFICIENT
    assert result["reason"] == synthesiser.REASON_NO_EVIDENCE
    assert result["text"] == ""


def test_refused_section_still_records_what_it_rejected(monkeypatch):
    """A refusal carries its rejected candidates, so eval can tell a retrieval
    miss apart from an empty index."""
    weak = FakeHit(1, "a.txt", "unrelated")
    monkeypatch.setattr(query, "retrieve", fake_retrieve({"q": [(weak, -8.0)]}))

    section = {"number": 1, "name": "Territory snapshot", "sub_queries": ["q"]}
    result = synthesiser.synthesise_section(section, PLAN_STUB, generate=never_called)

    assert result["sources_considered"] == [
        {"source": "a.txt", "score": -8.0, "kept": False}
    ]


# ---------------------------------------------------------------------------
# Gate two: the model's own refusal
# ---------------------------------------------------------------------------

def test_model_refusal_token_becomes_status_not_text(monkeypatch):
    """The sentinel must never leak into the briefing prose."""
    hit = FakeHit(1, "a.txt", "text")
    monkeypatch.setattr(query, "retrieve", fake_retrieve({"q": [(hit, 3.0)]}))

    section = {"number": 4, "name": "Trend signals", "sub_queries": ["q"]}
    result = synthesiser.synthesise_section(
        section, PLAN_STUB, generate=lambda prompt: "INSUFFICIENT_SOURCES"
    )

    assert result["status"] == synthesiser.STATUS_INSUFFICIENT
    assert result["reason"] == synthesiser.REASON_MODEL_DECLINED
    assert synthesiser.INSUFFICIENT_TOKEN not in result["text"]


@pytest.mark.parametrize(
    "raw", ["INSUFFICIENT_SOURCES", " INSUFFICIENT_SOURCES ", "INSUFFICIENT_SOURCES."]
)
def test_is_refusal_tolerates_punctuation(raw):
    """A model that adds a full stop has still refused."""
    assert synthesiser.is_refusal(raw)


def test_is_refusal_does_not_fire_on_prose_mentioning_the_token():
    """A section that merely discusses insufficient sources is still a section."""
    assert not synthesiser.is_refusal(
        "The sources are thin but INSUFFICIENT_SOURCES would overstate it."
    )


# ---------------------------------------------------------------------------
# Answered sections and citations
# ---------------------------------------------------------------------------

def test_answered_section_extracts_citations(monkeypatch):
    hit = FakeHit(1, "a.txt", "text")
    monkeypatch.setattr(query, "retrieve", fake_retrieve({"q": [(hit, 3.0)]}))

    section = {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]}
    result = synthesiser.synthesise_section(
        section,
        PLAN_STUB,
        generate=lambda prompt: "It commissioned a quiz [source: a.txt].",
    )

    assert result["status"] == synthesiser.STATUS_ANSWERED
    assert result["citations"] == ["a.txt"]


def test_extract_citations_deduplicates_and_keeps_order():
    text = "One [source: b.txt]. Two [source: a.txt]. Three [source: b.txt]."
    assert synthesiser.extract_citations(text) == ["b.txt", "a.txt"]


def test_extract_citations_returns_empty_for_uncited_text():
    """An uncited section must surface as zero citations, so the Reviewer can
    reject it rather than the pipeline quietly passing it through."""
    assert synthesiser.extract_citations("A confident claim with no source.") == []


# ---------------------------------------------------------------------------
# Whole-briefing assembly
# ---------------------------------------------------------------------------

def test_derived_section_is_not_generated(monkeypatch):
    section = {"number": 7, "name": "Sources", "derived": True, "sub_queries": []}
    result = synthesiser.synthesise_section(section, PLAN_STUB, generate=never_called)

    assert result["status"] == synthesiser.STATUS_DERIVED


def test_synthesise_assembles_sources_from_citations(monkeypatch):
    """Section 7 is the union of what sections 1 to 6 actually cited."""
    hit_a = FakeHit(1, "a.txt", "text a")
    hit_b = FakeHit(2, "b.txt", "text b")
    monkeypatch.setattr(
        query,
        "retrieve",
        fake_retrieve({"q1": [(hit_a, 3.0)], "q2": [(hit_b, 3.0)]}),
    )

    plan = dict(
        PLAN_STUB,
        sections=[
            {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q1"]},
            {"number": 3, "name": "Competing formats", "sub_queries": ["q2"]},
            {"number": 7, "name": "Sources", "derived": True, "sub_queries": []},
        ],
    )

    briefing = synthesiser.synthesise(
        plan, generate=lambda prompt: "Claim [source: a.txt] and [source: b.txt]."
    )

    assert briefing["sources"] == ["a.txt", "b.txt"]


def test_synthesise_reports_mixed_statuses(monkeypatch):
    """A briefing where some sections answer and others refuse is a valid
    result, not a partial failure."""
    hit = FakeHit(1, "a.txt", "text")
    monkeypatch.setattr(
        query,
        "retrieve",
        fake_retrieve({"q1": [(hit, 3.0)], "q2": [(hit, -9.0)]}),
    )

    plan = dict(
        PLAN_STUB,
        sections=[
            {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q1"]},
            {"number": 4, "name": "Trend signals", "sub_queries": ["q2"]},
        ],
    )

    briefing = synthesiser.synthesise(
        plan, generate=lambda prompt: "Claim [source: a.txt]."
    )

    statuses = [section["status"] for section in briefing["sections"]]
    assert statuses == [synthesiser.STATUS_ANSWERED, synthesiser.STATUS_INSUFFICIENT]


# ---------------------------------------------------------------------------
# Live
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=False,
    reason=(
        "Citation compliance is not reliable on the free-tier model. Across the "
        "first two live runs of this test, section 2 came back answered with "
        "three correct citations once and answered with zero citations once. "
        "Same code, same plan shape. The assertion is the correct contract and "
        "it stays as written: prompt-level citation enforcement is a request "
        "the model sometimes honours, not a guarantee. Closing this is the "
        "Reviewer stage's job, which rejects an uncited claim rather than "
        "hoping the synthesiser attaches one. Marked non-strict so a passing "
        "run is not itself a failure, and left in the suite so the flake stays "
        "visible rather than being tuned away."
    ),
)
def test_live_briefing_answers_what_the_corpus_supports_and_refuses_the_rest():
    """Live call. Slow on the free tier, minutes rather than seconds.

    The corpus is 20 commission announcements. Broadcaster slate and
    competing formats have evidence. Territory snapshot, trend signals,
    format fit and risks do not. The assertion is that split.
    """
    import planner

    plan = planner.plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )
    assert planner.validate_plan(plan) == []

    briefing = synthesiser.synthesise(plan)
    by_number = {section["number"]: section for section in briefing["sections"]}

    assert by_number[2]["status"] == synthesiser.STATUS_ANSWERED
    assert by_number[2]["citations"]

    unsupported = [by_number[n]["status"] for n in (1, 4, 5, 6)]
    assert synthesiser.STATUS_INSUFFICIENT in unsupported


def gather(sub_queries):
    """Shorthand for the module-level default threshold."""
    return synthesiser.gather_evidence(sub_queries)
