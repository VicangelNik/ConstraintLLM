from __future__ import annotations


def tag_based_retrieval(query_tags: list[str], problems: list[dict], topk: int = 4) -> list[dict]:
    """Perform simple retrieval based on tag overlap."""
    query_set = set(query_tags)
    scored_items = []
    for item in problems:
        item_tags = set(item.get("constraints", []))
        overlap = len(query_set & item_tags)
        coverage = overlap / len(query_set) if query_set else 0.0
        score = (-overlap, -coverage, len(item_tags), item.get("name", ""))
        scored_items.append((score, item))
    scored_items.sort(key=lambda pair: pair[0])
    return [pair[1] for pair in scored_items[:topk]]
