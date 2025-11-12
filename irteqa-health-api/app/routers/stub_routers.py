"""Stub routers for remaining endpoints - to be implemented"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_tenant_id, get_idempotency_key
from app.schemas import JobResponse, JobStatusEnum

# Intake Router
intake = APIRouter()

@intake.post("/intake/forms", status_code=status.HTTP_202_ACCEPTED)
async def submit_intake_form(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    return JobResponse(job_id="job_123", status=JobStatusEnum.QUEUED, result_ref=None)

# Consents Router
consents = APIRouter()

@consents.post("/consents", status_code=status.HTTP_201_CREATED)
async def create_consent(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Consent stored"}

# Insurance Router
insurance = APIRouter()

@insurance.post("/insurance/verify", status_code=status.HTTP_202_ACCEPTED)
async def verify_insurance(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    return JobResponse(job_id="job_456", status=JobStatusEnum.QUEUED, result_ref=None)

# Matching Router
matching = APIRouter()

@matching.post("/matching/assign", status_code=status.HTTP_201_CREATED)
async def assign_therapist(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Therapist assigned"}

# Goals Router
goals = APIRouter()

@goals.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Goal created"}

# Billing Router
billing = APIRouter()

@billing.post("/billing/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Invoice created"}

@billing.post("/billing/webhooks/stripe")
async def stripe_webhook(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Webhook received"}

# Notifications Router
notifications = APIRouter()

@notifications.post("/notifications/send", status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Notification queued"}

# Treatment Router
treatment = APIRouter()

@treatment.post("/treatment/terminate", status_code=status.HTTP_201_CREATED)
async def terminate_treatment(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Treatment terminated"}

# Jobs Router
jobs = APIRouter()

@jobs.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    return JobResponse(job_id=job_id, status=JobStatusEnum.RUNNING, result_ref=None)

# Webhooks Router
webhooks = APIRouter()

@webhooks.post("/webhooks/endpoints", status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"message": "Webhook endpoint created"}

# Realtime Router
realtime = APIRouter()

@realtime.post("/rt/tokens", status_code=status.HTTP_201_CREATED)
async def create_rt_token(
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    return {"token": "rt_token_abc123"}

@realtime.post("/rt/offer")
async def webrtc_offer(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    return {"answer": "sdp_answer"}

@realtime.get("/rt/connect")
async def rt_connect_websocket(session_id: str):
    return {"message": "WebSocket endpoint - use WS protocol"}

@realtime.get("/rt/audio")
async def rt_audio_websocket(session_id: str):
    return {"message": "WebSocket endpoint - use WS protocol"}

@realtime.get("/rt/stream")
async def rt_sse_stream(session_id: str):
    return {"message": "SSE endpoint - use EventSource"}