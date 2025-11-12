from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Session, Job, JobStatus
from app.schemas import (
    SessionCreate, SessionResponse, SessionStartRequest, 
    SessionStartResponse, SessionNotesAppend, SessionBriefRequest,
    SessionSummaryRequest, JobResponse
)
from app.dependencies import get_tenant_id, get_idempotency_key

router = APIRouter()

@router.get("/sessions")
async def list_sessions(
    tenant_id: str = Depends(get_tenant_id),
    cursor: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    filter_status: Optional[str] = Query(None, alias="filter[status]"),
    sort: Optional[str] = Query("-start_at"),
    db: AsyncSession = Depends(get_db)
):
    """List sessions with pagination and filtering"""
    
    query = select(Session).where(Session.tenant_id == tenant_id)
    
    if filter_status:
        query = query.where(Session.status == filter_status)
    
    # Apply sorting
    if sort == "-start_at":
        query = query.order_by(desc(Session.start_at))
    else:
        query = query.order_by(Session.start_at)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return {
        "data": [SessionResponse.model_validate(s) for s in sessions],
        "pagination": {
            "cursor": None,  # TODO: Implement cursor pagination
            "has_more": len(sessions) == limit
        }
    }

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Create a new therapy session"""
    
    new_session = Session(
        tenant_id=tenant_id,
        **session_data.model_dump()
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session

@router.post("/sessions/{id}:brief", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def generate_session_brief(
    id: str,
    brief_request: SessionBriefRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate pre-session brief (AI) → Job"""
    
    job = Job(
        tenant_id=tenant_id,
        job_type="session_brief",
        status=JobStatus.QUEUED,
        input_data={
            "session_id": id,
            "include": brief_request.include
        }
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # TODO: Queue actual AI processing task
    
    return JobResponse(
        job_id=job.id,
        status=job.status,
        result_ref=None
    )

@router.post("/sessions/{id}:start", response_model=SessionStartResponse)
async def start_session(
    id: str,
    start_request: SessionStartRequest,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Mark session started; optionally enable live assist"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    session.status = "in_progress"
    session.live_assist_enabled = start_request.live_assist
    session.live_assist_consent = start_request.consent
    
    await db.commit()
    
    response = SessionStartResponse(live_assist=start_request.live_assist)
    
    if start_request.live_assist:
        # Generate RT connection info
        response.rt = {
            "token": f"rt_token_{id}",
            "ws_audio_url": f"wss://api.hoop.health/v1/rt/audio?session_id={id}",
            "ws_control_url": f"wss://api.hoop.health/v1/rt/connect?session_id={id}",
            "sse_stream_url": f"https://api.hoop.health/v1/rt/stream?session_id={id}"
        }
    
    return response

@router.post("/sessions/{id}:stop")
async def stop_session(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Stop session / end live assist"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    session.live_assist_enabled = False
    await db.commit()
    
    return {"message": "Session stopped"}

@router.post("/sessions/{id}/notes", status_code=status.HTTP_202_ACCEPTED)
async def append_notes(
    id: str,
    notes_data: SessionNotesAppend,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Append notes or RT transcript segments"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    # Append to existing notes or transcript
    if notes_data.segment_id:
        # This is a transcript segment
        existing = session.transcript or ""
        session.transcript = existing + "\n" + notes_data.text
    else:
        # Regular notes
        existing = session.notes or ""
        session.notes = existing + "\n" + notes_data.text
    
    await db.commit()
    
    return {"message": "Notes appended"}

@router.post("/sessions/{id}:complete")
async def complete_session(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Mark session completed"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    session.status = "completed"
    session.end_at = datetime.utcnow()
    await db.commit()
    
    # TODO: Emit session.completed event
    
    return {"message": "Session completed", "session_id": id}

@router.post("/sessions/{id}:summarize", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def summarize_session(
    id: str,
    summary_request: SessionSummaryRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate SOAP summary (AI) → Job"""
    
    job = Job(
        tenant_id=tenant_id,
        job_type="session_summary",
        status=JobStatus.QUEUED,
        input_data={
            "session_id": id,
            "format": summary_request.format,
            "max_words": summary_request.max_words
        }
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # TODO: Queue actual AI processing task
    
    return JobResponse(
        job_id=job.id,
        status=job.status,
        result_ref=None
    )