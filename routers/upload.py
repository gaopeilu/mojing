from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.md5_util import get_md5str, check_md5str_exist, save_md5str_to_file, handle_upload_text
from utils.rag_util import text_splitter, vector_db_add_chroma
from utils.logger_util import logger
from utils.path_util import get_project_abs_path
from models.database import get_db
from models.user_model import User
from services.auth_service import get_current_user
import os
import shutil

router = APIRouter()


@router.post("/upload")
async def upload_document(
        file: UploadFile = File(..., description="上传的文档文件"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    上传文档并存入向量数据库
    支持格式：TXT, PDF, DOCX
    """
    # 1. 验证文件格式
    allowed_extensions = ['.txt', '.pdf', '.docx', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")

    # 2. 保存临时文件
    temp_dir = get_project_abs_path("uploads/temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"文件已保存到临时路径: {temp_path}")

        # 3. 计算 MD5 并检查重复
        md5str = get_md5str(temp_path)
        logger.info(f"文件 MD5: {md5str}")

        if check_md5str_exist(md5str):
            os.remove(temp_path)  # 清理临时文件
            return {"code": 200, "message": "文件已存在，无需重复上传"}

        # 4. 解析文档内容
        text_content = handle_upload_text(temp_path)
        if not text_content:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail="文档解析失败或内容为空")

        logger.info(f"文档解析成功，文本长度: {len(text_content)} 字符")

        # 5. 文本分割
        chunks = text_splitter(text_content)
        if not chunks:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail="文本分割后为空")

        logger.info(f"文本分割为 {len(chunks)} 个块")

        # 6. 存入向量数据库（使用真实用户 ID）
        vector_db_add_chroma(current_user.id, chunks, file.filename)

        # 7. 保存 MD5 凭证
        save_md5str_to_file(md5str)

        logger.info(f"文件上传成功: {file.filename}")

        # 8. 返回结果
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "file_name": file.filename,
                "chunks_count": len(chunks),
                "md5": md5str
            }
        }

    except HTTPException:
        raise  # 重新抛出 HTTP 异常

    except Exception as e:
        logger.error(f"上传处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

    finally:
        # 9. 清理临时文件（无论成功失败都执行）
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"临时文件已清理: {temp_path}")





