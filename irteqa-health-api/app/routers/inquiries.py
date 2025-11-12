from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Inquiry
from app.schemas import InquiryCreate, InquiryResponse
from app.dependencies import get_tenant_id, get_idempotency_key

router = APIRouter()

@router.post("/inquiries", status_code=status.HTTP_201_CREATED, response_model=InquiryResponse)
async def create_inquiry(
    inquiry_data: InquiryCreate,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Create a lead/inquiry"""
    
    new_inquiry = Inquiry(
        tenant_id=tenant_id,
        **inquiry_data.model_dump()
    )
    
    db.add(new_inquiry)
    await db.commit()
    await db.refresh(new_inquiry)
    
    # TODO: Trigger inquiry.submitted event
    # TODO: Send welcome email
    
    return new_inquiry