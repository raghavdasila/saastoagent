from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class CorpusHttpProblem(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class CorpusProblemView(BaseModel):
    code: str
    message: str


async def corpus_problem_response(
    _request: Request, error: CorpusHttpProblem
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=CorpusProblemView(code=error.code, message=error.message).model_dump(),
        headers={"Cache-Control": "no-store"},
    )


__all__ = ["CorpusHttpProblem", "CorpusProblemView", "corpus_problem_response"]
