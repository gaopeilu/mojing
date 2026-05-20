"""
LLM 调用工具模块
封装阿里云 DashScope 大模型调用
"""
import os
from langchain_community.llms import Tongyi
from utils.logger_util import logger


def call_dashscope_llm(prompt: str, model: str = "qwen-plus", temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    调用阿里云 DashScope LLM
    
    参数：
        prompt: 提示词
        model: 模型名称（qwen-turbo / qwen-plus / qwen-max）
        temperature: 创造性参数（0-1，越高越有创意）
        max_tokens: 最大输出长度
    
    返回：
        LLM 生成的文本
    """
    # 获取 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到 DASHSCOPE_API_KEY 环境变量！")
    
    try:
        # 初始化 LLM
        llm = Tongyi(
            model=model,
            dashscope_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 调用
        logger.info(f"[LLM调用] 使用模型: {model}, 提示词长度: {len(prompt)} 字符")
        response = llm.invoke(prompt)
        
        # 确保返回的是字符串（兼容不同版本的 LangChain）
        if hasattr(response, 'content'):
            result = response.content
        else:
            result = str(response)
            
        logger.info(f"[LLM调用] 响应长度: {len(result)} 字符")
        return result
    
    except Exception as e:
        logger.error(f"[LLM调用] 失败: {e}", exc_info=True)
        raise e
