from langgraph.graph import StateGraph, END

from src.workflow.state import FlowSynthState
from src.workflow.nodes.orchestrator import orchestrator_node
from src.workflow.nodes.researcher import researcher_node
from src.workflow.nodes.analyst import analyst_node
from src.workflow.nodes.writer import writer_node
from src.workflow.nodes.reviewer import reviewer_node
from src.workflow.nodes.finalizer import finalizer_node

MAX_REVISIONS = 3


def review_router(state: FlowSynthState) -> str:
    score = state.get("review_score", 0)
    revisions = state.get("revision_count", 0)
    if score >= 7 or revisions >= MAX_REVISIONS:
        return "finalizer"
    return "writer"


def build_graph() -> StateGraph:
    builder = StateGraph(FlowSynthState)

    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("writer", writer_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("finalizer", finalizer_node)

    builder.set_entry_point("orchestrator")

    builder.add_edge("orchestrator", "researcher")
    builder.add_edge("researcher", "analyst")
    builder.add_edge("analyst", "writer")
    builder.add_edge("writer", "reviewer")

    builder.add_conditional_edges(
        "reviewer",
        review_router,
        {"finalizer": "finalizer", "writer": "writer"},
    )

    builder.add_edge("finalizer", END)

    return builder.compile()


flowsynth_graph = build_graph()
