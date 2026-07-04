from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS(timeout=10) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
            for r in results
        ]
    except Exception as e:
        return [{"title": "Search failed", "snippet": str(e), "url": ""}]
