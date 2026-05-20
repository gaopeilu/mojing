# 文本分割器相关配置
import os
from langchain_community.embeddings import DashScopeEmbeddings

chunk_size = 1000
chunk_overlap = 200
length_function = len
separators = ["\n\n", "\n", r"(?<=\. )", " ", ""]  # 使用原始字符串避免转义警告


# 向量数据库相关配置
collection_name = "chroma_db"

# 从环境变量获取 API Key（必须在创建对象前确保已设置）
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope_api_key:
    raise ValueError(
        "未找到 DASHSCOPE_API_KEY 环境变量！\n"
        "请在系统中设置：setx DASHSCOPE_API_KEY \"你的API密钥\"\n"
        "或在代码中直接设置：os.environ['DASHSCOPE_API_KEY'] = 'sk-xxx'"
    )

embedding_function = DashScopeEmbeddings(
    model="text-embedding-v3",  # 使用阿里云官方模型名称
    dashscope_api_key=dashscope_api_key  # 显式传入 API Key
)
persist_directory = "data"

# LLM 模型配置（不同场景使用不同模型）
# 全部使用有免费额度的模型
outline_model = "qwen-turbo"       # 生成大纲用（速度快，听话）
create_model = "qwen-plus"         # 生成正文用（质量较好，有免费额度）
seek_model = "qwen-turbo"          # 反思优化用（速度最快）

# ========== JWT 认证配置（新增）==========
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


