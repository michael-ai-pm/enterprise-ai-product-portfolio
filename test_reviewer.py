"""Tests for the Reviewer stage.

Offline against fixture sections, with generation injected. The Reviewer's
whole reason for existing is that the model is unreliable, so a test suite
that needs the model to behave in order to prove the Reviewer works would be
missing the point.

The live test is the one that matters for the backlog: it runs a real
briefing through review and asserts that no answered section survives
without a citation. That is the assertion the Synthesiser could not hold.
"""

import pytest

import reviewer
import synthesiser


PLAN_STUB = {
    "format": "The Golden Elevators",
    "broadcaster": "Channel 4",
    "territory": "United Kingdom",
}


def answered(text="A claim [source: a.txt].", citations=("a.txt",), kept=("a.txt",)):
    return {
        "number": 2,
        "name": "Broadcaster slate",
        "status": synthesiser.STATUS_ANSWERED,
        "reason": None,
        "text": text,
        "citations": list(citations),
        "sources_considered": [
            {"source": name, "score": 5.0, "kept": True} for name in kept
        ],
    }


def refused(text=""):
    return {
        "number": 1,
        "name": "Territory snapshot",
        "status": synthesiser.STATUS_INSUFFICIENT,
        "reason": synthesiser.REASON_NO_EVIDENCE,
        "text": text,
        "citations": [],
        "sources_considered": [],
    }


# ---------------------------------------------------------------------------
# Tier one: the deterministic checks
# ---------------------------------------------------------------------------

def test_clean_answered_section_passes():
    assert reviewer.check_section(answered()) == []


def test_answered_section_without_citations_fails():
    """The measured failure the Reviewer was built for."""
    section = answered(text="A confident claim with no source.", citations=())
    assert reviewer.check_section(section) == [reviewer.FAILURE_MISSING_CITATION]


def test_citation_naming_a_source_never_retrieved_fails():
    section = answered(citations=("invented.txt",), kept=("a.txt",))
    assert reviewer.FAILURE_INVENTED_CITATION in reviewer.check_section(section)


def test_citation_of_a_rejected_source_fails():
    """A chunk that failed the relevance gate was never shown to the model,
    so citing it is an invented citation even though the file is real."""
    section = answered(citations=("b.txt",), kept=("a.txt",))
    section["sources_considered"].append(
        {"source": "b.txt", "score": -4.0, "kept": False}
    )
    assert reviewer.FAILURE_INVENTED_CITATION in reviewer.check_section(section)


def test_refused_section_with_prose_fails():
    """A refusal carrying text is the exact failure the refusal prevents."""
    section = refused(text="The UK market is growing strongly.")
    assert reviewer.check_section(section) == [reviewer.FAILURE_FABRICATED_CONTENT]


def test_clean_refused_section_passes():
    assert reviewer.check_section(refused()) == []


def test_derived_section_is_not_checked():
    section = {"number": 7, "name": "Sources", "status": synthesiser.STATUS_DERIVED,
               "text": "", "citations": [], "sources_considered": []}
    assert reviewer.check_section(section) == []


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

def test_failed_section_is_retried_once_and_can_recover(monkeypatch):
    """The loop in section 7: one retry with the failure reasons in context."""
    fixed = answered()
    monkeypatch.setattr(
        synthesiser, "synthesise_section", lambda *a, **k: dict(fixed)
    )

    broken = answered(text="No source here.", citations=())
    result = reviewer.review_section(
        broken, PLAN_STUB, {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]}
    )

    assert result["review"]["verdict"] == reviewer.VERDICT_PASS
    assert result["review"]["attempts"] == 2
    assert result["review"]["warning"] is False
    assert result["review"]["first_attempt_failures"] == [reviewer.FAILURE_MISSING_CITATION]


def test_second_failure_surfaces_as_quality_warning(monkeypatch):
    """Two strikes and the section is surfaced with a warning, not dropped
    and not silently passed."""
    monkeypatch.setattr(
        synthesiser,
        "synthesise_section",
        lambda *a, **k: answered(text="Still no source.", citations=()),
    )

    broken = answered(text="No source here.", citations=())
    result = reviewer.review_section(
        broken, PLAN_STUB, {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]}
    )

    assert result["review"]["verdict"] == reviewer.VERDICT_FAIL
    assert result["review"]["attempts"] == reviewer.MAX_ATTEMPTS
    assert result["review"]["warning"] is True
    assert result["text"]


def test_passing_section_is_not_retried(monkeypatch):
    """A clean section costs nothing. No resynthesis, no call."""
    def explode(*args, **kwargs):
        raise AssertionError("a passing section must not be resynthesised")

    monkeypatch.setattr(synthesiser, "synthesise_section", explode)

    result = reviewer.review_section(
        answered(), PLAN_STUB, {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]}
    )
    assert result["review"]["attempts"] == 1


def test_retry_feedback_names_the_failure():
    feedback = reviewer.build_feedback([reviewer.FAILURE_MISSING_CITATION])
    assert "citation" in feedback.lower()


# ---------------------------------------------------------------------------
# Tier two: the LLM support check
# ---------------------------------------------------------------------------

def test_deep_check_does_not_run_when_tier_one_already_failed(monkeypatch):
    """The cheap gate protects the expensive one. A section that failed the
    free check must never reach the judge."""
    def explode(*args, **kwargs):
        raise AssertionError("judge was called on a section that failed tier one")

    monkeypatch.setattr(
        synthesiser, "synthesise_section", lambda *a, **k: answered()
    )

    broken = answered(text="No source.", citations=())
    reviewer.review_section(
        broken,
        PLAN_STUB,
        {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]},
        deep=True,
        judge=explode,
    )


def test_unsupported_verdict_from_judge_becomes_a_failure(monkeypatch):
    monkeypatch.setattr(
        synthesiser,
        "gather_evidence",
        lambda sub_queries, min_score=0.0: ([("hit", 5.0)], [("hit", 5.0)]),
    )
    monkeypatch.setattr(synthesiser.query, "build_context", lambda hits: "ctx")

    failures = reviewer.judge_support(
        answered(),
        {"sub_queries": ["q"]},
        judge=lambda text, hits: "UNSUPPORTED the claim about ratings is not in the source.",
    )
    assert failures == [reviewer.FAILURE_UNSUPPORTED_CLAIM]


def test_supported_verdict_from_judge_passes(monkeypatch):
    monkeypatch.setattr(
        synthesiser,
        "gather_evidence",
        lambda sub_queries, min_score=0.0: ([("hit", 5.0)], [("hit", 5.0)]),
    )
    monkeypatch.setattr(synthesiser.query, "build_context", lambda hits: "ctx")

    assert reviewer.judge_support(
        answered(), {"sub_queries": ["q"]}, judge=lambda text, hits: "SUPPORTED"
    ) == []


# ---------------------------------------------------------------------------
# Whole-briefing review
# ---------------------------------------------------------------------------

def test_review_summarises_counts(monkeypatch):
    monkeypatch.setattr(
        synthesiser, "synthesise_section", lambda *a, **k: answered()
    )

    briefing = {"sections": [answered(), refused(), answered(text="Nope.", citations=())]}
    plan = dict(
        PLAN_STUB,
        sections=[
            {"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]},
            {"number": 1, "name": "Territory snapshot", "sub_queries": ["q"]},
        ],
    )

    result = reviewer.review(briefing, plan)

    assert result["review_summary"]["sections"] == 3
    assert result["review_summary"]["retried"] == 1
    assert result["review_summary"]["warnings"] == 0


def test_review_reassembles_sources_after_a_retry(monkeypatch):
    """A retry can change what was cited, so section 7 is rebuilt from the
    reviewed sections rather than carried over."""
    monkeypatch.setattr(
        synthesiser,
        "synthesise_section",
        lambda *a, **k: answered(citations=("z.txt",), kept=("z.txt",)),
    )

    briefing = {"sections": [answered(text="Nope.", citations=())], "sources": []}
    plan = dict(PLAN_STUB, sections=[{"number": 2, "name": "Broadcaster slate", "sub_queries": ["q"]}])

    assert reviewer.review(briefing, plan)["sources"] == ["z.txt"]


# ---------------------------------------------------------------------------
# Live
# ---------------------------------------------------------------------------

def test_live_review_leaves_no_uncited_answered_section():
    """Live, slow, and the point of the whole stage.

    This is the assertion the Synthesiser alone could not hold, and it now
    lives here rather than in test_synthesiser.py, where it was marked
    xfail because the model attached citations roughly half the time. The
    contract belongs to the stage that enforces it, not the stage that
    requests it.

    After review, an answered section either carries a citation or carries a
    quality warning saying review does not stand behind it. It is never
    quietly uncited. Note that both outcomes are acceptable: the Reviewer's
    job is to make the failure visible, not to guarantee the model
    eventually complies.
    """
    import planner

    plan = planner.plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )
    assert planner.validate_plan(plan) == []

    briefing = reviewer.review(synthesiser.synthesise(plan), plan)

    for section in briefing["sections"]:
        if section["status"] != synthesiser.STATUS_ANSWERED:
            continue
        assert section["citations"] or section["review"]["warning"], (
            f"section {section['number']} is answered, uncited and unflagged"
        )
