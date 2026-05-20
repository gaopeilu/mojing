"""
用户风格样本数据模型
对应数据库表：user_styles
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from models.database import Base


class UserStyle(Base):
    """
    用户风格样本表模型
    
    字段说明：
    - id: 样本ID（主键，自增）
    - user_id: 所属用户ID（外键，关联 users 表）
    - title: 样本标题（如文件名）
    - content: 样本文本内容
    - style_description: LLM 分析的风格描述
    - word_count: 字数统计
    - uploaded_at: 上传时间（自动生成）
    """
    __tablename__ = "user_styles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    style_description = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

    # 关系：一个用户可以有多个风格样本
    user = relationship("User", backref="styles")

    def __repr__(self):
        return f"<UserStyle(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
