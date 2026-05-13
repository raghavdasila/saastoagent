from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_async_session
from backend.services.entry_runtime import ENTRY_SESSION_COOKIE
from backend.services.qa.schemas import QADomainModelResponse, QAEvalRequest, QAEvalResponse, QAResetResponse, QAScenarioListResponse
from backend.services.qa.service import domain_model, evaluate_turn, is_reset_allowed, list_scenarios, reset_qa_context

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.get("/scenarios", response_model=QAScenarioListResponse)
async def qa_scenarios():
    return QAScenarioListResponse(scenarios=list_scenarios())


@router.get("/domain-model", response_model=QADomainModelResponse)
async def qa_domain_model():
    return QADomainModelResponse(domain=domain_model())


@router.post("/evaluate-turn", response_model=QAEvalResponse)
async def qa_evaluate_turn(body: QAEvalRequest):
    return evaluate_turn(body)


@router.post("/reset", response_model=QAResetResponse)
async def qa_reset(response: Response, session: AsyncSession = Depends(get_async_session)):
    if not is_reset_allowed(settings.auth_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="QA reset is only available in the local development configuration.",
        )
    result = await reset_qa_context(session)
    response.delete_cookie(ENTRY_SESSION_COOKIE, path="/")
    return result
