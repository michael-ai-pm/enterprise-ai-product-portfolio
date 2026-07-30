"""Planner LLM: decomposes a briefing request into a structured plan.

The Planner is the first stage of the constrained agent loop described in
section 7 of the architecture document. Given a format, a broadcaster and a
territory, it produces an explicit, logged plan of sub-queries, one set per
briefing section, before any retrieval happens.

Two decisions worth stating plainly.

First, the plan is structured output, not prose. The Planner returns JSON
against a fixed schema. This is what makes the stage independently
evaluable: I can score the plan on its own, without running retrieval or
synthesis, and attribute a failure to planning rather than to everything
downstream.

Second, the current date is injected into the system prompt and the
model is explicitly forbidden from inventing year anchors. Left to itself
it dates sub-queries to its training cutoff, which matches nothing in a
keyword index built from a differently dated corpus.

Third, section 7 (Sources) is declared in the plan but marked as derived.
It carries no sub-queries because it is assembled from the citations of
sections 1 to 6 rather than retrieved in its own right. Declaring it keeps
the plan faithful to the seven-section output contract in section 3.2 of
the architecture document without inventing retrieval work that does not
exist.
"""

import json
import os
from datetime import date

from dotenv import load_dotenv
import litellm

load_dotenv()


# The seven briefing sections from section 3.2 of the architecture document.
# The order is fixed and the plan must cover all of them.
SECTIONS = [
    "Territory snapshot",
    "Broadcaster slate",
    "Competing formats",
    "Trend signals",
    "Format fit",
    "Risks and counterarguments",
    "Sources",
]

# Section 7 is assembled from the citations of the sections above it.
DERIVED_SECTIONS = {"Sources"}


PLANNER_SYSTEM_PROMPT_TEMPLATE = """You are the planning stage of a market research agent for a TV format sales team.

Your job is to decompose a briefing request into an explicit retrieval plan. You do NOT answer the question and you do NOT write the briefing. You only plan what needs to be found.

The briefing has exactly seven sections, in this order:
1. Territory snapshot - TV consumption trends, AVOD versus SVOD split, peak slots
2. Broadcaster slate - current programming, recent commissions, gaps in the schedule
3. Competing formats - what is running, what is winning, what is being cancelled or remade
4. Trend signals - signals indicating audience appetite
5. Format fit - the reasoned argument for why this format suits this broadcaster and territory
6. Risks and counterarguments - what the broadcaster is likely to push back on
7. Sources - assembled from the citations of sections 1 to 6

Today's date is {today}. The retrieval index covers commission announcements and trade press from around this period.

For sections 1 to 6, produce two to four specific retrieval sub-queries each. A sub-query is a concrete search string, not a restatement of the section name. Write sub-queries that name the actual broadcaster, territory, genre or format where relevant, because they will be run against a retrieval index of commission announcements and trade press.

Do NOT put years or dates into sub-queries unless the user's request explicitly names one. The index is searched on keywords, so a year you invented will match nothing and will actively push the right document down the ranking. Write "Channel 4 recent quiz commissions", never "Channel 4 quiz commissions 2024".

Section 7 is derived. It carries no sub-queries.

Respond with ONLY a JSON object, no preamble, no explanation, no markdown code fences. Use exactly this shape:

{
  "format": "<the format given>",
  "broadcaster": "<the broadcaster given>",
  "territory": "<the territory given>",
  "sections": [
    {"number": 1, "name": "Territory snapshot", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 2, "name": "Broadcaster slate", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 3, "name": "Competing formats", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 4, "name": "Trend signals", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 5, "name": "Format fit", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 6, "name": "Risks and counterarguments", "derived": false, "sub_queries": ["...", "..."]},
    {"number": 7, "name": "Sources", "derived": true, "sub_queries": []}
  ]
}"""


def build_system_prompt(today=None):
    """Build the system prompt with the current date injected.

    The date matters more than it looks. Without it the model anchors its
    sub-queries to its own training cutoff and writes year tokens that
    appear nowhere in the corpus, which hurts keyword matching rather than
    helping it. Passing the date explicitly, and forbidding invented year
    anchors, is the fix.
    """
    if today is None:
        today = date.today()
    # A plain replace, not .format(). The prompt contains a literal JSON
    # example, and .format() would try to read every brace in it as a
    # placeholder and fail.
    return PLANNER_SYSTEM_PROMPT_TEMPLATE.replace("{today}", today.strftime("%d %B %Y"))


def build_planner_prompt(format_name, broadcaster, territory):
    """Build the user prompt for a single planning request."""
    return (
        f"Format to pitch: {format_name}\n"
        f"Target broadcaster: {broadcaster}\n"
        f"Territory: {territory}\n\n"
        "Produce the retrieval plan."
    )


def parse_plan(raw):
    """Parse the model's response into a plan dict.

    Models wrap JSON in markdown fences more often than they should, even
    when told not to. Rather than fail the whole stage on a formatting
    habit, strip the fence if it is there and parse what is inside.
    """
    text = raw.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        # Drop the opening fence line and any trailing fence line.
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)


def validate_plan(plan):
    """Check a plan against the schema. Returns a list of problems.

    An empty list means the plan is valid. I return the problems rather
    than raising, because during the build I want to see every failure in
    one pass rather than the first one only.
    """
    problems = []

    for key in ("format", "broadcaster", "territory", "sections"):
        if key not in plan:
            problems.append(f"missing top-level key: {key}")

    sections = plan.get("sections")
    if not isinstance(sections, list):
        problems.append("sections is not a list")
        return problems

    if len(sections) != 7:
        problems.append(f"expected 7 sections, got {len(sections)}")

    for index, section in enumerate(sections, start=1):
        name = section.get("name")
        expected_name = SECTIONS[index - 1] if index <= len(SECTIONS) else None

        if section.get("number") != index:
            problems.append(f"section {index}: number is {section.get('number')}")

        if expected_name and name != expected_name:
            problems.append(f"section {index}: name is '{name}', expected '{expected_name}'")

        sub_queries = section.get("sub_queries")
        if not isinstance(sub_queries, list):
            problems.append(f"section {index}: sub_queries is not a list")
            continue

        if name in DERIVED_SECTIONS:
            if sub_queries:
                problems.append(f"section {index}: derived section should have no sub-queries")
        else:
            if len(sub_queries) < 2:
                problems.append(f"section {index}: only {len(sub_queries)} sub-queries, expected at least 2")

    return problems


def plan(format_name, broadcaster, territory):
    """Run the Planner stage and return the parsed plan."""
    response = litellm.completion(
        model="openrouter/openrouter/free",
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_planner_prompt(format_name, broadcaster, territory)},
        ],
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    return parse_plan(response.choices[0].message.content)


if __name__ == "__main__":
    result = plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )

    print(json.dumps(result, indent=2))
    print()

    problems = validate_plan(result)
    if problems:
        print(f"Plan INVALID, {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("Plan valid: 7 sections, correct names, sub-queries present.")
