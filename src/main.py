import uuid
import asyncio
from pathlib import Path

import markdown
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.auth import router as auth_router, get_current_user
from src.database import init_db, create_research, update_research, get_research_history, get_research_by_id, get_research_by_task_id, get_latest_research, delete_research
from src.workflow.graph import flowsynth_graph
from src.workflow.progress import clear_stage


def render_md(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "sane_lists"],
    )


app = FastAPI(title="FlowSynth")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth_router)

tasks: dict[str, dict] = {}
_lock = asyncio.Lock()


WORKFLOW_TIMEOUT = 120


async def run_workflow(task_id: str, query: str, research_id: int | None = None) -> None:
    try:
        initial_state = {
            "query": query,
            "research_plan": "",
            "search_results": [],
            "analysis": "",
            "draft": "",
            "review_score": 0,
            "review_feedback": "",
            "revision_count": 0,
            "final_output": "",
            "errors": [],
            "_task_id": task_id,
        }

        result = await asyncio.wait_for(
            asyncio.to_thread(flowsynth_graph.invoke, initial_state),
            timeout=WORKFLOW_TIMEOUT,
        )

        text_fields = {
            "research_plan", "analysis", "draft",
            "review_feedback", "final_output",
        }
        r = {}
        for field in text_fields:
            val = result.get(field, "")
            r[field] = val
            r[f"{field}_html"] = render_md(val)
        r["query"] = result.get("query", query)
        r["review_score"] = result.get("review_score", 0)
        r["revision_count"] = result.get("revision_count", 0)
        r["errors"] = result.get("errors", [])

        clear_stage(task_id)
        async with _lock:
            tasks[task_id] = {"status": "completed", "result": r}

        if research_id:
            update_research(research_id, "completed", r)

    except asyncio.TimeoutError:
        clear_stage(task_id)
        async with _lock:
            tasks[task_id] = {"status": "failed", "error": "Pipeline timed out after 120s"}
        if research_id:
            update_research(research_id, "failed")

    except Exception as e:
        clear_stage(task_id)
        async with _lock:
            tasks[task_id] = {"status": "failed", "error": str(e)}
        if research_id:
            update_research(research_id, "failed")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"api_key_configured": bool(settings.groq_api_key)},
    )


@app.post("/api/research")
async def start_research(query: str = Form(...), request: Request = None):
    task_id = str(uuid.uuid4())
    user = get_current_user(request)
    research_id = None
    if user:
        research_id = create_research(user["id"], query, task_id)

    async with _lock:
        tasks[task_id] = {"status": "running"}
    asyncio.create_task(run_workflow(task_id, query, research_id))
    return {"task_id": task_id}


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    from src.workflow.progress import get_stage
    async with _lock:
        task = tasks.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"status": "not_found"})
    stage = get_stage(task_id) if task["status"] == "running" else None
    return {"status": task["status"], "stage": stage, "error": task.get("error")}


@app.get("/api/result/{task_id}")
async def get_result(task_id: str, request: Request = None):
    from src.workflow.progress import get_stage
    async with _lock:
        task = tasks.get(task_id)
    if task:
        if task["status"] != "completed":
            stage = get_stage(task_id)
            return {"status": task["status"], "stage": stage}
        return task["result"]
    # DB fallback for historical results
    user = get_current_user(request)
    if user:
        row = get_research_by_task_id(task_id, user["id"])
        if row and row.get("result"):
            return row["result"]
    return JSONResponse(status_code=404, content={"status": "not_found"})


@app.get("/result/{task_id}", response_class=HTMLResponse)
async def result_page(request: Request, task_id: str):
    return templates.TemplateResponse(
        request,
        "result.html",
        {"task_id": task_id},
    )


@app.get("/api/history")
async def history(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    rows = get_research_history(user["id"])
    return {"history": rows}


@app.get("/api/research/{research_id}")
async def get_saved_research(research_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    row = get_research_by_id(research_id, user["id"])
    if not row:
        return JSONResponse(status_code=404, content={"error": "Research not found"})
    return row


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse(request, "result.html", {"task_id": ""})


@app.get("/auth/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse(request, "signin.html", {})


@app.get("/auth/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})


@app.delete("/api/research/{research_id}")
async def delete_saved_research(research_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    deleted = delete_research(research_id, user["id"])
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Research not found"})
    return {"ok": True}
