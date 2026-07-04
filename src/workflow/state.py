from typing import TypedDict, List


class SearchResult(TypedDict):
    title: str
    snippet: str
    url: str


class FlowSynthState(TypedDict):
    query: str
    research_plan: str
    search_results: List[SearchResult]
    analysis: str
    draft: str
    review_score: int
    review_feedback: str
    revision_count: int
    final_output: str
    errors: List[str]
    _task_id: str
