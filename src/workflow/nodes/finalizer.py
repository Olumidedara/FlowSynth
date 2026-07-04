from src.llm import call_llm
from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState

SYSTEM_PROMPT = """You are a content finalizer. Polish the article into its final form.
Ensure formatting is clean, consistent, and ready for presentation.
Add a brief summary at the top."""


def finalizer_node(state: FlowSynthState) -> dict:
    set_stage(state.get("_task_id", ""), "Finalizing output...")
    final = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Query: {state['query']}\n\nDraft:\n{state.get('draft', '')}\n\nReview feedback: {state.get('review_feedback', '')}",
        temperature=0.4,
    )
    return {"final_output": final}
