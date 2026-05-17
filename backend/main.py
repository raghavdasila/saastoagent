from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.auth import auth_backend, current_active_user, fastapi_users
from backend.core.config import settings
from backend.core.database import create_tables
from backend.core.models import User
from backend.core.schemas import UserCreate, UserRead
from backend.routes.entry import router as entry_router
from backend.routes.app_graph import router as app_graph_router
from backend.routes.health import router as health_router
from backend.routes.saas_agents import router as saas_agents_router
from backend.routes.agent import router as agent_router
from backend.routes.connections import router as connections_router
from backend.routes.qa import router as qa_router

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_up")
    await create_tables()
    yield
    logger.info("shutting_down")


app = FastAPI(title="SaaStoAgent v0.1", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)


@app.get("/api/me", response_model=UserRead, tags=["users"])
async def get_current_user(user: User = Depends(current_active_user)):
    return user


app.include_router(health_router)
app.include_router(entry_router)
app.include_router(app_graph_router)
app.include_router(saas_agents_router)
app.include_router(agent_router)
app.include_router(connections_router)
app.include_router(qa_router)
