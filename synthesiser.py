"""Synthesiser LLM: composes the briefing from a plan and the retrieval layer.

This is the fourth step of the constrained agent loop in section 7 of the
architecture document. It takes a validated plan from planner.plan(), runs
each sub-query through query.retrieve(), and writes the section text with a
citation on every factual claim.

The decision that shapes this whole file: a section with no supporting
evidence returns an explicit insufficient_sources status. It does not get
filled in from model knowledge.

That is not a workaround for a thin corpus. The corpus here is 20 commission
announcements, so sections 2 and 3 (broadcaster slate, competing formats)
have something to retrieve against and sections 1, 4, 5 and 6 do not. An
agent that writes a confident territory snapshot with no viewing data behind
it is the failure mode citation enforcement exists to prevent. So the
refusal is a first-class output: it carries a status field, a reason, and
the evidence that was considered and rejected, all of which the Reviewer and
the eval harness can score directly.

There are two gates, deliberately.

The first is deterministic and runs before any generation call. Every
retrieved chunk carries a cross-encoder relevance score, and a section whose
best chunk fails to clear SECTION_MIN_SCORE is refused without an LLM call
at all. That makes the refusal reproducible offline, attributable to
retrieval rather than to the model, and free.

The second is the model's own. If the sources clear the threshold but do not
actually address the section, the Synthesiser returns a fixed token rather
than writing around the gap. Recording which gate fired is the point: a
retrieval-side refusal and a model-side refusal are different findings.
"""

import os
import re

from dotenv import load_dotenv
import litellm

import query

load_dotenv()


# Cross-encoder relevance floor for a chunk to count as evidence.
# The ms-marco cross-encoder returns a logit, roughly -11 to +11, where
# positive means the model judges the chunk relevant to the query. Zero is
# the natural decision boundary and that is why it is the starting value.
# It is a hand-set threshold, not a measured one. Tuning it against the
# offline golden set, once that exists, is the honest way to arrive at a
# number, and until then this is a provisional default.
SECTION_MIN_SCORE = 0.0

# Chunks pulled per sub-query before the threshold filter.
HITS_PER_SUB_QUERY = 3

# The token the model returns rather than writing a section it cannot
# support. A fixed sentinel, not a phrase, so parsing it is exact.
INSUFFICIENT_TOKEN = "INSUFFICIENT_SOURCES"

# Section statuses. These are the values the Reviewer and the eval harness
# read, so they are part of the contract rather than incidental strings.
STATUS_ANSWERED = "answered"
STATUS_INSUFFICIENT = "insufficient_sources"
STATUS_DERIVED = "derived"

# Which gate produced a refusal.
REASON_NO_EVIDENCE = "no_evidence_retrieved"
REASON_MODEL_DECLINED = "model_declined"


SYNTHESISER_SYSTEM_PROMPT = """You are the synthesis stage of a market research agent for a TV format sales team.

You are writing ONE section of a market briefing. You will be given the section name, what the section is meant to cover, and a set of retrieved sources.

Rules, in order of importance:

1. Use ONLY the sources provided. Do not use anything you know from training. If a fact is not in the sources, it does not go in the section.
2. Every factual claim must cite its source inline, in the form [source: filename]. A sentence carrying a fact with no citation is a failure.
3. If the sources provided do not actually address this section, reply with exactly the single word INSUFFICIENT_SOURCES and nothing else. Do not write a partial section. Do not hedge your way to an answer. Do not reason from general knowledge about the territory, the broadcaster or the market.

Point 3 is not a fallback for a hard question. It is the correct answer whenever the evidence is absent. A short honest refusal is worth more here than a plausible paragraph.

Write two to four sentences of plain prose. No headings, no bullet points, no preamble."""


def build_section_prompt(section_name, plan, hits, feedback=None):
    """Build the user prompt for a single section's synthesis.

    `feedback` carries the Reviewer's failure reasons on a retry. Section 7
    of the architecture document specifies one retry with the failure
    reasons in context, so the reasons go into the prompt rather than the
    section simply being regenerated and hoped over.
    """
    context = query.build_context(hits)
    prompt = (
        f"Format being pitched: {plan.get('format')}\n"
        f"Target broadcaster: {plan.get('broadcaster')}\n"
        f"Territory: {plan.get('territory')}\n\n"
        f"Section to write: {section_name}\n\n"
        f"Sources:\n\n{context}\n\n"
    )

    if feedback:
        prompt += (
            "A previous attempt at this section was REJECTED by review for "
            f"the following reason(s):\n{feedback}\n\n"
            "Write the section again and fix those failures. The citation "
            "rule is not optional.\n\n"
        )

    return prompt + f"Write the {section_name} section."


def gather_evidence(sub_queries, min_score=SECTION_MIN_SCORE, k=HITS_PER_SUB_QUERY):
    """Retrieve for every sub-query in a section and keep what clears the floor.

    Returns (kept, considered). Both are lists of (hit, score) pairs,
    deduplicated by point id and sorted best first. The rejected candidates
    stay in `considered` on purpose: section 6.3 of the architecture
    document keeps the discarded set because when retrieval quality drops,
    that set is the first place to look.
    """
    by_id = {}

    for sub_query in sub_queries:
        for hit, score in query.retrieve(sub_query, k=k, with_scores=True):
            # A chunk can surface for several sub-queries in the same
            # section. Keep the best score it earned across all of them.
            if hit.id not in by_id or score > by_id[hit.id][1]:
                by_id[hit.id] = (hit, score)

    considered = sorted(by_id.values(), key=lambda pair: pair[1], reverse=True)
    kept = [pair for pair in considered if pair[1] >= min_score]
    return kept, considered


def extract_citations(text):
    """Pull the cited filenames out of a section, in order, deduplicated."""
    found = re.findall(r"\[source:\s*([^\]]+)\]", text, flags=re.IGNORECASE)

    citations = []
    for name in found:
        name = name.strip()
        if name and name not in citations:
            citations.append(name)
    return citations


def is_refusal(text):
    """True if the model returned the refusal token rather than a section.

    Matched loosely on purpose. A model that wraps the token in a full stop
    or a stray quote has still refused, and treating that as prose would
    put the word INSUFFICIENT_SOURCES into a briefing.
    """
    stripped = text.strip().strip('."\'` ')
    return stripped.upper() == INSUFFICIENT_TOKEN


def synthesise_section(section, plan, min_score=SECTION_MIN_SCORE, generate=None, feedback=None):
    """Synthesise one section and return its structured result.

    `generate` is the generation function, injected so the offline tests can
    exercise both gates without a live call. `feedback` is the Reviewer's
    rejection reason on a retry.
    """
    if generate is None:
        generate = _generate

    name = section.get("name")
    number = section.get("number")

    result = {
        "number": number,
        "name": name,
        "status": STATUS_DERIVED,
        "reason": None,
        "text": "",
        "citations": [],
        "sources_considered": [],
    }

    if section.get("derived"):
        return result

    kept, considered = gather_evidence(
        section.get("sub_queries", []), min_score=min_score
    )

    result["sources_considered"] = [
        {"source": hit.payload["source"], "score": score, "kept": score >= min_score}
        for hit, score in considered
    ]

    # Gate one, deterministic. Nothing cleared the relevance floor, so the
    # section is refused here and no generation call is made.
    if not kept:
        result["status"] = STATUS_INSUFFICIENT
        result["reason"] = REASON_NO_EVIDENCE
        return result

    hits = [hit for hit, score in kept]
    text = generate(build_section_prompt(name, plan, hits, feedback=feedback))

    # Gate two, the model's own. The sources cleared the floor but do not
    # address the section.
    if is_refusal(text):
        result["status"] = STATUS_INSUFFICIENT
        result["reason"] = REASON_MODEL_DECLINED
        return result

    result["status"] = STATUS_ANSWERED
    result["text"] = text.strip()
    result["citations"] = extract_citations(text)
    return result


def synthesise(plan, min_score=SECTION_MIN_SCORE, generate=None):
    """Run the Synthesiser over a validated plan and return the briefing.

    The result carries per-section status so the Reviewer stage and the eval
    harness can score a refusal as a legitimate outcome rather than reading
    an empty section as a crash.
    """
    sections = []
    for section in plan.get("sections", []):
        sections.append(
            synthesise_section(section, plan, min_score=min_score, generate=generate)
        )

    # Section 7 is assembled from the citations above it, not retrieved.
    # This is the derived section the Planner declares and leaves empty.
    cited = []
    for section in sections:
        for citation in section["citations"]:
            if citation not in cited:
                cited.append(citation)

    return {
        "format": plan.get("format"),
        "broadcaster": plan.get("broadcaster"),
        "territory": plan.get("territory"),
        "sections": sections,
        "sources": sorted(cited),
    }


def _generate(user_prompt):
    """The live generation call. One call per answered section.

    Per section rather than one call for the whole briefing, so a failure is
    attributable to a section and each context stays small. Six sections is
    well inside the 12 LLM calls per request cap in section 7.
    """
    response = litellm.completion(
        model="openrouter/openrouter/free",
        messages=[
            {"role": "system", "content": SYNTHESISER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
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

    problems = planner.validate_plan(the_plan)
    if problems:
        print(f"Plan INVALID, {len(problems)} problem(s), synthesising anyway:")
        for problem in problems:
            print(f"  - {problem}")
        print()

    briefing = synthesise(the_plan)

    for section in briefing["sections"]:
        print(f"--- {section['number']}. {section['name']} [{section['status']}]")
        if section["status"] == STATUS_INSUFFICIENT:
            print(f"    reason: {section['reason']}")
            print(f"    candidates considered: {len(section['sources_considered'])}")
        elif section["status"] == STATUS_ANSWERED:
            print(section["text"])
            print(f"    citations: {', '.join(section['citations']) or 'NONE'}")
        print()

    print(f"Sources: {', '.join(briefing['sources']) or 'none'}")
