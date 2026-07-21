"""Unit tests for the retrieval layer in query.py.

These run against the real Qdrant store and BM25 index, so they confirm the
retrieval logic behaves correctly on the actual indexed corpus rather than on
mocks. Importing query.py loads the models and builds the index once.
"""

import query


def test_keyword_retrieval_returns_results_for_known_term():
    """A term that exists in the corpus should return at least one chunk."""
    hits = query.retrieve_keyword("Richard Osman", k=10)
    assert len(hits) > 0


def test_keyword_retrieval_filters_zero_scores():
    """Nonsense query with no keyword overlap should return nothing,
    because retrieve_keyword drops any chunk scoring zero."""
    hits = query.retrieve_keyword("zzzxqvwk nonexistent gibberish", k=10)
    assert hits == []


def test_keyword_retrieval_respects_k():
    """Never return more than k results."""
    hits = query.retrieve_keyword("show", k=3)
    assert len(hits) <= 3


def test_merge_deduplicates_by_id():
    """The merged candidate set must contain no duplicate point ids,
    even though a chunk can surface in both semantic and keyword paths."""
    candidates = query.merge_candidates("Richard Osman quiz show", candidate_k=10)
    ids = [c.id for c in candidates]
    assert len(ids) == len(set(ids))


def test_rerank_respects_top_k():
    """Reranking must never return more than top_k results."""
    candidates = query.merge_candidates("Richard Osman quiz show", candidate_k=10)
    reranked = query.rerank("Richard Osman quiz show", candidates, top_k=3)
    assert len(reranked) <= 3


def test_rerank_handles_empty_candidates():
    """Reranking an empty candidate set returns an empty list, not an error."""
    assert query.rerank("anything", [], top_k=3) == []


def test_retrieve_end_to_end_returns_top_k():
    """The full hybrid retrieve should return at most k source-attributed hits."""
    hits = query.retrieve("Richard Osman quiz show", k=3)
    assert len(hits) <= 3
    for hit in hits:
        assert "text" in hit.payload
        assert "source" in hit.payload


def test_build_context_formats_sources():
    """build_context must wrap every chunk with its source marker."""
    hits = query.retrieve("Richard Osman quiz show", k=2)
    context = query.build_context(hits)
    assert "[Source:" in context