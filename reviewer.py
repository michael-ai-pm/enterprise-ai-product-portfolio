"""Reviewer: checks the Synthesiser's output against the citation contract.

Step five of the constrained agent loop in section 7 of the architecture
document. It exists because of a measured failure, not a theoretical one.
Running the Synthesiser twice on the same plan produced a section marked
answered with three correct citations once, and the same section marked
answered with no citations at all the other time. Prompt-level citation
enforcement is a request a weak model honours some of the time. The
Reviewer is what turns it into a contract.

Its job is narrow on purpose. It is not a general quality critic and it is
not a second synthesiser. It checks three things and routes a failure back
for one retry.

Two tiers, cheap gating expensive, the same shape as the Synthesiser's
retrieval gate.

Tier one is pure Python. Free, deterministic, reproducible offline, and it
covers the whole rubric: a citation is present, a citation is real, and a
refused section stays empty. Every section goes through it.

Tier two is an LLM support check, asking whether the cited source actually
backs the claim. It runs only on sections that clear tier one, so a section
that failed the free check never costs a call.

Tier two is OFF by default inside the loop, and that is a decision worth
stating rather than burying. Section 7 caps a request at twelve LLM calls.
One planner call plus up to six synthesis calls plus retries already reaches
ten or eleven. Adding a support-check call per section breaks the cap. So
the loop runs tier one only, and tier two is exposed as a flag for the eval
harness, where it acts as a judge outside the request budget. That is a real
tension between section 4, which describes an LLM reviewer, and section 7,
which sets the cap. Inside the loop the cap wins.
"""

import os

from dotenv import load_dotenv
import litellm

import synthesiser

load_dotenv()


VERDICT_PASS = "pass"
VERDICT_FAIL = "fail"

# Failure codes. Stable strings rather than prose, because the eval pipeline
# counts them and a reworded message should not change a metric.
FAILURE_MISSING_CITATION = "missing_citation"
FAILURE_INVENTED_CITATION = "invented_citation"
FAILURE_FABRICATED_CONTENT = "fabricated_content"
FAILURE_UNSUPPORTED_CLAIM = "unsupported_claim"

# Section 7: retry once on failure, then surface as a quality warning.
# One retry, so two attempts in total.
MAX_ATTEMPTS = 2

# Human-readable reasons, fed back into the synthesis prompt on a retry.
FAILURE_FEEDBACK = {
    FAILURE_MISSING_CITATION: (
        "The section made factual claims with no citation. Every factual claim "
        "must carry [source: filename] inline."
    ),
    FAILURE_INVENTED_CITATION: (
        "The section cited a filename that was not among the sources provided. "
        "Cite only the sources given to you."
    ),
    FAILURE_FABRICATED_CONTENT: (
        "The section was refused for lack of sources but still contained text. "
        "A refused section carries no prose."
    ),
    FAILURE_UNSUPPORTED_CLAIM: (
        "A claim in the section was not supported by the source it cited."
    ),
}


JUDGE_SYSTEM_PROMPT = """You are the review stage of a market research agent. You check whether a written section is supported by the sources it cites.

You are not rewriting the section and you are not judging whether it is well written. You are answering one question: is every factual claim in this section actually supported by the source text provided?

Reply with exactly the single word SUPPORTED if every claim is backed by the sources.

Otherwise reply with UNSUPPORTED followed by one sentence naming the claim that is not backed. Do not reply with anything else."""


def kept_sources(section):
    """The filenames that survived the Synthesiser's relevance gate."""
    return {
        entry["source"]
        for entry in section.get("sources_considered", [])
        if entry.get("kept")
    }


def check_section(section):
    """Tier one. Deterministic checks, no model call. Returns failure codes.

    An empty list means the section passes. Returning codes rather than
    raising keeps every failure visible in one pass, which is the same
    choice planner.validate_plan makes.
    """
    failures = []
    status = section.get("status")

    if status == synthesiser.STATUS_ANSWERED:
        citations = section.get("citations", [])

        # Rubric one. This is the check the citation flake demanded.
        if not citations:
            failures.append(FAILURE_MISSING_CITATION)

        # Rubric two. A citation must name a source that was actually put in
        # front of the model, not one it produced from nowhere.
        available = kept_sources(section)
        for citation in citations:
            if citation not in available:
                failures.append(FAILURE_INVENTED_CITATION)
                break

    elif status == synthesiser.STATUS_INSUFFICIENT:
        # Rubric three. A refusal that quietly carries prose is the failure
        # mode the refusal exists to prevent.
        if section.get("text", "").strip():
            failures.append(FAILURE_FABRICATED_CONTENT)

    return failures


def build_feedback(failures):
    """Turn failure codes into the prose passed back to the Synthesiser."""
    return "\n".join(
        f"- {FAILURE_FEEDBACK[code]}" for code in failures if code in FAILURE_FEEDBACK
    )


def judge_support(section, plan_section, judge=None, min_score=synthesiser.SECTION_MIN_SCORE):
    """Tier two. Ask a model whether the cited sources back the claims.

    Off by default in the loop, see the module docstring on the call cap.
    The evidence is re-gathered rather than carried through the result,
    because retrieval is local and free while storing every chunk's full
    text in the briefing would bloat the audit record for no gain.
    """
    if judge is None:
        judge = _judge

    kept, _considered = synthesiser.gather_evidence(
        plan_section.get("sub_queries", []), min_score=min_score
    )
    if not kept:
        return []

    hits = [hit for hit, score in kept]
    verdict = judge(section.get("text", ""), hits)

    if verdict.strip().upper().startswith("SUPPORTED"):
        return []
    return [FAILURE_UNSUPPORTED_CLAIM]


def review_section(section, plan, plan_section, generate=None, deep=False, judge=None):
    """Review one section, retrying once if it fails.

    Returns the section, which is the original if it passed and the
    resynthesised one if a retry happened. The `review` key carries the
    verdict, the failures, the attempt count and the quality warning, so the
    eval pipeline reads retry rate straight off the result rather than
    inferring it.
    """
    failures = check_section(section)

    if not failures and deep and section.get("status") == synthesiser.STATUS_ANSWERED:
        failures = judge_support(section, plan_section, judge=judge)

    if not failures:
        section["review"] = {
            "verdict": VERDICT_PASS,
            "failures": [],
            "attempts": 1,
            "warning": False,
        }
        return section

    # Retry once, with the failure reasons in context. A derived section has
    # nothing to resynthesise, so it is never retried.
    if plan_section is None or section.get("status") == synthesiser.STATUS_DERIVED:
        section["review"] = {
            "verdict": VERDICT_FAIL,
            "failures": failures,
            "attempts": 1,
            "warning": True,
        }
        return section

    retried = synthesiser.synthesise_section(
        plan_section, plan, generate=generate, feedback=build_feedback(failures)
    )

    second_failures = check_section(retried)
    if not second_failures and deep and retried.get("status") == synthesiser.STATUS_ANSWERED:
        second_failures = judge_support(retried, plan_section, judge=judge)

    # A second failure surfaces as a quality warning rather than being
    # dropped or silently passed. The user sees the section and sees that
    # review does not stand behind it.
    retried["review"] = {
        "verdict": VERDICT_PASS if not second_failures else VERDICT_FAIL,
        "failures": second_failures,
        "first_attempt_failures": failures,
        "attempts": MAX_ATTEMPTS,
        "warning": bool(second_failures),
    }
    return retried


def review(briefing, plan, generate=None, deep=False, judge=None):
    """Review every section of a briefing and return the reviewed briefing.

    The briefing is rebuilt rather than mutated in place, because a retried
    section is a different section and the audit record should not pretend
    otherwise.
    """
    plan_by_number = {
        section.get("number"): section for section in plan.get("sections", [])
    }

    reviewed = []
    for section in briefing.get("sections", []):
        reviewed.append(
            review_section(
                section,
                plan,
                plan_by_number.get(section.get("number")),
                generate=generate,
                deep=deep,
                judge=judge,
            )
        )

    # Sources are reassembled, because a retry can change what was cited.
    cited = []
    for section in reviewed:
        for citation in section.get("citations", []):
            if citation not in cited:
                cited.append(citation)

    result = dict(briefing)
    result["sections"] = reviewed
    result["sources"] = sorted(cited)
    result["review_summary"] = summarise(reviewed)
    return result


def summarise(sections):
    """Counts the eval pipeline reads directly."""
    return {
        "sections": len(sections),
        "passed": sum(1 for s in sections if s.get("review", {}).get("verdict") == VERDICT_PASS),
        "failed": sum(1 for s in sections if s.get("review", {}).get("verdict") == VERDICT_FAIL),
        "retried": sum(1 for s in sections if s.get("review", {}).get("attempts", 1) > 1),
        "warnings": sum(1 for s in sections if s.get("review", {}).get("warning")),
    }


def _judge(section_text, hits):
    """The live tier-two call."""
    context = synthesiser.query.build_context(hits)
    response = litellm.completion(
        model="openrouter/openrouter/free",
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Sources:\n\n{context}\n\nSection:\n\n{section_text}",
            },
        ],
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import planner

    the_plan = planner.plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )

    briefing = review(synthesiser.synthesise(the_plan), the_plan)

    for section in briefing["sections"]:
        review_result = section["review"]
        line = f"--- {section['number']}. {section['name']} [{section['status']}]"
        line += f" review={review_result['verdict']} attempts={review_result['attempts']}"
        if review_result["warning"]:
            line += " QUALITY WARNING"
        print(line)
        if review_result["failures"]:
            print(f"    failures: {', '.join(review_result['failures'])}")
        if section["status"] == synthesiser.STATUS_ANSWERED:
            print(f"    citations: {', '.join(section['citations']) or 'NONE'}")
        print()

    print(briefing["review_summary"])
