"""
用户服务：注册、查询、更新
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user_model import User
from services.auth_service import hash_password


def register_user(db: Session, username: str, password: str, email: str = None) -> User:
    """
    注册新用户
    
    参数：
        db: 数据库会话
        username: 用户名
        password: 明文密码
        email: 邮箱（可选）
    
    返回：
        新创建的 User 对象
    
    异常：
        HTTPException: 用户名已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    new_user = User(
        username=username,
        password_hash=hash_password(password),  # 密码加密
        email=email
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    根据 ID 查询用户
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


def get_user_by_username(db: Session, username: str) -> User:
    """
    根据用户名查询用户
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user
