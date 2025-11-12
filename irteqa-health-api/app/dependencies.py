from fastapi import Header, HTTPException, status
from typing import Optional

async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract and validate tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "missing_tenant_id",
                    "message": "X-Tenant-Id header is required"
                }
            }
        )
    return x_tenant_id

async def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None)
) -> Optional[str]:
    """Extract idempotency key from header"""
    return idempotency_key

async def verify_bearer_token(authorization: str = Header(...)) -> str:
    """Verify bearer token (placeholder for actual auth)"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "invalid_authorization",
                    "message": "Invalid authorization header format"
                }
            }
        )
    token = authorization.replace("Bearer ", "")
    # TODO: Implement actual JWT validation
    return token