from fastapi import APIRouter
from app.api.v1 import auth, hackathons, submissions, evaluations, rankings, chat, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(hackathons.router, prefix="/hackathons", tags=["hackathons"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
