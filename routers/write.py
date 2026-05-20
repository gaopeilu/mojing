from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from agent.workflow import build_outline_graph, build_refine_graph, build_write_graph
from utils.logger_util import logger
from models.database import get_db
from models.user_model import User
from services.auth_service import get_current_user
from services.history_service import save_writing_history

router = APIRouter()


# --- 定义请求模型 (Pydantic) ---

class OutlineRequest(BaseModel):
    """接口 1: 生成初稿大纲"""
    user_id: int
    query: str


class RefineRequest(BaseModel):
    """接口 2: 重修大纲 (用户给意见)"""
    user_id: int
    query: str
    outline: str  # 上一版大纲
    feedback: str # 用户的修改意见


class GenerateRequest(BaseModel):
    """接口 3: 确认大纲并生成正文"""
    user_id: int
    query: str
    outline: str  # 用户确认的大纲
    style_id: int = None  # 可选：指定使用的风格样本 ID


# --- 接口 1: 生成初稿大纲 ---
@router.post("/write/outline")
async def create_initial_outline(
    req: OutlineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"[接口] 用户 {current_user.username} 请求生成大纲: {req.query}")
    try:
        app = build_outline_graph()
        result = app.invoke({
            "user_id": current_user.id,  # 从 JWT 获取真实 user_id
            "query": req.query,
            "retrieval_docs": [],
            "outline": "",
            "feedback": "",
            "content": ""
        })
        return {"code": 200, "data": {"outline": result['outline']}}
    except Exception as e:
        logger.error(f"初稿生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 接口 2: 重修大纲 ---
@router.post("/write/refine")
async def refine_outline(
    req: RefineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"[接口] 用户 {current_user.username} 收到重修请求, 反馈: {req.feedback}")
    try:
        app = build_refine_graph()
        result = app.invoke({
            "user_id": current_user.id,  # 从 JWT 获取
            "query": req.query,
            "retrieval_docs": [], # 重修通常不需要重新检索
            "outline": req.outline,
            "feedback": req.feedback,
            "content": ""
        })
        return {"code": 200, "data": {"outline": result['outline']}}
    except Exception as e:
        logger.error(f"重修失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 接口 3: 生成正文 ---
@router.post("/write/generate")
async def generate_content(
    req: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"[接口] 用户 {current_user.username} 请求生成正文")
    try:
        app = build_write_graph()
        result = app.invoke({
            "user_id": current_user.id,  # 从 JWT 获取
            "query": req.query,
            "retrieval_docs": [],
            "outline": req.outline,
            "feedback": "",
            "content": "",
            "style_id": req.style_id  # 传递风格 ID
        })
        
        # 保存写作历史
        save_writing_history(
            db=db,
            user_id=current_user.id,
            query=req.query,
            outline=req.outline,
            content=result['content']
        )
        
        return {"code": 200, "data": {"content": result['content']}}
    except Exception as e:
        logger.error(f"正文生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
