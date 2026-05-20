"""
写作历史接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from models.database import get_db
from models.user_model import User
from services.auth_service import get_current_user
from services.history_service import get_user_history, get_history_by_id

router = APIRouter(prefix="/history", tags=["写作历史"])


class HistoryResponse(BaseModel):
    """历史记录响应"""
    id: int
    query: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/list", response_model=List[HistoryResponse])
async def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    获取当前用户的写作历史列表
    """
    histories = get_user_history(db, current_user.id, limit)
    
    return [
        HistoryResponse(
            id=h.id,
            query=h.query,
            created_at=str(h.created_at)
        )
        for h in histories
    ]


@router.get("/{history_id}")
async def get_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定历史记录的详情
    """
    history = get_history_by_id(db, current_user.id, history_id)
    
    return {
        "code": 200,
        "data": {
            "id": history.id,
            "query": history.query,
            "outline": history.outline,
            "content": history.content,
            "created_at": str(history.created_at)
        }
    }
