import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.dependencies import get_current_user
from core.config import settings
from models.user import User
from models.dataset import Dataset
from loguru import logger

router = APIRouter()

ALLOWED_TYPES = {
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/json": "json",
}


@router.post("/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only CSV, XLSX, JSON files allowed")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    file_id = str(uuid.uuid4())
    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{file_id}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(contents)

    dataset = Dataset(
        id=file_id,
        owner_id=current_user.id,
        filename=filename,
        original_name=file.filename,
        file_path=file_path,
        file_size=len(contents),
        file_type=ext,
        status="uploaded",
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    logger.info(f"Dataset uploaded: {file_id} by user {current_user.id}")
    return {"id": dataset.id, "original_name": dataset.original_name,
            "file_type": dataset.file_type, "file_size": dataset.file_size}


@router.get("/")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dataset).where(Dataset.owner_id == current_user.id)
        .order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    return [
        {"id": d.id, "original_name": d.original_name, "file_type": d.file_type,
         "file_size": d.file_size, "status": d.status, "row_count": d.row_count,
         "col_count": d.col_count, "created_at": d.created_at}
        for d in datasets
    ]


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)

    await db.delete(dataset)
    await db.commit()
