"""
数据库初始化脚本
运行此文件创建数据库表
"""
from models import init_db

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_db()
    print("数据库初始化完成！")
