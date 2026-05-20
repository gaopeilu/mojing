"""
认证相关接口：注册、登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from models.database import get_db
from services.user_service import register_user
from services.auth_service import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from utils.logger_util import logger

router = APIRouter(prefix="/auth", tags=["用户认证"])


# ========== 请求模型 ==========
class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    email: str = None


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


# ========== 接口 ==========
@router.post("/register", summary="用户注册")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    注册新用户
    
    - **username**: 用户名（唯一）
    - **password**: 密码
    - **email**: 邮箱（可选）
    """
    logger.info(f"[注册] 新用户: {req.username}")
    
    try:
        user = register_user(
            db=db,
            username=req.username,
            password=req.password,
            email=req.email
        )
        
        logger.info(f"[注册] 成功: {user.username} (ID: {user.id})")
        
        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "user_id": user.id,
                "username": user.username
            }
        }
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.error(f"[注册] 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回 JWT Token
    """
    logger.info(f"[登录] 用户尝试登录: {form_data.username}")
    
    # 验证用户身份
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"[登录] 失败: 用户名或密码错误 - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建 Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    logger.info(f"[登录] 成功: {user.username} (ID: {user.id})")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )
