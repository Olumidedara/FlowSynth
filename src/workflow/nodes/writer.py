from src.llm import call_llm
from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState

SYSTEM_PROMPT = """You are a professional content writer. Based on the research and analysis provided,
write a well-structured article with:
1. An engaging introduction
2. Well-organized body sections with headings
3. A concise conclusion
4. Clear, accessible language

If this is a revision, carefully address all feedback from the reviewer."""


def writer_node(state: FlowSynthState) -> dict:
    rev = state.get("revision_count", 0)
    stage = "Revising article..." if rev > 0 else "Writing article..."
    set_stage(state.get("_task_id", ""), stage)

    feedback_context = ""
    if state.get("review_feedback"):
        feedback_context = f"\n\nPrevious reviewer feedback to address:\n{state['review_feedback']}"

    draft = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Query: {state['query']}\n\nResearch plan:\n{state.get('research_plan', '')}\n\nAnalysis:\n{state.get('analysis', '')}\n\nSearch results:\n" + "\n".join(
            f"- {r['title']}: {r['snippet']}" for r in state.get("search_results", [])
        ) + feedback_context,
    )
    return {"draft": draft}
