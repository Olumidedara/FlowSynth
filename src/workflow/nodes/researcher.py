from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState
from src.workflow.tools.search import search_web


def researcher_node(state: FlowSynthState) -> dict:
    set_stage(state.get("_task_id", ""), "Gathering web research...")
    plan = state.get("research_plan", state["query"])
    search_queries = [line for line in plan.split("\n") if line.strip() and "?" in line]
    if not search_queries:
        search_queries = [state["query"]]

    all_results = []
    for i, query in enumerate(search_queries[:4]):
        set_stage(state.get("_task_id", ""), f"Searching web ({i+1}/{min(len(search_queries), 4)})...")
        results = search_web(query.strip("- ").strip(), max_results=3)
        all_results.extend(results)

    return {"search_results": all_results[:10]}
