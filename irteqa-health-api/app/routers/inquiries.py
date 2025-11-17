from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Inquiry, Client, ClientStatus
from app.schemas import InquiryCreate, InquiryResponse
from app.dependencies import get_tenant_id, get_idempotency_key
from app.services.email_service import email_service

router = APIRouter()

@router.post("/inquiries", status_code=status.HTTP_201_CREATED, response_model=InquiryResponse)
async def create_inquiry(
    inquiry_data: InquiryCreate,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Create a lead/inquiry and trigger onboarding workflow"""

    # Create inquiry record
    new_inquiry = Inquiry(
        tenant_id=tenant_id,
        **inquiry_data.model_dump()
    )

    db.add(new_inquiry)
    await db.commit()
    await db.refresh(new_inquiry)

    # Create or update provisional client record
    result = await db.execute(
        select(Client).where(
            Client.tenant_id == tenant_id,
            Client.email == inquiry_data.email
        )
    )
    existing_client = result.scalar_one_or_none()

    if not existing_client:
        # Create new provisional client
        new_client = Client(
            tenant_id=tenant_id,
            name=inquiry_data.name,
            email=inquiry_data.email,
            phone=inquiry_data.phone,
            concerns=inquiry_data.concerns,  # Store initial concerns
            status=ClientStatus.ONBOARDING  # Set status to onboarding
        )
        db.add(new_client)
        await db.commit()
        await db.refresh(new_client)
        client_id = new_client.id
    else:
        # Update existing client
        existing_client.name = inquiry_data.name
        existing_client.phone = inquiry_data.phone or existing_client.phone
        existing_client.concerns = inquiry_data.concerns
        if existing_client.status != ClientStatus.ACTIVE:
            existing_client.status = ClientStatus.ONBOARDING
        await db.commit()
        client_id = existing_client.id

    # Generate onboarding link
    onboarding_link = f"https://app.irteqa.com/onboarding/{client_id}"

    # Send welcome email with onboarding link
    try:
        email_sent = await email_service.send_welcome_email(
            to_email=inquiry_data.email,
            patient_name=inquiry_data.name,
            onboarding_link=onboarding_link
        )

        if email_sent:
            print(f"[INQUIRY] Welcome email sent to {inquiry_data.email}")
        else:
            print(f"[INQUIRY] Failed to send welcome email to {inquiry_data.email}")
    except Exception as e:
        print(f"[INQUIRY] Error sending welcome email: {e}")

    return new_inquiry