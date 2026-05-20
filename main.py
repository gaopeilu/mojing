import sys
import io

# 强制设置标准输出为 UTF-8，解决 Windows GBK 编码报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.upload import router as upload_router
from routers.write import router as write_router
from routers.auth import router as auth_router
from routers.style import router as style_router
from routers.history import router as history_router
from models import init_db
import os

# 加载环境变量（必须在最前面）
load_dotenv()

# 初始化数据库（首次运行时创建表）
init_db()

app = FastAPI()

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改成具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(auth_router, prefix="/api/v1", tags=["用户认证"])
app.include_router(upload_router, prefix="/api/v1", tags=["文档上传"])
app.include_router(write_router, prefix="/api/v1", tags=["智能写作"])
app.include_router(style_router, prefix="/api/v1", tags=["风格管理"])
app.include_router(history_router, prefix="/api/v1", tags=["写作历史"])


@app.get("/")
async def root():
    """首页 - 返回古风前端页面"""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
