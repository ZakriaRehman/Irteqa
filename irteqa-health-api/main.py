from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid

from app.database import engine, Base
from app.routers import inquiries, clients, sessions
from app.routers.stub_routers import (
    intake, consents, insurance, matching, goals,
    billing, notifications, treatment, webhooks, jobs, realtime
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="Hoop Health API",
    version="1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": str(exc)
            }
        }
    )

# Include routers - fully implemented
app.include_router(inquiries.router, prefix="/v1", tags=["inquiries"])
app.include_router(clients.router, prefix="/v1", tags=["clients"])
app.include_router(sessions.router, prefix="/v1", tags=["sessions"])

# Include stub routers - to be implemented
app.include_router(intake, prefix="/v1", tags=["intake"])
app.include_router(consents, prefix="/v1", tags=["consents"])
app.include_router(insurance, prefix="/v1", tags=["insurance"])
app.include_router(matching, prefix="/v1", tags=["matching"])
app.include_router(goals, prefix="/v1", tags=["goals"])
app.include_router(billing, prefix="/v1", tags=["billing"])
app.include_router(notifications, prefix="/v1", tags=["notifications"])
app.include_router(treatment, prefix="/v1", tags=["treatment"])
app.include_router(webhooks, prefix="/v1", tags=["webhooks"])
app.include_router(jobs, prefix="/v1", tags=["jobs"])
app.include_router(realtime, prefix="/v1", tags=["realtime"])

@app.get("/")
async def root():
    return {"message": "Hoop Health API v1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}