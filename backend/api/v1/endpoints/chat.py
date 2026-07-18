from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.analysis import AnalysisJob, ChatMessage, AnalysisResult, MLModel, Report
from services.ai_service import AIService
import uuid

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/{job_id}/message")
async def send_message(
    job_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job_result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build context from analysis results
    results_q = await db.execute(select(AnalysisResult).where(AnalysisResult.job_id == job_id))
    results = results_q.scalars().all()

    models_q = await db.execute(select(MLModel).where(MLModel.job_id == job_id))
    ml_models = models_q.scalars().all()

    report_q = await db.execute(select(Report).where(Report.job_id == job_id))
    report = report_q.scalar_one_or_none()

    # Fetch chat history
    history_q = await db.execute(
        select(ChatMessage).where(ChatMessage.job_id == job_id)
        .order_by(ChatMessage.created_at.asc()).limit(20)
    )
    history = history_q.scalars().all()

    context_data = {
        "results": [{"type": r.result_type, "data": r.data} for r in results],
        "models": [{"name": m.model_name, "metrics": m.metrics, "is_best": m.is_best} for m in ml_models],
        "summary": report.executive_summary if report else None,
        "insights": report.business_insights if report else None,
    }

    ai = AIService()
    answer = await ai.answer_question(
        question=body.message,
        context=context_data,
        history=[{"role": m.role, "content": m.content} for m in history],
    )

    # Save messages
    user_msg = ChatMessage(id=str(uuid.uuid4()), job_id=job_id, role="user", content=body.message)
    assistant_msg = ChatMessage(id=str(uuid.uuid4()), job_id=job_id, role="assistant", content=answer)
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()

    return {"role": "assistant", "content": answer}


@router.get("/{job_id}/history")
async def get_history(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.job_id == job_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]
