import os


# 获取项目的根目录
def get_project_root_path():
    abs_path = os.path.abspath(__file__)
    project_root_path = os.path.dirname(os.path.dirname(abs_path))
    return project_root_path


# 获取项目的绝对路径 需要传入参数
def get_project_abs_path(file_path):
    return os.path.join(get_project_root_path(), file_path)


if __name__ == '__main__':
    print(get_project_root_path())
    print(get_project_abs_path('main.py'))


