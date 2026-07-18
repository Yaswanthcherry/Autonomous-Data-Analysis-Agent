from fastapi import APIRouter
from api.v1.endpoints import auth, datasets, analysis, chat, reports, users, events

api_router = APIRouter()
api_router.include_router(auth.router,     prefix="/auth",     tags=["auth"])
api_router.include_router(users.router,    prefix="/users",    tags=["users"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(events.router,   prefix="/events",   tags=["events"])
api_router.include_router(chat.router,     prefix="/chat",     tags=["chat"])
api_router.include_router(reports.router,  prefix="/reports",  tags=["reports"])
