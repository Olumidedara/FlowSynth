import json

from src.llm import call_llm
from src.workflow.progress import set_stage
from src.workflow.state import FlowSynthState

SYSTEM_PROMPT = """You are a content quality reviewer. Evaluate the article on:
1. Accuracy - is the information correct and well-sourced?
2. Completeness - does it cover all key aspects of the query?
3. Structure - is it well-organized with clear sections?
4. Clarity - is it easy to read and understand?

Return ONLY a JSON object with these fields:
{
  "score": <integer 1-10>,
  "feedback": "<specific improvement suggestions>",
  "verdict": "<'pass' if score >= 7, else 'revise'>"
}"""


def reviewer_node(state: FlowSynthState) -> dict:
    set_stage(state.get("_task_id", ""), "Reviewing article quality...")
    revision_count = state.get("revision_count", 0)
    draft = state.get("draft", "")

    if not draft:
        return {"review_score": 7, "review_feedback": "No draft to review, proceeding.", "revision_count": revision_count}

    response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Query: {state['query']}\n\nDraft article:\n{draft}",
        temperature=0.3,
    )

    try:
        review = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        score = int(review.get("score", 5))
        feedback = review.get("feedback", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        score = 5
        feedback = "Review parsing failed, defaulting to revise."

    return {
        "review_score": score,
        "review_feedback": feedback,
        "revision_count": revision_count + 1,
    }
