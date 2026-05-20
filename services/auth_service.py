"""
认证服务：注册、登录、JWT Token 管理
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from models.database import get_db
from models.user_model import User
from configs.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# ========== 密码加密上下文 ==========
# 使用 bcrypt 直接加密（避免 passlib 兼容性问题）
import bcrypt

# OAuth2 方案（用于 Swagger UI 的授权按钮）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ========== 密码处理 ==========
def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    
    类比：把明文密码放进搅拌机，变成无法还原的密文
    """
    # 生成盐值并哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    类比：把输入的密码也搅拌一遍，对比结果是否一致
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


# ========== JWT Token ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Access Token
    
    参数：
        data: 要编码的数据（通常包含 user_id, username）
        expires_delta: 过期时间增量
    
    返回：
        JWT Token 字符串
    
    类比：给用户发一个临时手环，手环上有用户信息和过期时间
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # 编码 JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码 JWT Token
    
    参数：
        token: JWT Token 字符串
    
    返回：
        解码后的 payload 字典
    
    异常：
        JWTError: Token 无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 验证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ========== 用户认证 ==========
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户身份
    
    参数：
        db: 数据库会话
        username: 用户名
        password: 明文密码
    
    返回：
        User 对象（验证成功）或 None（验证失败）
    """
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    
    # 用户不存在或密码错误
    if not user or not verify_password(password, user.password_hash):
        return None
    
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户（依赖注入）
    
    用法：
        @router.get("/me")
        def read_me(current_user: User = Depends(get_current_user)):
            return current_user
    
    类比：检查用户的手环是否有效，有效则返回用户信息
    """
    # 解码 Token
    payload = decode_access_token(token)
    user_id: int = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
