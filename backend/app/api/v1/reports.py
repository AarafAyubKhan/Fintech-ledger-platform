"""
FinSight AI — Report Endpoints
View, generate, and export financial reports.
"""

import io

import structlog
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from uuid6 import uuid7

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import NotFoundException
from app.models.report import Report, ReportType
from app.schemas import ReportListResponse, ReportResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    user: CurrentUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
    report_type: str | None = None,
) -> ReportListResponse:
    """List all reports for the current user."""
    query = select(Report).where(Report.user_id == user.id)

    if report_type:
        query = query.where(Report.report_type == report_type)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = query.order_by(Report.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    user: CurrentUser,
    db: DBSession,
) -> ReportResponse:
    """Get a specific report by ID."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report", report_id)

    return ReportResponse.model_validate(report)


@router.get("/{report_id}/export/{format}")
async def export_report(
    report_id: str,
    format: str,
    user: CurrentUser,
    db: DBSession,
) -> StreamingResponse:
    """Export a report as PDF or DOCX."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report", report_id)

    from app.services.report_service import ReportExportService

    export_service = ReportExportService()

    if format == "pdf":
        pdf_bytes = await export_service.export_pdf(report)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{report.title}.pdf"'
            },
        )
    elif format == "docx":
        docx_bytes = await export_service.export_docx(report)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{report.title}.docx"'
            },
        )
    else:
        raise NotFoundException("Export format", format)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a report."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException("Report", report_id)

    await db.delete(report)
