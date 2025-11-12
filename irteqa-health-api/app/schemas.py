from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatusEnum(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class SessionStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class ClientStatusEnum(str, Enum):
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"

# Job Response
class JobResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    result_ref: Optional[str] = None

# Inquiry
class InquiryCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    concerns: Optional[str] = None

class InquiryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Client
class ClientCreate(BaseModel):
    status: Optional[ClientStatusEnum] = ClientStatusEnum.ONBOARDING
    name: str
    email: EmailStr
    phone: Optional[str] = None
    concerns: Optional[str] = None
    intake_data: Optional[Dict[str, Any]] = None

class ClientResponse(BaseModel):
    id: str
    tenant_id: str
    status: ClientStatusEnum
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Intake Form
class IntakeFormSubmit(BaseModel):
    client_id: str
    raw_form: Dict[str, Any]

# Consent
class ConsentCreate(BaseModel):
    client_id: str
    consent_signed: bool
    artifact_url: Optional[str] = None

class ConsentResponse(BaseModel):
    id: str
    client_id: str
    signed: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Insurance Verification
class InsuranceVerify(BaseModel):
    client_id: str
    provider: str
    member_id: str

# Matching
class TherapistAssign(BaseModel):
    client_id: str
    strategy: str = "rules_v1"

class TherapistAssignResponse(BaseModel):
    therapist_id: str
    client_id: str
    assigned_at: datetime

# Session
class SessionCreate(BaseModel):
    client_id: str
    therapist_id: str
    start_at: datetime
    status: Optional[SessionStatusEnum] = SessionStatusEnum.SCHEDULED

class SessionResponse(BaseModel):
    id: str
    client_id: str
    therapist_id: str
    status: SessionStatusEnum
    start_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class SessionStartRequest(BaseModel):
    live_assist: bool = False
    consent: bool = False

class SessionStartResponse(BaseModel):
    live_assist: bool
    rt: Optional[Dict[str, str]] = None

class SessionNotesAppend(BaseModel):
    mode: str = "append"
    text: str
    ts_ms: Optional[int] = None
    segment_id: Optional[str] = None
    final: Optional[bool] = None

class SessionBriefRequest(BaseModel):
    include: List[str] = ["intake_summary", "last_session_summary", "active_goals"]

class SessionSummaryRequest(BaseModel):
    format: str = "SOAP"
    max_words: int = 250

# Goals
class GoalCreate(BaseModel):
    client_id: str
    session_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class GoalResponse(BaseModel):
    id: str
    client_id: str
    title: str
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Billing
class InvoiceCreate(BaseModel):
    client_id: str
    session_id: Optional[str] = None
    amount_cents: int
    status: str = "draft"

class InvoiceResponse(BaseModel):
    id: str
    client_id: str
    amount_cents: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Notifications
class NotificationSend(BaseModel):
    to: str | List[str]
    channel: str
    template: str
    data: Optional[Dict[str, Any]] = None
    schedule: Optional[List[Dict[str, str]]] = None

# Treatment
class TreatmentTerminate(BaseModel):
    client_id: str
    summary: str
    plan: Optional[str] = None

# Webhooks
class WebhookEndpointCreate(BaseModel):
    url: str
    events: List[str]

class WebhookEndpointResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    secret: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Real-time
class RTTokenCreate(BaseModel):
    session_id: str
    duration_seconds: int = 3600

class RTTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    ws_audio_url: str
    ws_control_url: str
    sse_stream_url: str