"""File download endpoints for completed sessions."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.session_manager import session_manager
from exports.markdown_exporter import MarkdownExporter
from exports.json_exporter import JSONExporter
from exports.docx_exporter import DocxExporter

router = APIRouter()
_md   = MarkdownExporter()
_json = JSONExporter()
_docx = DocxExporter()

DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ── Shared helpers ────────────────────────────────────────────────────────────

def _require_session_result(session_id: str):
    status = session_manager.get_status(session_id)
    if status == "not_found":
        raise HTTPException(404, f"Session '{session_id}' not found")
    if status != "complete":
        raise HTTPException(409, f"Session '{session_id}' is not yet complete (status: {status})")
    mgr = session_manager.get_result(session_id)
    if mgr is None:
        raise HTTPException(500, "Result missing despite complete status")
    return mgr


def _require_best_group_result(session_id: str):
    mgr = _require_session_result(session_id)
    return mgr.groups[mgr.overall_best_group_index]


def _require_group_result(session_id: str, group_idx: int):
    mgr = _require_session_result(session_id)
    if group_idx >= len(mgr.groups):
        raise HTTPException(404, f"Group {group_idx} not found (session has {len(mgr.groups)} group(s))")
    return mgr.groups[group_idx]


# ── Existing markdown / JSON / ZIP exports (best group) ──────────────────────

@router.get("/{session_id}/export/markdown")
async def export_markdown(session_id: str):
    result = _require_best_group_result(session_id)
    path = _md.export(result)
    return FileResponse(path=str(path), media_type="text/markdown", filename=f"{session_id}_report.md")


@router.get("/{session_id}/export/policy")
async def export_final_policy(session_id: str):
    result = _require_best_group_result(session_id)
    path = _md.export_final_policy(result)
    return FileResponse(path=str(path), media_type="text/markdown", filename=f"{session_id}_final_policy.md")


@router.get("/{session_id}/export/json")
async def export_json(session_id: str):
    result = _require_best_group_result(session_id)
    path = _json.export(result)
    return FileResponse(path=str(path), media_type="application/json", filename=f"{session_id}_export.json")


@router.get("/{session_id}/export/versions")
async def export_all_versions(session_id: str):
    """Returns a zip of all per-version markdown files from the best group."""
    import zipfile, io
    result = _require_best_group_result(session_id)
    paths = _md.export_all_versions(result)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            zf.write(p, p.name)
    buf.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{session_id}_versions.zip"'},
    )


# ── Per-group Word (.docx) exports ────────────────────────────────────────────

@router.get("/{session_id}/export/group/{group_idx}/final/docx")
async def export_group_final_docx(session_id: str, group_idx: int):
    """Final document for a specific generator group as .docx."""
    result = _require_group_result(session_id, group_idx)
    path = _docx.export_final(result)
    fn = f"{session_id}_gen{group_idx + 1}_final.docx"
    return FileResponse(path=str(path), media_type=DOCX_MEDIA, filename=fn)


@router.get("/{session_id}/export/group/{group_idx}/iter/{iter_num}/draft/docx")
async def export_iter_draft_docx(session_id: str, group_idx: int, iter_num: int):
    """Draft document for a specific iteration of a generator group as .docx."""
    result = _require_group_result(session_id, group_idx)
    try:
        path = _docx.export_iteration_draft(result, iter_num)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    fn = f"{session_id}_gen{group_idx + 1}_iter{iter_num}_draft.docx"
    return FileResponse(path=str(path), media_type=DOCX_MEDIA, filename=fn)


@router.get("/{session_id}/export/group/{group_idx}/iter/{iter_num}/reviews/docx")
async def export_iter_reviews_docx(session_id: str, group_idx: int, iter_num: int):
    """All reviewer comments for a specific iteration as .docx."""
    result = _require_group_result(session_id, group_idx)
    try:
        path = _docx.export_iteration_reviews(result, iter_num)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    fn = f"{session_id}_gen{group_idx + 1}_iter{iter_num}_reviews.docx"
    return FileResponse(path=str(path), media_type=DOCX_MEDIA, filename=fn)
