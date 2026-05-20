"""
用户数据模型
对应数据库表：users
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from models.database import Base


class User(Base):
    """
    用户表模型
    
    字段说明：
    - id: 用户ID（主键，自增）
    - username: 用户名（唯一，不能为空）
    - password_hash: 密码哈希值（不能存明文！）
    - email: 邮箱（可选）
    - created_at: 注册时间（自动生成）
    - updated_at: 更新时间（自动更新）
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        """调试时显示用户信息"""
        return f"<User(id={self.id}, username='{self.username}')>"
