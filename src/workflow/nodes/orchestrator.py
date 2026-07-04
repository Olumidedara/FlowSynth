from src.llm import call_llm
from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState

SYSTEM_PROMPT = """You are a research planning specialist. Given a user's query, create a structured research plan.
Break the query into 2-4 key subtopics that need to be investigated.
For each subtopic, provide 2-3 specific search questions.
Output only the research plan in a clear, numbered format."""


def orchestrator_node(state: FlowSynthState) -> dict:
    set_stage(state.get("_task_id", ""), "Planning research strategy...")
    plan = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Create a research plan for the following query:\n\n{state['query']}",
    )
    return {"research_plan": plan}
