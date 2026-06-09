"""
FinSight AI — Document Management Endpoints
Upload, list, retrieve, delete documents and trigger ingestion.
"""

import os
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.api.deps import CurrentUser, DBSession
from app.config import get_settings
from app.core.exceptions import DocumentProcessingException, NotFoundException
from app.models.document import Document, DocumentStatus, DocumentType, FileType
from app.models.audit_log import AuditLog
from app.schemas import DocumentListResponse, DocumentResponse, DocumentUploadRequest

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "html"}


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    document_type: str = Form("other"),
    company_id: str = Form(None),
    regulation_id: str = Form(None),
    user: CurrentUser = None,
    db: DBSession = None,
) -> DocumentResponse:
    """Upload a document for processing and ingestion into the RAG pipeline."""
    # Validate file extension
    if not file.filename:
        raise DocumentProcessingException("No file name provided")

    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentProcessingException(
            f"Unsupported file type: {extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise DocumentProcessingException(
            f"File too large: {file_size / (1024*1024):.1f}MB. Maximum: {settings.max_upload_size_mb}MB"
        )

    # Save file to storage
    doc_id = str(uuid7())
    upload_dir = os.path.join("data", "uploads", user.id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc_id}.{extension}")

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    try:
        file_type = FileType(extension)
    except ValueError:
        file_type = FileType.PDF

    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        doc_type = DocumentType.OTHER

    document = Document(
        id=doc_id,
        title=title,
        description=description,
        file_path=file_path,
        file_name=file.filename,
        file_type=file_type,
        file_size_bytes=file_size,
        document_type=doc_type,
        status=DocumentStatus.PENDING,
        company_id=company_id,
        regulation_id=regulation_id,
        uploaded_by=user.id,
    )
    db.add(document)

    # Audit log
    db.add(AuditLog(
        id=str(uuid7()),
        user_id=user.id,
        action="document_uploaded",
        resource_type="document",
        resource_id=doc_id,
        details={"file_name": file.filename, "file_size": file_size},
    ))

    await db.flush()

    logger.info(
        "document_uploaded",
        doc_id=doc_id,
        file_name=file.filename,
        user_id=user.id,
    )

    return DocumentResponse.model_validate(document)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    user: CurrentUser,
    db: DBSession,
    page: int = 1,
    page_size: int = 20,
    document_type: str | None = None,
    status_filter: str | None = None,
) -> DocumentListResponse:
    """List documents uploaded by the current user."""
    query = select(Document).where(Document.uploaded_by == user.id)

    if document_type:
        query = query.where(Document.document_type == document_type)
    if status_filter:
        query = query.where(Document.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user: CurrentUser,
    db: DBSession,
) -> DocumentResponse:
    """Get a specific document by ID."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.uploaded_by == user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundException("Document", document_id)

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a document and its associated chunks."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.uploaded_by == user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundException("Document", document_id)

    # Delete physical file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    await db.delete(document)

    # Audit log
    db.add(AuditLog(
        id=str(uuid7()),
        user_id=user.id,
        action="document_deleted",
        resource_type="document",
        resource_id=document_id,
    ))

    logger.info("document_deleted", doc_id=document_id, user_id=user.id)


@router.post("/{document_id}/ingest", response_model=DocumentResponse)
async def trigger_ingestion(
    document_id: str,
    user: CurrentUser,
    db: DBSession,
) -> DocumentResponse:
    """Trigger the RAG ingestion pipeline for a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.uploaded_by == user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundException("Document", document_id)

    if document.status == DocumentStatus.PROCESSING:
        raise DocumentProcessingException("Document is already being processed")

    # Update status
    document.status = DocumentStatus.PROCESSING

    # Trigger async ingestion (in production, use Celery/background task)
    from app.services.document_service import DocumentService
    doc_service = DocumentService(db)

    try:
        await doc_service.ingest_document(document)
        document.status = DocumentStatus.COMPLETED
        document.processed_at = datetime.now(timezone.utc)
    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.processing_error = str(e)
        logger.error("ingestion_failed", doc_id=document_id, error=str(e))

    await db.flush()
    return DocumentResponse.model_validate(document)
