from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from configs.config import outline_model, create_model, seek_model
from models import UserStyle
from utils.llm_util import call_dashscope_llm
from utils.rag_util import retriever_with_re_ranking
from models.database import SessionLocal
from services.style_service import get_user_style_description, get_latest_style, analyze_and_save_style
import logging

logger = logging.getLogger(__name__)


# 1. 定义状态
class WriteStatus(TypedDict):
    user_id: int
    query: str
    retrieval_docs: List[dict]
    outline: str
    feedback: str
    content: str
    style_id: int  # 新增：用户指定的风格 ID


# 2. 定义节点

def retrieval_node(state: WriteStatus) -> WriteStatus:
    """检索节点：获取参考资料"""
    user_id = state["user_id"]
    query = state["query"]
    logger.info(f"[检索节点] 为用户 {user_id} 检索: {query}")
    docs = retriever_with_re_ranking(user_id=user_id, query=query, top_k=3)
    return {"retrieval_docs": docs}


def generate_outline_node(state: WriteStatus) -> WriteStatus:
    """创意节点：生成初稿 OR 根据反馈重修大纲"""
    query = state['query']
    docs = state.get('retrieval_docs', [])
    feedback = state.get('feedback', '')

    # 处理上下文
    context = ""
    if docs:
        context_parts = [f"【参考资料 {i+1}】\n{doc.get('page_content', '')}" for i, doc in enumerate(docs)]
        context = "\n\n".join(context_parts)
        ref_note = f"\n\n---\n## [参考资料说明]\n参考了以下资料：\n" + "\n".join([f"- 【参考资料 {i+1}】" for i in range(len(docs))])
    else:
        context = "无相关资料。"
        ref_note = "\n\n---\n## [参考资料说明]\n未检索到相关资料。"

    # 动态构建 Prompt
    if feedback:
        # --- 重修模式 ---
        old_outline = state.get('outline', '')
        prompt = f"""
你是一个专业的写作编辑。请根据用户的【修改意见】优化【上一版大纲】。

# 原始需求: {query}
# 上一版大纲: {old_outline}
# 用户修改意见: {feedback}

# 【重要要求】
1. **大纲必须极其简洁，控制在100字左右**
2. 使用 Markdown 标题层级（# ## ###）
3. 只保留核心要点，不要展开说明
4. 不要举例，不要详细解释
5. 每个要点用简短的短语表达

请直接输出优化后的大纲（Markdown格式）：
"""
    else:
        # --- 初稿模式 ---
        prompt = f"""
你是一个专业的写作助手。请根据以下资料生成极其简洁的大纲。

# 用户需求: {query}
# 参考资料: {context}

# 【重要要求】
1. **大纲必须极其简洁，控制在100字左右**（包括参考资料说明）
2. 使用 Markdown 标题层级（# ## ###）
3. 只保留核心框架，不要展开说明
4. 不要举例，不要详细解释
5. 每个要点用简短的短语表达（不超过15字）
6. 末尾附上参考资料说明

请直接输出大纲内容：
"""

    try:
        # 大纲生成限制最大 token 数为 200（严格控制输出长度）
        outline_text = call_dashscope_llm(prompt, model=outline_model, max_tokens=200)
        
        final_outline = outline_text + ref_note
        logger.info(f"[创意节点] {'重修' if feedback else '初稿'}成功，大纲长度: {len(outline_text)}")
        return {"outline": final_outline}
    except Exception as e:
        logger.error(f"[创意节点] 失败: {e}")
        return {"outline": f"生成出错: {str(e)}"}


def write_content_node(state: WriteStatus) -> WriteStatus:
    """写作节点：根据确认的大纲生成正文初稿"""
    query = state['query']
    outline = state['outline']
    user_id = state.get('user_id')
    style_id = state.get('style_id')  # 获取前端传来的风格 ID

    # 1. 获取用户风格描述（安全获取）
    style_desc = "保持专业、客观、逻辑清晰的商务写作风格。"
    if user_id:
        try:
            db = SessionLocal()
            # 优先使用指定的 style_id，如果没有则获取最新的
            target_style_id = style_id
            if not target_style_id:
                latest_style = get_latest_style(db, user_id)
                target_style_id = latest_style.id if latest_style else None
            
            if target_style_id:
                # 尝试从数据库获取指定风格的描述
                style_obj = db.query(UserStyle).filter(
                    UserStyle.id == target_style_id,
                    UserStyle.user_id == user_id
                ).first()
                
                if style_obj and style_obj.style_description:
                    style_desc = style_obj.style_description
                elif style_obj:
                    # 如果还没分析完，临时调用一次分析函数
                    style_desc = analyze_and_save_style(db, target_style_id)
        finally:
            db.close()

    logger.info(f"[写作节点] 开始撰写... (风格来源 ID: {style_id or '默认/最新'})")

    prompt = f"""
你是一个专业的专栏作家。请严格按照以下【写作大纲】撰写一篇深度文章。

# 写作主题
{query}

# 写作大纲
{outline}

# 风格要求（重要）
请务必模仿以下写作风格：
{style_desc}

# 格式要求
1. 字数控制：全文控制在800字左右（700-900字）
2. 内容展开：将每个要点扩写成通顺、有深度的段落
3. 逻辑连贯：段落之间要有自然的过渡
4. 语言风格：专业但不晦涩，通俗易懂

请直接输出正文内容：
"""

    try:
        content = call_dashscope_llm(prompt, model=create_model, max_tokens=4000)
        logger.info(f"[写作节点] 初稿生成成功，长度: {len(content)}")
        return {"content": content}
    except Exception as e:
        logger.error(f"[写作节点] 失败: {e}")
        return {"content": f"正文生成出错: {str(e)}"}


def reflect_content_node(state: WriteStatus) -> WriteStatus:
    """反思节点：对生成的正文进行快速优化"""
    content = state.get('content', '')
    
    if not content:
        logger.warning("[反思节点] 没有可反思的内容，跳过")
        return {"content": ""}
    
    logger.info(f"[反思节点] 开始对正文进行快速优化...")
    
    prompt = f"""
请对以下文章进行快速优化，重点关注：
1. 删除冗余表达，使语言更精炼
2. 检查段落过渡是否自然
3. 确保字数在800字左右

# 原文
{content}

# 要求
- 直接输出优化后的版本
- 不要解释修改过程
- 如果没有明显问题，保持原文不变

优化后的文章：
"""
    
    try:
        optimized_content = call_dashscope_llm(prompt, model=seek_model, max_tokens=2500)
        logger.info(f"[反思节点] 优化完成，最终长度: {len(optimized_content)}")
        return {"content": optimized_content}
    except Exception as e:
        logger.error(f"[反思节点] 失败: {e}")
        # 如果反思失败，返回原文
        return {"content": content}


# 3. 构建三个独立工作流 (供三个接口调用)

def build_outline_graph():
    """
    接口 1：生成初稿大纲
    流程：检索 -> 生成大纲
    """
    workflow = StateGraph(WriteStatus)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("generate", generate_outline_node)

    workflow.set_entry_point("retrieval")
    workflow.add_edge("retrieval", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


def build_refine_graph():
    """
    接口 2：重修大纲（用户给意见后调用）
    流程：直接利用已有的大纲和新的反馈进行重修
    注意：这里不需要重新检索，所以直接从 generate 节点开始
    """
    workflow = StateGraph(WriteStatus)
    workflow.add_node("generate", generate_outline_node)

    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


def build_write_graph():
    """
    接口 3：确认大纲并生成正文
    流程：生成初稿 -> 反思优化 -> 返回终稿
    """
    workflow = StateGraph(WriteStatus)
    workflow.add_node("write", write_content_node)
    workflow.add_node("reflect", reflect_content_node)

    workflow.set_entry_point("write")
    workflow.add_edge("write", "reflect")
    workflow.add_edge("reflect", END)

    return workflow.compile()
