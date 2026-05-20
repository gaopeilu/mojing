import os
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from configs import config
from utils.path_util import get_project_abs_path


# 文本分割器函数 对传入的文本进行分割


def text_splitter(text: str) -> list:
    """原子操作 将长文本分割成小块"""
    fg = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=config.length_function,
        separators=config.separators,
    )
    return fg.split_text(text)


# 向量数据库函数检索器实例并将分割的文本传入向量数据库
def vector_db_add_chroma(user_id: int, texts: list, file_name: str = "unknown"):
    # 原子操作 创建向量数据库 并添加文本存入库
    collection_name = f"knowledge_base_{user_id}"
    os.makedirs(config.persist_directory, exist_ok=True)

    chroma = Chroma(
        persist_directory=get_project_abs_path(config.persist_directory),                   # 向量数据库保存路径
        embedding_function=config.embedding_function,    # 嵌入模型
        collection_name=collection_name,                 # 向量数据库名称
    )
    if texts:
        # 存入数据的时候带上数据源名称
        metadatas = [{"file_name": file_name}] * len(texts)
        chroma.add_texts(texts, metadatas=metadatas)


# 检索函数（简化版，暂时去掉重排序）
def retriever_with_re_ranking(user_id: int, query: str, top_k: int = 5):
    """
    从用户的向量库中检索相关文档
    
    参数：
        user_id: 用户ID，用于定位对应的向量库
        query: 查询文本
        top_k: 返回最相关的 top_k 个文档
    
    返回：
        list[dict]: 每个元素包含 page_content, metadata, score
    """
    # 1. 根据 user_id 找到对应的 Collection（就像找用户的私人图书馆）
    collection_name = f"knowledge_base_{user_id}"
    
    # 2. 初始化 Chroma 客户端
    chroma = Chroma(
        persist_directory=get_project_abs_path(config.persist_directory),
        embedding_function=config.embedding_function,
        collection_name=collection_name,
    )
    
    # 3. 执行相似度检索（返回 List[Tuple[Document, float]]）
    # similarity_search_with_score 返回的是元组列表：[(文档对象, 距离分数), ...]
    docs_with_scores = chroma.similarity_search_with_score(
        query=query,
        k=top_k
    )
    
    # 4. 如果没有检索到结果，返回空列表
    if not docs_with_scores:
        return []
    
    # 5. 格式化返回结果（把元组转换成字典，方便后续使用）
    result = []
    for doc, score in docs_with_scores:
        result.append({
            "page_content": doc.page_content,  # 文档的文本内容
            "metadata": doc.metadata,          # 文档的元数据（file_name, is_snippet等）
            "score": score                     # 距离分数（越小越相似）
        })
    
    # 6. 返回格式化后的结果
    return result








