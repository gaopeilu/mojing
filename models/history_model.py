"""
写作历史数据模型
对应数据库表：writing_history
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from models.database import Base


class WritingHistory(Base):
    """
    写作历史表模型
    
    字段说明：
    - id: 记录ID（主键，自增）
    - user_id: 所属用户ID（外键，关联 users 表）
    - query: 写作主题
    - outline: 使用的大纲
    - content: 生成的正文
    - reference_docs: 参考文档列表（JSON格式字符串）
    - created_at: 生成时间（自动生成）
    """
    __tablename__ = "writing_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String(500), nullable=False)
    outline = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    reference_docs = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 关系：一个用户可以有多条写作历史
    user = relationship("User", backref="writing_histories")

    def __repr__(self):
        return f"<WritingHistory(id={self.id}, user_id={self.user_id}, query='{self.query[:50]}...')>"
