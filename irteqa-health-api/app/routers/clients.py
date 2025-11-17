from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Client
from app.schemas import ClientCreate, ClientResponse
from app.dependencies import get_tenant_id, get_idempotency_key

router = APIRouter()

@router.get("/clients")
async def list_clients(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """List all clients for the tenant"""
    result = await db.execute(
        select(Client).where(Client.tenant_id == tenant_id)
    )
    clients = result.scalars().all()

    return {
        "data": [
            {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "phone": client.phone,
                "status": client.status,
                "concerns": client.concerns,
                "created_at": client.created_at.isoformat() if client.created_at else None,
            }
            for client in clients
        ]
    }

@router.post("/clients", status_code=status.HTTP_201_CREATED, response_model=ClientResponse)
async def upsert_client(
    client_data: ClientCreate,
    tenant_id: str = Depends(get_tenant_id),
    idempotency_key: str = Depends(get_idempotency_key),
    db: AsyncSession = Depends(get_db)
):
    """Upsert client (provisional or full)"""
    
    # Check if client exists by email
    result = await db.execute(
        select(Client).where(
            Client.tenant_id == tenant_id,
            Client.email == client_data.email
        )
    )
    existing_client = result.scalar_one_or_none()
    
    if existing_client:
        # Update existing client
        for key, value in client_data.model_dump(exclude_unset=True).items():
            setattr(existing_client, key, value)
        await db.commit()
        await db.refresh(existing_client)
        return existing_client
    else:
        # Create new client
        new_client = Client(
            tenant_id=tenant_id,
            **client_data.model_dump()
        )
        db.add(new_client)
        await db.commit()
        await db.refresh(new_client)
        return new_client

@router.get("/clients/{id}/progress")
async def get_client_progress(
    id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    """Get outcomes/engagement snapshot for a client"""
    
    result = await db.execute(
        select(Client).where(
            Client.id == id,
            Client.tenant_id == tenant_id
        )
    )
    client = result.scalar_one_or_none()
    
    if not client:
        return {"error": {"code": "not_found", "message": "Client not found"}}
    
    # TODO: Calculate actual progress metrics
    return {
        "client_id": client.id,
        "status": client.status,
        "total_sessions": 0,
        "completed_goals": 0,
        "engagement_score": 0.0,
        "last_session": None
    }