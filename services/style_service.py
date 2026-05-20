"""
风格服务层：负责处理所有与“用户写作风格”相关的业务逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import json  # 用于处理 JSON 格式的数据

from models.style_model import UserStyle  # 导入风格样本的数据库模型
from utils.llm_util import call_dashscope_llm  # 导入调用通义千问的工具函数
from configs.config import seek_model  # 导入配置好的模型名称


def upload_style_sample(
    db: Session,
    user_id: int,
    content: str,
    title: str = None
) -> UserStyle:
    """
    【存档案】上传用户的风格样本文章
    作用：把用户上传的文章存入 SQLite 数据库，作为后续学习的素材
    """
    # 1. 计算文章字数，方便前端展示
    word_count = len(content)

    # 2. 创建一个数据库对象（就像填一张登记表）
    new_style = UserStyle(
        user_id=user_id,          # 记录是谁传的
        title=title or f"风格样本_{word_count}字", # 如果没有标题，就自动生成一个
        content=content,          # 存入文章内容
        word_count=word_count     # 存入字数统计
    )

    # 3. 数据库三连击：添加 -> 提交保存 -> 刷新获取最新 ID
    db.add(new_style)
    db.commit()
    db.refresh(new_style)

    return new_style


def get_user_styles(db: Session, user_id: int, limit: int = 10) -> List[UserStyle]:
    """
    【查档案】获取当前用户的风格样本列表
    作用：在前端“风格管理”页面展示用户传过哪些文章
    """
    styles = (
        db.query(UserStyle)
        .filter(UserStyle.user_id == user_id)  # 安全过滤：只查当前用户的
        .order_by(UserStyle.uploaded_at.desc()) # 按时间倒序：最新的排前面
        .limit(limit)                           # 限制数量：一次只取 10 个
        .all()
    )

    return styles


def get_latest_style(db: Session, user_id: int) -> Optional[UserStyle]:
    """
    【找最新】获取用户最近上传的一篇样本
    作用：在写作时，如果没指定用哪篇风格，默认就用最新这篇
    """
    style = (
        db.query(UserStyle)
        .filter(UserStyle.user_id == user_id)
        .order_by(UserStyle.uploaded_at.desc())
        .first()  # 只取第一条
    )

    return style


def analyze_and_save_style(db: Session, style_id: int) -> str:
    """
    【做体检】核心功能：调用 LLM 分析文章风格并保存结果
    作用：让 AI 读一遍文章，总结出它的“写作指纹”，存在数据库里
    """
    # 1. 根据 ID 去数据库把那篇文章捞出来
    style = db.query(UserStyle).filter(UserStyle.id == style_id).first()

    if not style:
        raise HTTPException(status_code=404, detail="风格样本不存在")

    # 2. 防重复检查：如果之前已经分析过了，直接返回旧结果，省点 API 钱
    if style.style_description:
        return style.style_description

    # 3. 构造 Prompt（提示词）：告诉 AI 该怎么分析
    # 注意：只取前 2000 字，因为风格通常在开头就能看出来，且能节省 Token
    prompt = f"""
请分析以下文章的写作风格特征：

{style.content[:2000]}

请从以下维度分析：
1. 语言风格（正式/口语化/学术/文艺）
2. 句式特点（短句为主/长句复杂/排比多用）
3. 用词偏好（专业术语/日常词汇/成语典故）
4. 段落结构（总分总/递进式/并列式）
5. 语气态度（客观中立/主观情感/幽默风趣）

请用简洁的语言总结，控制在 200 字以内。
"""

    try:
        # 4. 呼叫 AI 大脑：发送请求并获取分析结果
        style_description = call_dashscope_llm(prompt, model=seek_model, max_tokens=500)

        # 5. 把分析结果存回数据库的 style_description 字段
        style.style_description = style_description
        db.commit()
        db.refresh(style)

        return style_description

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风格分析失败: {str(e)}")


def get_user_style_description(db: Session, user_id: int) -> str:
    """
    【取指纹】安全地获取用户的风格描述
    作用：如果用户有风格样本则返回分析结果，否则返回默认提示，防止报错
    """
    # 1. 尝试获取用户最新的风格样本
    style = get_latest_style(db, user_id)
    
    # 2. 如果找到了样本，且已经有分析结果，直接返回
    if style and style.style_description:
        return style.style_description
    
    # 3. 兜底策略：如果没有样本或还没分析完，返回一个通用的“专业风格”指令
    return "保持专业、客观、逻辑清晰的商务写作风格，用词精准，避免过于口语化。"


def delete_style_sample(db: Session, user_id: int, style_id: int) -> bool:
    """
    【删档案】删除指定的风格样本
    作用：用户觉得这篇写得不好，想删掉重新传
    """
    # 安全锁：确保用户只能删自己的样本，不能删别人的
    style = (
        db.query(UserStyle)
        .filter(UserStyle.id == style_id, UserStyle.user_id == user_id)
        .first()
    )

    if not style:
        raise HTTPException(status_code=404, detail="风格样本不存在或无权删除")

    db.delete(style)
    db.commit()

    return True
