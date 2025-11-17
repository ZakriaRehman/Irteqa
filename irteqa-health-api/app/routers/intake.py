"""
Intake Form Router
Handles patient onboarding intake forms and consent management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Client, Consent, ClientStatus
from app.dependencies import get_tenant_id
from app.services.email_service import email_service

router = APIRouter()


@router.get("/intake/{client_id}")
async def get_intake_status(
    client_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Get intake form status for a client"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check consent status
    consent_result = await db.execute(
        select(Consent).where(
            Consent.client_id == client_id,
            Consent.tenant_id == tenant_id
        )
    )
    consents = consent_result.scalars().all()

    consent_status = {
        consent.consent_type: {
            "signed": consent.signed,
            "signed_at": consent.signed_at.isoformat() if consent.signed_at else None
        }
        for consent in consents
    }

    return {
        "client_id": client.id,
        "name": client.name,
        "email": client.email,
        "status": client.status.value,
        "intake_completed": client.intake_data is not None,
        "intake_data": client.intake_data,
        "consents": consent_status,
        "assigned_therapist_id": client.assigned_therapist_id
    }


@router.post("/intake/{client_id}")
async def submit_intake_form(
    client_id: str,
    intake_data: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Submit intake form data"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update client with intake data
    client.intake_data = intake_data

    # Extract key fields from intake data
    if "date_of_birth" in intake_data:
        try:
            client.date_of_birth = datetime.fromisoformat(intake_data["date_of_birth"])
        except:
            pass

    if "insurance_provider" in intake_data:
        client.insurance_provider = intake_data["insurance_provider"]

    if "insurance_member_id" in intake_data:
        client.insurance_member_id = intake_data["insurance_member_id"]

    if "presenting_concerns" in intake_data:
        client.concerns = intake_data["presenting_concerns"]

    # Update status to onboarding if not already active
    if client.status != ClientStatus.ACTIVE:
        client.status = ClientStatus.ONBOARDING

    await db.commit()
    await db.refresh(client)

    print(f"[INTAKE] Intake form submitted for client {client_id}")

    # TODO: Trigger therapist matching logic
    # TODO: Auto-assign therapist based on specialties and availability

    return {
        "message": "Intake form submitted successfully",
        "client_id": client.id,
        "status": client.status.value,
        "next_step": "consent_forms"
    }


@router.get("/intake/{client_id}/consents")
async def get_required_consents(
    client_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Get required consent forms for client"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get existing consents
    consent_result = await db.execute(
        select(Consent).where(
            Consent.client_id == client_id,
            Consent.tenant_id == tenant_id
        )
    )
    existing_consents = {c.consent_type: c for c in consent_result.scalars().all()}

    # Define required consent types
    required_consents = [
        {
            "type": "treatment_consent",
            "title": "Consent for Treatment",
            "description": "Authorization to receive mental health treatment services",
            "required": True
        },
        {
            "type": "telehealth_consent",
            "title": "Telehealth Services Consent",
            "description": "Agreement to receive services via telehealth/video",
            "required": True
        },
        {
            "type": "privacy_hipaa",
            "title": "Privacy Practices & HIPAA",
            "description": "Acknowledgment of Notice of Privacy Practices",
            "required": True
        },
        {
            "type": "financial_agreement",
            "title": "Financial Agreement",
            "description": "Agreement regarding fees and payment",
            "required": True
        },
        {
            "type": "recording_consent",
            "title": "Session Recording Consent",
            "description": "Consent for audio/video recording of sessions",
            "required": False
        }
    ]

    # Add status to each consent
    for consent in required_consents:
        consent_type = consent["type"]
        if consent_type in existing_consents:
            existing = existing_consents[consent_type]
            consent["signed"] = existing.signed
            consent["signed_at"] = existing.signed_at.isoformat() if existing.signed_at else None
            consent["consent_id"] = existing.id
        else:
            consent["signed"] = False
            consent["signed_at"] = None
            consent["consent_id"] = None

    return {
        "client_id": client_id,
        "consents": required_consents
    }


@router.post("/intake/{client_id}/consents/{consent_type}")
async def sign_consent(
    client_id: str,
    consent_type: str,
    signature_data: Optional[Dict[str, Any]] = None,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Sign a consent form"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check if consent already exists
    consent_result = await db.execute(
        select(Consent).where(
            Consent.client_id == client_id,
            Consent.tenant_id == tenant_id,
            Consent.consent_type == consent_type
        )
    )
    existing_consent = consent_result.scalar_one_or_none()

    if existing_consent:
        # Update existing consent
        existing_consent.signed = True
        existing_consent.signed_at = datetime.utcnow()
        if signature_data and "artifact_url" in signature_data:
            existing_consent.artifact_url = signature_data["artifact_url"]
        await db.commit()
        consent_id = existing_consent.id
    else:
        # Create new consent
        new_consent = Consent(
            tenant_id=tenant_id,
            client_id=client_id,
            consent_type=consent_type,
            signed=True,
            signed_at=datetime.utcnow(),
            artifact_url=signature_data.get("artifact_url") if signature_data else None
        )
        db.add(new_consent)
        await db.commit()
        await db.refresh(new_consent)
        consent_id = new_consent.id

    # Check if all required consents are signed
    all_consents_result = await db.execute(
        select(Consent).where(
            Consent.client_id == client_id,
            Consent.tenant_id == tenant_id
        )
    )
    all_consents = all_consents_result.scalars().all()

    required_types = {"treatment_consent", "telehealth_consent", "privacy_hipaa", "financial_agreement"}
    signed_types = {c.consent_type for c in all_consents if c.signed}

    all_required_signed = required_types.issubset(signed_types)

    # If all consents signed and intake complete, mark as active
    if all_required_signed and client.intake_data:
        client.status = ClientStatus.ACTIVE
        await db.commit()
        print(f"[INTAKE] Client {client_id} completed onboarding - now active")

    return {
        "message": "Consent signed successfully",
        "consent_id": consent_id,
        "consent_type": consent_type,
        "all_required_signed": all_required_signed,
        "status": client.status.value
    }


@router.post("/intake/{client_id}/complete")
async def complete_onboarding(
    client_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark onboarding as complete and activate client"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Verify intake is complete
    if not client.intake_data:
        raise HTTPException(
            status_code=400,
            detail="Intake form must be completed before finishing onboarding"
        )

    # Verify required consents are signed
    consent_result = await db.execute(
        select(Consent).where(
            Consent.client_id == client_id,
            Consent.tenant_id == tenant_id,
            Consent.signed == True
        )
    )
    signed_consents = {c.consent_type for c in consent_result.scalars().all()}

    required_types = {"treatment_consent", "telehealth_consent", "privacy_hipaa", "financial_agreement"}

    if not required_types.issubset(signed_consents):
        missing = required_types - signed_consents
        raise HTTPException(
            status_code=400,
            detail=f"Missing required consents: {', '.join(missing)}"
        )

    # Update client status to active
    client.status = ClientStatus.ACTIVE
    await db.commit()

    print(f"[INTAKE] Onboarding completed for client {client_id}")

    # Send completion email
    try:
        dashboard_link = f"https://app.irteqa.com"
        email_sent = await email_service.send_onboarding_complete_email(
            to_email=client.email,
            patient_name=client.name,
            dashboard_link=dashboard_link
        )

        if email_sent:
            print(f"[INTAKE] Completion email sent to {client.email}")
        else:
            print(f"[INTAKE] Failed to send completion email to {client.email}")
    except Exception as e:
        print(f"[INTAKE] Error sending completion email: {e}")

    # TODO: Send therapist assignment notification
    # TODO: Enable session scheduling

    return {
        "message": "Onboarding completed successfully",
        "client_id": client_id,
        "status": client.status.value,
        "next_step": "schedule_session"
    }
