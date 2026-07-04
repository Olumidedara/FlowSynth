from src.llm import call_llm
from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState

SYSTEM_PROMPT = """You are a data analyst. Examine the research findings and extract:
1. Key insights and patterns
2. Contradictions or gaps in information
3. The most important takeaways
4. Connections between subtopics
Provide a structured analysis that will inform content creation."""


def analyst_node(state: FlowSynthState) -> dict:
    set_stage(state.get("_task_id", ""), "Analyzing research findings...")
    findings = "\n".join(
        f"Title: {r['title']}\n{r['snippet']}"
        for r in state.get("search_results", [])
    )
    analysis = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Query: {state['query']}\n\nResearch plan:\n{state.get('research_plan', '')}\n\nFindings:\n{findings}",
    )
    return {"analysis": analysis}
