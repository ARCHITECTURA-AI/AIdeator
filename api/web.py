"""Server-rendered app pages and read endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.config import settings
from db.ideas import get_idea, list_ideas, save_idea
from db.reports import get_report, list_reports
from db.runs import get_run, list_runs, list_runs_for_idea, save_run
from engine.orchestrator import start_run
from models.idea import Idea
from models.run import Run, RunMode, RunTier

router = APIRouter(tags=["web"])

_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(_ROOT / "templates"))
_DOCS_DIR = settings.app_docs_dir

_SETTINGS: dict[str, str | bool] = {
    "default_mode": settings.app_default_mode,
    "allow_cloud": False,
    "telemetry_enabled": False,
    "api_keys_configured": False,
}


@dataclass(slots=True)
class Pagination:
    page: int
    pages: int
    has_prev: bool
    has_next: bool
    prev_page: int
    next_page: int


def _fmt_ts(value: object) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M UTC")
    return str(value)


def _mode_label(mode: str) -> str:
    return mode.replace("-", " ").title()


def _mode_disclosure(mode: str) -> str:
    return {
        "local-only": "No outbound network calls are allowed in this run.",
        "hybrid": "Outbound calls are restricted to keyword-only payloads.",
        "cloud-enabled": "Outbound providers may receive richer run context.",
    }[mode]


T = TypeVar("T")


def _paginate(items: list[T], page: int, per_page: int) -> tuple[list[T], Pagination]:
    total = len(items)
    pages = max((total + per_page - 1) // per_page, 1)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    end = start + per_page
    return (
        items[start:end],
        Pagination(
            page=page,
            pages=pages,
            has_prev=page > 1,
            has_next=page < pages,
            prev_page=max(1, page - 1),
            next_page=min(pages, page + 1),
        ),
    )


def _report_path_for_idea(idea_id: UUID) -> Path:
    return _DOCS_DIR / f"idea-{idea_id}.md"


def _render_markdown(markdown_text: str) -> str:
    # Keep rendering dependency-free while preserving readability.
    return "<pre class='markdown-pre'>" + escape(markdown_text) + "</pre>"


def _idea_rows() -> list[dict[str, object]]:
    runs = list_runs()
    runs_by_idea: dict[UUID, list[Run]] = {}
    for run in runs:
        runs_by_idea.setdefault(run.idea_id, []).append(run)

    rows: list[dict[str, object]] = []
    for idea in list_ideas():
        idea_runs = runs_by_idea.get(idea.idea_id, [])
        last_run = max(idea_runs, key=lambda item: item.created_at, default=None)
        rows.append(
            {
                "id": str(idea.idea_id),
                "title": idea.title,
                "description": idea.description,
                "target_user": idea.target_user,
                "context": idea.context,
                "created_at": _fmt_ts(idea.created_at),
                "runs_count": len(idea_runs),
                "last_run_status": last_run.status if last_run else "pending",
            }
        )
    rows.sort(key=lambda item: str(item["created_at"]), reverse=True)
    return rows


def _run_rows(*, idea_filter: UUID | None = None) -> list[dict[str, object]]:
    idea_title_map = {idea.idea_id: idea.title for idea in list_ideas()}
    source = list_runs_for_idea(idea_filter) if idea_filter else list_runs()
    rows: list[dict[str, object]] = []
    for run in source:
        rows.append(
            {
                "id": str(run.run_id),
                "idea_id": str(run.idea_id),
                "idea_title": idea_title_map.get(run.idea_id, "Unknown idea"),
                "status": run.status,
                "mode": run.mode,
                "mode_label": _mode_label(run.mode),
                "tier": run.tier,
                "created_at": _fmt_ts(run.created_at),
                "updated_at": _fmt_ts(run.updated_at),
                "duration": "n/a",
                "error_code": run.error_code,
            }
        )
    rows.sort(key=lambda item: str(item["created_at"]), reverse=True)
    return rows


@router.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse("/app/dashboard", status_code=302)


@router.get("/app", include_in_schema=False)
def app_root_redirect() -> RedirectResponse:
    return RedirectResponse("/app/dashboard", status_code=302)


@router.get("/settings")
def get_settings() -> dict[str, str | bool]:
    return _SETTINGS


@router.put("/settings")
def update_settings(payload: dict[str, str | bool]) -> dict[str, str | bool]:
    for key, value in payload.items():
        if key in _SETTINGS:
            _SETTINGS[key] = value
    return _SETTINGS


@router.get("/diagnostics")
def get_diagnostics() -> dict[str, object]:
    return {
        "status": "ok",
        "ideas_count": len(list_ideas()),
        "runs_count": len(list_runs()),
        "reports_count": len(list_reports()),
    }


@router.get("/ideas")
def get_ideas(
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    rows = _idea_rows()
    if q:
        q_lower = q.lower()
        rows = [item for item in rows if q_lower in str(item["title"]).lower()]
    paged, pagination = _paginate(rows, page, per_page)
    return {
        "items": paged,
        "pagination": pagination.__dict__,
        "total": len(rows),
    }


@router.get("/ideas/{idea_id}")
def get_idea_by_id(idea_id: UUID) -> dict[str, object]:
    idea = get_idea(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {
        "id": str(idea.idea_id),
        "title": idea.title,
        "description": idea.description,
        "target_user": idea.target_user,
        "context": idea.context,
        "created_at": _fmt_ts(idea.created_at),
        "runs": _run_rows(idea_filter=idea_id),
    }


@router.get("/runs")
def get_runs(
    status: str = Query(default=""),
    mode: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    rows = _run_rows()
    if status:
        rows = [item for item in rows if item["status"] == status]
    if mode:
        rows = [item for item in rows if item["mode"] == mode]
    paged, pagination = _paginate(rows, page, per_page)
    return {
        "items": paged,
        "pagination": pagination.__dict__,
        "total": len(rows),
    }


@router.get("/runs/{run_id}")
def get_run_detail(run_id: UUID) -> dict[str, object]:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    idea = get_idea(run.idea_id)
    report = get_report(run_id)
    return {
        "id": str(run.run_id),
        "idea_id": str(run.idea_id),
        "idea_title": idea.title if idea else "Unknown idea",
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "created_at": _fmt_ts(run.created_at),
        "updated_at": _fmt_ts(run.updated_at),
        "error_code": run.error_code,
        "cards": report.cards if report else [],
        "artifact_path": report.artifact_path if report else f"docs/idea-{run.idea_id}.md",
    }


@router.get("/report-docs")
def list_report_docs() -> dict[str, object]:
    idea_map = {idea.idea_id: idea for idea in list_ideas()}
    docs = []
    for report in list_reports():
        run = get_run(report.run_id)
        if run is None:
            continue
        idea = idea_map.get(run.idea_id)
        docs.append(
            {
                "idea_id": str(run.idea_id),
                "idea_title": idea.title if idea else "Unknown idea",
                "artifact_path": report.artifact_path,
            }
        )
    return {"items": docs}


@router.get("/report-docs/{idea_id}")
def get_report_doc(idea_id: UUID) -> dict[str, str]:
    artifact_path = _report_path_for_idea(idea_id)
    markdown = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""
    try:
        artifact_display = str(artifact_path.relative_to(_ROOT))
    except ValueError:
        artifact_display = str(artifact_path)
    return {
        "idea_id": str(idea_id),
        "artifact_path": artifact_display,
        "markdown": markdown,
    }


def _base_context(request: Request, page_title: str) -> dict[str, object]:
    return {
        "request": request,
        "page_title": page_title,
        "active_path": request.url.path,
        "current_mode": str(_SETTINGS["default_mode"]),
    }


@router.get("/app/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    idea_rows = _idea_rows()
    run_rows = _run_rows()
    context = _base_context(request, "Dashboard")
    context.update(
        {
            "summary_ideas_count": len(idea_rows),
            "summary_runs_last_24h": len(run_rows),
            "summary_runs_failed_last_24h": len(
                [row for row in run_rows if row["status"] == "failed"]
            ),
            "recent_ideas": idea_rows[:5],
            "recent_runs": run_rows[:5],
        }
    )
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


@router.get("/app/ideas", response_class=HTMLResponse)
def ideas_page(
    request: Request,
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
) -> HTMLResponse:
    idea_rows = _idea_rows()
    if q:
        q_lower = q.lower()
        idea_rows = [item for item in idea_rows if q_lower in str(item["title"]).lower()]
    paged, pagination = _paginate(idea_rows, page, 20)
    context = _base_context(request, "Ideas")
    context.update({"ideas": paged, "query": q, "pagination": pagination})
    return templates.TemplateResponse(request=request, name="ideas_list.html", context=context)


@router.get("/app/ideas/new", response_class=HTMLResponse)
def new_idea_page(request: Request) -> HTMLResponse:
    context = _base_context(request, "New Idea")
    return templates.TemplateResponse(request=request, name="idea_new.html", context=context)


@router.post("/app/ideas/new")
def create_idea_from_form(
    title: str = Form(...),
    description: str = Form(...),
    target_user: str = Form(...),
    context: str = Form(""),
) -> RedirectResponse:
    idea = Idea(title=title, description=description, target_user=target_user, context=context)
    save_idea(idea)
    return RedirectResponse(f"/app/ideas/{idea.idea_id}", status_code=303)


@router.get("/app/ideas/{idea_id}", response_class=HTMLResponse)
def idea_detail_page(request: Request, idea_id: UUID) -> HTMLResponse:
    idea = get_idea(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    context = _base_context(request, "Idea Detail")
    context.update(
        {
            "idea": {
                "id": str(idea.idea_id),
                "title": idea.title,
                "description": idea.description,
                "target_user": idea.target_user,
                "context": idea.context,
                "created_at": _fmt_ts(idea.created_at),
            },
            "runs": _run_rows(idea_filter=idea_id),
            "available_modes": ["local-only", "hybrid", "cloud-enabled"],
            "default_mode": str(_SETTINGS["default_mode"]),
        }
    )
    return templates.TemplateResponse(request=request, name="idea_detail.html", context=context)


@router.post("/app/runs/create")
def create_run_from_form(
    idea_id: UUID = Form(...),
    mode: RunMode = Form(...),
    tier: RunTier = Form(...),
) -> RedirectResponse:
    run = Run(idea_id=idea_id, mode=mode, tier=tier)
    save_run(run)
    start_run(run.run_id)
    return RedirectResponse(f"/app/runs/{run.run_id}", status_code=303)


@router.get("/app/runs", response_class=HTMLResponse)
def runs_page(
    request: Request,
    status: str = Query(default=""),
    mode: str = Query(default=""),
    page: int = Query(default=1, ge=1),
) -> HTMLResponse:
    run_rows = _run_rows()
    if status:
        run_rows = [item for item in run_rows if item["status"] == status]
    if mode:
        run_rows = [item for item in run_rows if item["mode"] == mode]
    paged, pagination = _paginate(run_rows, page, 20)
    context = _base_context(request, "Runs")
    context.update(
        {"runs": paged, "filters": {"status": status, "mode": mode}, "pagination": pagination}
    )
    return templates.TemplateResponse(request=request, name="runs_list.html", context=context)


@router.get("/app/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(request: Request, run_id: UUID) -> HTMLResponse:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    idea = get_idea(run.idea_id)
    report = get_report(run_id)
    artifact_path = _report_path_for_idea(run.idea_id)
    cards = report.cards if report else []
    context = _base_context(request, f"Run {run_id}")
    context.update(
        {
            "run": {
                "id": str(run.run_id),
                "idea_id": str(run.idea_id),
                "idea_title": idea.title if idea else "Unknown idea",
                "status": run.status,
                "mode": run.mode,
                "mode_label": _mode_label(run.mode),
                "tier": run.tier,
                "queued_at": _fmt_ts(run.created_at),
                "started_at": _fmt_ts(run.created_at),
                "finished_at": (
                    _fmt_ts(run.updated_at) if run.status in {"succeeded", "failed"} else "—"
                ),
                "duration": "n/a",
                "error_code": run.error_code,
                "error_message": "Dependency timeout or provider error." if run.error_code else "",
            },
            "cards": cards,
            "signals": [],
            "docs_available": artifact_path.exists(),
            "docs_url": f"/app/reports/{run.idea_id}",
            "mode_disclosure": _mode_disclosure(run.mode),
        }
    )
    return templates.TemplateResponse(request=request, name="run_detail.html", context=context)


@router.get("/app/reports", response_class=HTMLResponse)
def reports_page(request: Request) -> HTMLResponse:
    report_rows = list_report_docs()["items"]
    if not isinstance(report_rows, list):
        report_rows = []
    selected_idea_id = report_rows[0]["idea_id"] if report_rows else None
    selected_doc = ""
    if selected_idea_id is not None:
        selected_doc = get_report_doc(UUID(str(selected_idea_id)))["markdown"]

    context = _base_context(request, "Reports")
    context.update(
        {
            "docs": report_rows,
            "selected_idea_id": selected_idea_id,
            "selected_doc_html": _render_markdown(selected_doc) if selected_doc else "",
        }
    )
    return templates.TemplateResponse(request=request, name="reports_browser.html", context=context)


@router.get("/app/reports/{idea_id}", response_class=HTMLResponse)
def reports_for_idea_page(request: Request, idea_id: UUID) -> HTMLResponse:
    report_rows = list_report_docs()["items"]
    if not isinstance(report_rows, list):
        report_rows = []
    doc_payload = get_report_doc(idea_id)
    context = _base_context(request, "Reports")
    context.update(
        {
            "docs": report_rows,
            "selected_idea_id": str(idea_id),
            "selected_doc_html": _render_markdown(doc_payload["markdown"]),
        }
    )
    return templates.TemplateResponse(request=request, name="reports_browser.html", context=context)


@router.get("/app/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    context = _base_context(request, "Settings")
    context.update({"settings": _SETTINGS})
    return templates.TemplateResponse(request=request, name="settings.html", context=context)


@router.post("/app/settings")
def update_settings_from_form(
    default_mode: str = Form(...),
    allow_cloud: str = Form("false"),
    telemetry_enabled: str = Form("false"),
) -> RedirectResponse:
    _SETTINGS["default_mode"] = default_mode
    _SETTINGS["allow_cloud"] = allow_cloud == "true"
    _SETTINGS["telemetry_enabled"] = telemetry_enabled == "true"
    return RedirectResponse("/app/settings", status_code=303)


@router.get("/app/diagnostics", response_class=HTMLResponse)
def diagnostics_page(request: Request) -> HTMLResponse:
    context = _base_context(request, "Diagnostics")
    context.update({"diagnostics": get_diagnostics()})
    return templates.TemplateResponse(request=request, name="diagnostics.html", context=context)
