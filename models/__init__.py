"""
数据库模型包
导入所有模型，并提供初始化函数
"""
from models.database import Base, engine
from models.user_model import User
from models.style_model import UserStyle
from models.history_model import WritingHistory


def init_db():
    """
    初始化数据库：创建所有表
    
    只在首次运行时调用一次
    后续运行会自动跳过已存在的表
    """
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功！")


if __name__ == "__main__":
    init_db()