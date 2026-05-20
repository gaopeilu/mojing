"""
风格管理接口：上传、查询、删除风格样本
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from fastapi import BackgroundTasks
from services.style_service import analyze_and_save_style
from models.database import get_db
from models.user_model import User
from models.style_model import UserStyle
from services.auth_service import get_current_user
from services.style_service import (
    upload_style_sample,
    get_user_styles,
    analyze_and_save_style,
    delete_style_sample
)
from utils.md5_util import handle_upload_text
from utils.logger_util import logger
import os
import shutil
from utils.path_util import get_project_abs_path

router = APIRouter(prefix="/style", tags=["风格管理"])


class StyleSampleResponse(BaseModel):
    """风格样本响应"""
    id: int
    title: str
    word_count: int
    uploaded_at: str
    style_description: str = None
    
    class Config:
        from_attributes = True


@router.post("/upload")
async def upload_style(
    file: UploadFile = File(..., description="上传的文章文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    上传用户写作风格样本
    
    支持格式：TXT, PDF, DOCX, MD
    """
    # 1. 验证文件格式
    allowed_extensions = ['.txt', '.pdf', '.docx', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}"
        )
    
    # 2. 保存临时文件
    temp_dir = get_project_abs_path("uploads/temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. 解析文档内容
        text_content = handle_upload_text(temp_path)
        
        if not text_content:
            raise HTTPException(
                status_code=400,
                detail="文档解析失败或内容为空"
            )
        
        # 4. 存入数据库
        style = upload_style_sample(
            db=db,
            user_id=current_user.id,
            content=text_content,
            title=file.filename
        )
        
        # 5. 添加后台任务：异步分析风格
        background_tasks.add_task(analyze_and_save_style, db, style.id)
        
        logger.info(f"[风格上传] 用户 {current_user.username} 上传样本: {file.filename}")
        
        return {
            "code": 200,
            "message": "风格样本上传成功，正在后台进行风格分析...",
            "data": {
                "id": style.id,
                "title": style.title,
                "word_count": style.word_count
            }
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"[风格上传] 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"上传失败: {str(e)}"
        )
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/list", response_model=List[StyleSampleResponse])
async def list_styles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    获取当前用户的风格样本列表
    """
    styles = get_user_styles(db, current_user.id, limit)
    
    return [
        StyleSampleResponse(
            id=s.id,
            title=s.title,
            word_count=s.word_count,
            uploaded_at=str(s.uploaded_at),
            style_description=s.style_description
        )
        for s in styles
    ]


@router.post("/analyze/{style_id}")
async def analyze_style(
    style_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用 LLM 分析指定风格样本的特征
    """
    # 验证样本归属
    style = db.query(UserStyle).filter(
        UserStyle.id == style_id,
        UserStyle.user_id == current_user.id
    ).first()
    
    if not style:
        raise HTTPException(
            status_code=404,
            detail="风格样本不存在或无权访问"
        )
    
    # 分析风格
    style_description = analyze_and_save_style(db, style_id)
    
    return {
        "code": 200,
        "message": "风格分析完成",
        "data": {
            "style_id": style_id,
            "description": style_description
        }
    }


@router.delete("/delete/{style_id}")
async def delete_style(
    style_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定的风格样本
    """
    success = delete_style_sample(db, current_user.id, style_id)
    
    if success:
        return {
            "code": 200,
            "message": "删除成功"
        }
