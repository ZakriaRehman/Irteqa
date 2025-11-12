from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class ClientStatus(str, enum.Enum):
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"

class Inquiry(Base):
    __tablename__ = "inquiries"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    concerns = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    status = Column(SQLEnum(ClientStatus), default=ClientStatus.ONBOARDING)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    date_of_birth = Column(DateTime)
    concerns = Column(Text)
    intake_data = Column(JSON)
    insurance_provider = Column(String)
    insurance_member_id = Column(String)
    assigned_therapist_id = Column(String, ForeignKey("therapists.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    therapist = relationship("Therapist", back_populates="clients")
    sessions = relationship("Session", back_populates="client")
    goals = relationship("Goal", back_populates="client")

class Therapist(Base):
    __tablename__ = "therapists"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    license_number = Column(String)
    specialties = Column(JSON)
    availability = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    clients = relationship("Client", back_populates="therapist")
    sessions = relationship("Session", back_populates="therapist")

class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    consent_type = Column(String, nullable=False)
    signed = Column(Boolean, default=False)
    artifact_url = Column(String)
    signed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    therapist_id = Column(String, ForeignKey("therapists.id"), nullable=False)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    transcript = Column(Text)
    soap_summary = Column(JSON)
    live_assist_enabled = Column(Boolean, default=False)
    live_assist_consent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    client = relationship("Client", back_populates="sessions")
    therapist = relationship("Therapist", back_populates="sessions")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    session_id = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    target_date = Column(DateTime(timezone=True))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    client = relationship("Client", back_populates="goals")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"))
    amount_cents = Column(Integer, nullable=False)
    status = Column(String, default="draft")
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    job_type = Column(String, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED)
    input_data = Column(JSON)
    result_data = Column(JSON)
    result_ref = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    
    id = Column(String, primary_key=True, default=gen_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)
    secret = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())