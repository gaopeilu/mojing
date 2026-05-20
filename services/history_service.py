"""
写作历史服务：保存、查询历史记录
"""
from typing import List
from sqlalchemy.orm import Session
import json

from models.history_model import WritingHistory


def save_writing_history(
    db: Session,
    user_id: int,
    query: str,
    outline: str,
    content: str,
    reference_docs: List[dict] = None
) -> WritingHistory:
    """
    保存写作历史记录
    """
    # 将参考文档列表转为 JSON 字符串
    reference_docs_json = json.dumps(reference_docs, ensure_ascii=False) if reference_docs else None
    
    # 创建历史记录
    history = WritingHistory(
        user_id=user_id,
        query=query,
        outline=outline,
        content=content,
        reference_docs=reference_docs_json
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history


def get_user_history(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[WritingHistory]:
    """
    获取用户的写作历史列表（支持分页）
    """
    histories = (
        db.query(WritingHistory)
        .filter(WritingHistory.user_id == user_id)
        .order_by(WritingHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return histories


def get_history_by_id(db: Session, user_id: int, history_id: int) -> WritingHistory:
    """
    根据 ID 查询写作历史
    """
    from fastapi import HTTPException, status
    
    history = (
        db.query(WritingHistory)
        .filter(
            WritingHistory.id == history_id,
            WritingHistory.user_id == user_id
        )
        .first()
    )
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="写作历史不存在或无权访问"
        )
    
    return history
