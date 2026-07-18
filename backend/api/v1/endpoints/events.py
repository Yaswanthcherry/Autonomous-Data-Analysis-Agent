"""
Server-Sent Events — real-time pipeline progress stream
"""
import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.dependencies import get_current_user
from core.security import decode_token
from models.user import User
from models.analysis import AnalysisJob

router = APIRouter()


async def _get_user_from_token(
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Allow token via query param for SSE (EventSource can't set headers)."""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    payload = decode_token(token)
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user_from_token),
):
    """SSE endpoint — streams job progress until completion or failure."""

    async def event_generator():
        while True:
            result = await db.execute(
                select(AnalysisJob).where(AnalysisJob.id == job_id)
            )
            job = result.scalar_one_or_none()

            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            payload = {
                "job_id": job.id,
                "status": job.status,
                "current_stage": job.current_stage,
                "progress": job.progress,
                "error_message": job.error_message,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if job.status in ("completed", "failed"):
                break

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
