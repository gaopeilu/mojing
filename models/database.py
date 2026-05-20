"""
数据库连接配置
使用 SQLAlchemy + SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.path_util import get_project_abs_path
import os

# ========== 数据库配置 ==========
DATABASE_URL = f"sqlite:///{get_project_abs_path('data/users.db')}"

# 确保 data 目录存在
os.makedirs(get_project_abs_path('data'), exist_ok=True)

# 创建引擎（SQLite 需要 check_same_thread=False）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类（所有模型都要继承它）
Base = declarative_base()


# ========== 依赖注入 ==========
def get_db():
    """
    FastAPI 依赖注入函数
    每次请求创建一个独立的数据库会话
    请求结束后自动关闭
    
    用法：
        @router.get("/users")
        def list_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()