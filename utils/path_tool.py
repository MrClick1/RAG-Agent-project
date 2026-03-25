"""
为整个工程提供统一的绝对路径
"""
import os

def get_project_root() -> str:
    """
    获取工程所在的根目录
    :return:字符串根目录
    """

    # 获取当前文件所在的路径
    current_file = os.path.abspath(__file__)
    # 获取当前文件所在的文件夹
    current_dir = os.path.dirname(current_file)
    # 获取工程根目录
    project_root = os.path.dirname(current_dir)

    return project_root

def get_abs_path(relative_path: str) -> str:
    """
    获取相对路径，得到绝对路径
    :param relative_path:
    :return:
    """

    project_root = get_project_root()
    return os.path.join(project_root, relative_path)

# print(get_abs_path('config\config.py'))