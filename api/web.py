"""Server-rendered app pages and read endpoints."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from html import escape
import os
from pathlib import Path
from typing import TypeVar, Any, Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Form, HTTPException, Query, Request, BackgroundTasks, Response, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone, timedelta
from markupsafe import Markup

from aideator.paths import ensure_dir, get_all_paths, get_report_path_for_idea
from api.config import settings
from db.ideas import get_idea, list_ideas, save_idea
from db.reports import get_report, list_reports
from engine.orchestrator import execute_run
from engine.exporter import ReportExporter
from engine.forge import forge_concept_file
from db.comments import list_comments_for_idea, add_comment, Comment
from api.sharing import generate_share_link, validate_share_hash
from db.runs import get_run, list_runs, list_runs_for_idea, save_run
from models.idea import Idea
from models.run import Run, RunMode, RunTier

router = APIRouter(tags=["web"])

_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(_ROOT / "templates"))
_DOCS_DIR = settings.app_docs_dir

from api.settings_manager import (
    get_settings as get_persistent_settings,
    update_settings as update_persistent_settings,
)


class ForgeRequest(BaseModel):
    idea_id: UUID


@dataclass
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





def _render_markdown(markdown_text: str) -> str:
    import markdown
    # Use standard extensions for better formatting
    return markdown.markdown(markdown_text, extensions=["extra", "nl2br", "sane_lists"])


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
        duration_str = "—"
        if run.duration_ms:
            if run.duration_ms < 1000:
                duration_str = f"{run.duration_ms}ms"
            else:
                duration_str = f"{run.duration_ms / 1000:.1f}s"
        
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
                "duration": duration_str,
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
    return get_persistent_settings()


@router.put("/settings")
def update_settings(payload: dict[str, str | bool]) -> dict[str, str | bool]:
    return update_persistent_settings(payload)


@router.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


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
    artifact_path = get_report_path_for_idea(idea_id)
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
    """Shared template context for all server-rendered pages."""
    # Basic health check for context (Mocked for now, but ready for expansion)
    health = {"ollama": True, "duckduckgo": True, "tavily": False}
    
    return {
        "request": request,
        "page_title": page_title,
        "active_path": request.url.path,
        "current_mode": str(get_persistent_settings()["default_mode"]),
        "health": health,
    }


@router.get("/app/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    
    runs_last_24h = [r for r in list_runs() if r.created_at > day_ago]
    failed_last_24h = [r for r in runs_last_24h if r.status == "failed"]

    idea_rows = _idea_rows()
    run_rows = _run_rows()
    context = _base_context(request, "Dashboard")
    context.update(
        {
            "summary_ideas_count": len(idea_rows),
            "summary_runs_last_24h": len(runs_last_24h),
            "summary_runs_failed_last_24h": len(failed_last_24h),
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
            "default_mode": str(get_persistent_settings()["default_mode"]),
        }
    )
    return templates.TemplateResponse(request=request, name="idea_detail.html", context=context)


@router.post("/app/runs/create")
def create_run_from_form(
    background_tasks: BackgroundTasks,
    idea_id: UUID = Form(...),
    mode: RunMode = Form(...),
    tier: RunTier = Form(...),
) -> RedirectResponse:
    run = Run(idea_id=idea_id, mode=mode, tier=tier)
    save_run(run)
    background_tasks.add_task(execute_run, run.run_id)
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
    artifact_path = get_report_path_for_idea(run.idea_id)
    cards = report.cards if report else []
    findings = cards
    citations = report.citations if report else []
    
    # Confidence / Intensity calculation
    confidence_score = 0
    if run.status == "succeeded" and report:
        # Heuristic: base 60% + cards count + citation count
        confidence_score = min(98, 60 + (len(cards) * 5) + (len(citations) * 2))
    elif run.status == "failed":
        confidence_score = 0

    duration_str = "—"
    if run.duration_ms:
        if run.duration_ms < 1000:
            duration_str = f"{run.duration_ms}ms"
        else:
            duration_str = f"{run.duration_ms / 1000:.1f}s"

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
                "duration": duration_str,
                "error_code": run.error_code,
                "error_message": "Internal processing error or provider timeout." if run.error_code else "",
                "confidence_score": confidence_score,
            },
            "findings": findings,
            "citations": citations,
            "docs_available": artifact_path.exists(),
            "docs_url": f"/app/reports/{run.idea_id}",
            "mode_disclosure": _mode_disclosure(run.mode),
        }
    )
    return templates.TemplateResponse(request=request, name="run_detail.html", context=context)


@router.get("/app/reports", response_class=HTMLResponse)
def reports_page(request: Request, q: str = Query(default="")) -> HTMLResponse:
    report_rows = list_report_docs()["items"]
    if not isinstance(report_rows, list):
        report_rows = []
    
    if q:
        q_lower = q.lower()
        report_rows = [row for row in report_rows if q_lower in row["idea_title"].lower()]

    # Enrich report rows for the template
    for row in report_rows:
        row["source"] = "NEXUS_CORE"  # Default source for UI consistency
    
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
    return templates.TemplateResponse(request=request, name="reports_list.html", context=context)


@router.get("/app/reports/{idea_id}", response_class=HTMLResponse)
def reports_for_idea_page(request: Request, idea_id: UUID) -> HTMLResponse:
    idea = get_idea(idea_id)
    doc_payload = get_report_doc(idea_id)
    
    # Find latest successful run to extract stats
    runs = list_runs_for_idea(idea_id)
    success_runs = [r for r in runs if r.status == "succeeded"]
    latest_run = max(success_runs, key=lambda r: r.updated_at, default=None)
    
    launcher_data = {
        "title": idea.title if idea else "Unknown Concept",
        "description": idea.description if idea else "",
        "demand_score": "N/A",
        "demand_summary": "Ready for initial development.",
        "brand_hex": idea.brand_hex if idea else "#888888",
        "tier": idea.tier if idea else "Bronze",
    }
    
    if latest_run:
        report = get_report(latest_run.run_id)
        if report:
            for card in report.cards:
                if card.get("type") == "demand":
                    launcher_data["demand_score"] = str(card.get("score", "N/A"))
                    launcher_data["demand_summary"] = card.get("summary", launcher_data["demand_summary"])

    # Construct a rich report object for report_detail.html
    report_ui = {
        "id": str(idea_id),
        "title": idea.title if idea else "Unknown Idea",
        "created_at": _fmt_ts(latest_run.updated_at) if latest_run else "RECENT_SYNC",
        "summary": "Intelligence synthesis complete. Nexus engine provides high-confidence analysis.",
        "content": _render_markdown(doc_payload["markdown"])
    }
    
    context = _base_context(request, "Report Detail")
    context.update(
        {
            "report": report_ui,
            "launcher_data": launcher_data,
            "comments": list_comments_for_idea(idea_id),
        }
    )
    return templates.TemplateResponse(request=request, name="report_detail.html", context=context)


@router.get("/app/reports/{idea_id}/pdf")
def export_report_pdf(idea_id: UUID) -> Response:
    idea = get_idea(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Find latest successful run
    runs = list_runs_for_idea(idea_id)
    success_runs = [r for r in runs if r.status == "succeeded"]
    latest_run = max(success_runs, key=lambda r: r.updated_at, default=None)
    
    if not latest_run:
        raise HTTPException(status_code=400, detail="No successful runs found for this idea.")
    
    report = get_report(latest_run.run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report data not found")

    # Read markdown from artifact path
    artifact_path = get_report_path_for_idea(idea_id)
    content = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else "No synthesized content available."
    
    exporter = ReportExporter()
    pdf_bytes = exporter.generate_pdf(
        idea_title=idea.title,
        idea_description=idea.description,
        report_content=content,
        cards=report.cards,
        citations=report.citations
    )
    
    filename = f"AIdeator_Report_{idea.title.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/app/reports/{idea_id}/comments")
def post_comment(idea_id: UUID, content: str = Form(...), author: str = Form("System_User")) -> RedirectResponse:
    add_comment(Comment(idea_id=idea_id, author=author, content=content))
    return RedirectResponse(f"/app/reports/{idea_id}", status_code=303)


@router.post("/app/reports/{idea_id}/share")
def create_share(idea_id: UUID) -> dict[str, str]:
    share_hash = generate_share_link(idea_id)
    return {"share_url": f"/shared/{share_hash}"}


@router.post("/api/forge")
@router.post("/app/reports/{idea_id}/forge")
def forge_local(idea_id: Optional[UUID] = None, body: dict = Body(None)) -> dict[str, Any]:
    # Extract idea_id from path or body
    raw_id = idea_id or (body.get("idea_id") if body else None)
    
    if not raw_id:
        raise HTTPException(status_code=422, detail="Missing idea_id")

    # Ensure it's a UUID
    try:
        effective_id = UUID(str(raw_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid idea_id format")

    idea = get_idea(effective_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Find latest successful run
    runs = list_runs_for_idea(effective_id)
    success_runs = [r for r in runs if r.status == "succeeded"]
    latest_run = max(success_runs, key=lambda r: r.updated_at, default=None)
    
    if not latest_run:
        raise HTTPException(status_code=400, detail="No successful runs found for this idea.")
    
    report = get_report(latest_run.run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report data not found")

    # Read markdown from artifact path
    artifact_path = get_report_path_for_idea(effective_id)
    content = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else "No synthesized content available."
    
    demand_score = "N/A"
    demand_summary = "Ready for initial development."
    for card in report.cards:
        if card.get("type") == "demand":
            demand_score = str(card.get("score", "N/A"))
            demand_summary = card.get("summary", demand_summary)

    abs_path = forge_concept_file(
        idea_title=idea.title,
        demand_score=demand_score,
        demand_summary=demand_summary,
        report_content=content,
        root_dir="."
    )
    
    return {
        "status": "success", 
        "success": True,
        "file": str(abs_path),
        "message": "concept.md generated successfully"
    }


@router.get("/shared/{share_hash}", response_class=HTMLResponse)
def view_shared_report(request: Request, share_hash: str) -> HTMLResponse:
    idea_id = validate_share_hash(share_hash)
    if not idea_id:
        raise HTTPException(status_code=404, detail="Shared link expired or invalid.")
    
    idea = get_idea(idea_id)
    doc_payload = get_report_doc(idea_id)
    
    report_ui = {
        "id": str(idea_id),
        "title": idea.title if idea else "Shared Intelligence",
        "created_at": "SYNCHRONIZED_VAULT",
        "summary": "This is a read-only shared view of an AIdeator intelligence report.",
        "content": _render_markdown(doc_payload["markdown"])
    }
    
    context = _base_context(request, f"Shared Report: {report_ui['title']}")
    context.update({
        "report": report_ui,
        "is_shared_view": True,
        "launcher_data": {"brand_hex": idea.brand_hex, "tier": idea.tier} if idea else {}
    })
    # We use the same template but with a 'shared' flag to hide interactions
    return templates.TemplateResponse(request=request, name="report_detail.html", context=context)
@router.get("/app/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    context = _base_context(request, "Settings")
    context.update({"settings": get_persistent_settings()})
    return templates.TemplateResponse(request=request, name="settings.html", context=context)


@router.post("/app/settings")
def update_settings_from_form(
    default_mode: str = Form(...),
    allow_cloud: str = Form("false"),
    telemetry_enabled: str = Form("false"),
) -> RedirectResponse:
    update_persistent_settings({
        "default_mode": default_mode,
        "allow_cloud": allow_cloud == "true",
        "telemetry_enabled": telemetry_enabled == "true",
    })
    return RedirectResponse("/app/settings", status_code=303)


@router.get("/app/diagnostics", response_class=HTMLResponse)
def diagnostics_page(request: Request) -> HTMLResponse:
    context = _base_context(request, "Diagnostics")
    context.update({"diagnostics": get_diagnostics()})
    return templates.TemplateResponse(request=request, name="diagnostics.html", context=context)
