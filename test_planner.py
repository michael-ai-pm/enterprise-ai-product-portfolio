"""Tests for the Planner stage.

The Planner is tested in two halves, deliberately.

The schema and parsing logic are pure functions, so they are tested against
fixtures with no LLM call at all. They are fast, free and deterministic,
and they are where most planning bugs actually live.

The live call is tested separately and thinly. It confirms the model
returns something that parses and validates, which is the contract the
rest of the loop depends on. It is slow and it costs a request, so it
carries one assertion set rather than many.
"""

import planner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_valid_plan():
    """A minimal plan that should pass validation."""
    sections = []
    for index, name in enumerate(planner.SECTIONS, start=1):
        derived = name in planner.DERIVED_SECTIONS
        sections.append({
            "number": index,
            "name": name,
            "derived": derived,
            "sub_queries": [] if derived else ["query one", "query two"],
        })
    return {
        "format": "A quiz format",
        "broadcaster": "Channel 4",
        "territory": "United Kingdom",
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

def test_seven_sections_defined():
    """The briefing contract is seven sections. If this changes, the
    architecture document changed and the prompt must change with it."""
    assert len(planner.SECTIONS) == 7


def test_sources_is_the_derived_section():
    assert planner.DERIVED_SECTIONS == {"Sources"}
    assert planner.SECTIONS[-1] == "Sources"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def test_system_prompt_injects_the_date():
    """Without a real date the model anchors sub-queries to its training
    cutoff, which is the defect this injection exists to prevent."""
    import datetime
    prompt = planner.build_system_prompt(today=datetime.date(2026, 7, 21))
    assert "21 July 2026" in prompt
    assert "{today}" not in prompt


def test_system_prompt_keeps_the_json_example_intact():
    """The prompt contains a literal JSON example. A templating mistake
    would silently mangle it and the model would lose the schema."""
    prompt = planner.build_system_prompt()
    assert '"sections": [' in prompt
    assert '"derived": true' in prompt


def test_system_prompt_forbids_invented_years():
    prompt = planner.build_system_prompt()
    assert "Do NOT put years" in prompt


def test_user_prompt_carries_all_three_inputs():
    prompt = planner.build_planner_prompt("A quiz format", "Channel 4", "United Kingdom")
    assert "A quiz format" in prompt
    assert "Channel 4" in prompt
    assert "United Kingdom" in prompt


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def test_parse_plain_json():
    assert planner.parse_plan('{"a": 1}') == {"a": 1}


def test_parse_strips_markdown_fence():
    """Models wrap JSON in fences even when told not to. Parsing must
    survive that rather than failing the whole stage on a habit."""
    raw = '```json\n{"a": 1}\n```'
    assert planner.parse_plan(raw) == {"a": 1}


def test_parse_strips_bare_fence():
    raw = '```\n{"a": 1}\n```'
    assert planner.parse_plan(raw) == {"a": 1}


def test_parse_tolerates_surrounding_whitespace():
    assert planner.parse_plan('\n\n  {"a": 1}  \n') == {"a": 1}


# ---------------------------------------------------------------------------
# Validation: the happy path
# ---------------------------------------------------------------------------

def test_valid_plan_has_no_problems():
    assert planner.validate_plan(make_valid_plan()) == []


# ---------------------------------------------------------------------------
# Validation: the failures it must catch
# ---------------------------------------------------------------------------

def test_rejects_wrong_section_count():
    plan = make_valid_plan()
    plan["sections"] = plan["sections"][:6]
    problems = planner.validate_plan(plan)
    assert any("expected 7 sections" in p for p in problems)


def test_rejects_renamed_section():
    plan = make_valid_plan()
    plan["sections"][0]["name"] = "Territory overview"
    problems = planner.validate_plan(plan)
    assert any("section 1" in p and "name" in p for p in problems)


def test_rejects_out_of_order_numbering():
    plan = make_valid_plan()
    plan["sections"][2]["number"] = 9
    problems = planner.validate_plan(plan)
    assert any("section 3" in p and "number" in p for p in problems)


def test_rejects_too_few_sub_queries():
    plan = make_valid_plan()
    plan["sections"][0]["sub_queries"] = ["only one"]
    problems = planner.validate_plan(plan)
    assert any("only 1 sub-queries" in p for p in problems)


def test_rejects_sub_queries_on_derived_section():
    """Sources is assembled from citations. If the model plans retrieval
    for it, the model has misread the contract."""
    plan = make_valid_plan()
    plan["sections"][6]["sub_queries"] = ["should not be here"]
    problems = planner.validate_plan(plan)
    assert any("derived section" in p for p in problems)


def test_rejects_missing_top_level_keys():
    plan = make_valid_plan()
    del plan["broadcaster"]
    problems = planner.validate_plan(plan)
    assert any("broadcaster" in p for p in problems)


def test_rejects_sections_not_a_list():
    problems = planner.validate_plan({"sections": "nope"})
    assert any("not a list" in p for p in problems)


# ---------------------------------------------------------------------------
# Live call
# ---------------------------------------------------------------------------

def test_live_plan_is_valid():
    """The one test that costs a request. Confirms the model actually
    returns a plan that parses and validates against the schema, which is
    the contract every downstream stage depends on."""
    result = planner.plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )
    problems = planner.validate_plan(result)
    assert problems == [], "Live plan failed validation:\n" + "\n".join(problems)


def test_live_plan_avoids_invented_year_anchors():
    """Regression test for the date-anchoring defect found on 21 July.
    The model dated every sub-query to its training cutoff, and those year
    tokens match nothing in a 2026 corpus."""
    result = planner.plan(
        format_name="The Golden Elevators, a high-stakes primetime quiz format",
        broadcaster="Channel 4",
        territory="United Kingdom",
    )
    stale_years = {"2019", "2020", "2021", "2022", "2023", "2024"}
    offenders = []
    for section in result["sections"]:
        for sub_query in section["sub_queries"]:
            for year in stale_years:
                if year in sub_query:
                    offenders.append(f"  section {section['number']}: {sub_query}")
    assert not offenders, "Sub-queries carry invented year anchors:\n" + "\n".join(offenders)
