"""
这个文件写三个函数用来处理重复上传的文本
"""
from utils.logger_util import logger
import os
import hashlib
from utils.path_util import get_project_abs_path


# 检查传入的文本是否已经存在用户私有数据库
def check_md5str_exist(md5str):
    if not os.path.exists(get_project_abs_path("md5.txt")):
        with open(get_project_abs_path("md5.txt"), "w", encoding="utf-8") as f:
            return False
    else:
        with open(get_project_abs_path("md5.txt"), "r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip() == md5str:    # strip 是为了去掉回车
                    return True
            return False


# 将md5字符串保存到文件里
def save_md5str_to_file(md5str):
    """保存MD5到文件"""
    if not md5str:
        logger.warning("[md5保存]跳过空MD5字符串")
        return

    try:
        with open(get_project_abs_path("md5.txt"), "a", encoding="utf-8") as f:
            f.write(md5str + "\n")
        logger.info(f"[md5保存]保存成功：{md5str[:8]}...")  # 只显示前8位
    except Exception as e:
        logger.error(f"[md5保存]保存失败：{e}", exc_info=True)


# 获取传入文本的md5字符串
def get_md5str(file_path):
    # 创建md5对象
    md5_obj = hashlib.md5()

    chunk_size = 4096  # 每次读取4k 防止爆露内存
    try:
        with open(file_path, "rb") as f:  # 二进制方式打开文件
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5_obj.update(chunk)
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"[md5计算]文件{file_path}计算失败； {str(e)}", exc_info=True)
        return ""


# 处理上传的文本 将上传的文本转成字符串 可以处理 txt 文本 可以处理pdf
def handle_upload_text(file_path):
    """
        解析文档返回纯文本
        支持：.txt, .md, .pdf, .docx
        """
    import os

    file_ext = os.path.splitext(file_path)[1].lower()    # 分割文件名和后缀

    try:
        # 纯文本文件
        if file_ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        # PDF 文件
        elif file_ext == '.pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            except ImportError:
                logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
                return ""

        # DOCX 文件
        elif file_ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error("python-docx not installed. Install with: pip install python-docx")
                return ""

        else:
            logger.warning(f"Unsupported file format: {file_ext}")
            return ""

    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}", exc_info=True)
        return ""
