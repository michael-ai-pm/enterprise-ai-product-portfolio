"""Integration test for the retrieval pipeline over the full 20-document corpus.

Unlike the unit tests, which check each function in isolation, this test
checks that hybrid retrieval plus reranking returns the *correct* source
document for a set of questions with known answers. It proves the pipeline
discriminates between 20 similar documents, not just that it runs.

Run after ingesting the full corpus (python ingest.py).
"""

import query


# Each case: a question, and the source file that should be the top hit.
# These are chosen to span broadcasters, genres, and query types (title,
# host, subject matter) so the test exercises real discrimination.
KNOWN_ANSWERS = [
    ("Which quiz show is hosted by Richard Osman?", "itv-golden-elevators.txt"),
    ("Which daytime quiz show does Sandi Toksvig host?", "itv-second-guess.txt"),
    ("Which drama is set in a Highland fishing village in 1919?", "bbc-longest-winter.txt"),
    ("Which documentary follows workers in the gig economy?", "c4-below-the-line.txt"),
    ("Which series follows volunteer lifeboat crews?", "c5-coastal-rescue.txt"),
    ("Which thriller follows a sound engineer hearing voices?", "sky-quiet-house.txt"),
    ("Which natural history series is narrated by David Attenborough?", "bbc-marsh-kings.txt"),
    ("Which fantasy drama is set in a kingdom where memory is currency?", "netflix-ravenscar.txt"),
    ("Which crime drama follows a forensic accountant in Birmingham?", "bbc-the-ledger.txt"),
    ("Which Welsh-language thriller is set on the Ceredigion coast?", "bbc-tidewater.txt"),
]


def test_top_hit_is_correct_source():
    """For each known question, the correct document should be the top hit.

    We assert on the single best result after reranking. This is the
    strongest form of the test: not just 'the right doc appears somewhere'
    but 'the right doc ranks first'.
    """
    failures = []
    for question, expected_source in KNOWN_ANSWERS:
        hits = query.retrieve(question, k=3)
        assert hits, f"No hits returned for: {question}"
        top_source = hits[0].payload["source"]
        if top_source != expected_source:
            failures.append(
                f"  '{question}'\n"
                f"    expected: {expected_source}\n"
                f"    got:      {top_source}"
            )
    assert not failures, "Top-hit mismatches:\n" + "\n".join(failures)


def test_correct_source_in_top_3():
    """A softer check: the correct document should at least appear in the
    top 3 results for every question. If the strict top-hit test above
    fails but this passes, retrieval is working but ranking needs tuning."""
    failures = []
    for question, expected_source in KNOWN_ANSWERS:
        hits = query.retrieve(question, k=3)
        sources = [h.payload["source"] for h in hits]
        if expected_source not in sources:
            failures.append(f"  '{question}' -> {sources}")
    assert not failures, "Correct source missing from top 3:\n" + "\n".join(failures)


def test_full_answer_carries_citation():
    """End to end through the LLM: the generated answer must cite a source.
    This confirms the synthesis step enforces citation as designed."""
    result = query.answer("Which quiz show is hosted by Richard Osman?")
    assert "[source:" in result.lower()