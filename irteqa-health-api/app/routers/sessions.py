"""
Enhanced sessions router with WebSocket support for live transcription
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Session, Job, JobStatus, Client
from app.schemas import (
    SessionCreate, SessionResponse, SessionStartRequest, 
    SessionStartResponse, SessionNotesAppend, SessionBriefRequest,
    SessionSummaryRequest, JobResponse
)
from app.dependencies import get_tenant_id, get_idempotency_key
from app.websockets.session_ws import handle_audio_websocket, handle_transcript_stream

router = APIRouter()


@router.websocket("/rt/audio")
async def websocket_audio_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for audio streaming
    Client sends audio -> Deepgram transcribes -> Broadcast to all clients
    """
    await handle_audio_websocket(websocket, session_id, db)


@router.websocket("/rt/transcript")
async def websocket_transcript_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for receiving transcripts only
    Useful for observers or UI-only connections
    """
    await handle_transcript_stream(websocket, session_id)


@router.get("/sessions")
async def list_sessions(
    tenant_id: str = Depends(get_tenant_id),
    cursor: Optional[str] = None,
    limit: int = 50,
    filter_status: Optional[str] = None,
    sort: Optional[str] = "-start_at",
    db: AsyncSession = Depends(get_db)
):
    """List sessions with enhanced metadata"""
    
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
    
    # Enhance with client info
    session_list = []
    for session in sessions:
        client_result = await db.execute(
            select(Client).where(Client.id == session.client_id)
        )
        client = client_result.scalar_one_or_none()
        
        session_dict = SessionResponse.model_validate(session).model_dump()
        if client:
            session_dict["client_name"] = client.name
            session_dict["client_email"] = client.email
        
        session_list.append(session_dict)
    
    return {
        "data": session_list,
        "pagination": {
            "cursor": None,
            "has_more": len(sessions) == limit
        }
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
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
    
    return SessionResponse.model_validate(new_session)


@router.post("/sessions/{id}:start", response_model=SessionStartResponse)
async def start_session(
    id: str,
    start_request: SessionStartRequest,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Start session with live transcription"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    # Update session status
    session.status = "in_progress"
    session.live_assist_enabled = start_request.live_assist
    session.live_assist_consent = start_request.consent
    
    await db.commit()
    
    response = SessionStartResponse(live_assist=start_request.live_assist)
    
    # Provide WebSocket URLs for real-time connection
    base_url = "ws://localhost:8000/v1"  # TODO: Make configurable
    
    response.rt = {
        "token": f"session_{id}",
        "ws_audio_url": f"{base_url}/rt/audio?session_id={id}",
        "ws_transcript_url": f"{base_url}/rt/transcript?session_id={id}",
        "session_id": id
    }
    
    return response


@router.post("/sessions/{id}:stop")
async def stop_session(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Stop live transcription"""
    
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
    
    return {"message": "Session stopped", "session_id": id}


@router.post("/sessions/{id}:complete")
async def complete_session(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Mark session as completed"""
    
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
    session.live_assist_enabled = False
    await db.commit()
    
    return {"message": "Session completed", "session_id": id}


@router.get("/sessions/{id}")
async def get_session(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Get session details including transcript"""
    
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    # Get client info
    client_result = await db.execute(
        select(Client).where(Client.id == session.client_id)
    )
    client = client_result.scalar_one_or_none()
    
    session_dict = SessionResponse.model_validate(session).model_dump()
    if client:
        session_dict["client"] = {
            "id": client.id,
            "name": client.name,
            "email": client.email
        }
    
    return session_dict


@router.post("/sessions/{id}:summarize", status_code=status.HTTP_202_ACCEPTED)
async def summarize_session(
    id: str,
    summary_request: SessionSummaryRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate SOAP summary (AI) → Job"""
    
    # Verify session exists and has transcript
    result = await db.execute(
        select(Session).where(
            Session.id == id,
            Session.tenant_id == tenant_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"error": {"code": "not_found", "message": "Session not found"}}
    
    if not session.transcript:
        return {"error": {"code": "no_transcript", "message": "No transcript available"}}
    
    # Create job for SOAP generation
    job = Job(
        tenant_id=tenant_id,
        job_type="session_summary",
        status=JobStatus.QUEUED,
        input_data={
            "session_id": id,
            "format": summary_request.format,
            "max_words": summary_request.max_words,
            "transcript_length": len(session.transcript)
        }
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # TODO: Queue actual AI processing task
    # For now, mock SOAP generation
    session.soap_summary = {
        "subjective": "Client discussed feeling anxious about work deadlines.",
        "objective": "Client appeared engaged, maintained eye contact.",
        "assessment": "Moderate work-related anxiety, good insight.",
        "plan": "Continue weekly sessions, practice relaxation techniques."
    }
    await db.commit()
    
    return JobResponse(
        job_id=job.id,
        status=job.status,
        result_ref=f"/sessions/{id}/summary"
    )