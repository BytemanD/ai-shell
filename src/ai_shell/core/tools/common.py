import os
from pathlib import Path

from agents import function_tool


@function_tool
def list_dir(
    path: str | None = None,
    name: str | None = None,
    include_hidden: bool = False,
) -> list[str]:
    """列出目录下的子目录和文件

    Args:
        path: 路径，如何不指定，则使用当前目录
        name: 模糊匹配文件/目录名
        include_hidden: 是否包含 隐藏文件/目录
    Returns:
        文件/目录列表
    """
    find_path = Path(path) if path else Path.cwd()

    def _filter(x: Path):
        if name and name not in x.name:
            return False
        if not include_hidden and x.name.startswith("."):
            return False
        return True

    children = [x for x in find_path.iterdir()]
    return [str(x.relative_to(find_path)) for x in filter(_filter, children)]


@function_tool
def change_dir(path: str):
    """切换到指定目录"""
    os.chdir(path)


@function_tool
def read_file(path: Path, encoding: str = "utf-8"):
    """读取文本文件内容"""
    if not path.exists():
        raise ValueError(f"path {path} not exists")
    if not path.is_file():
        raise ValueError(f"path {path} is not a file")
    return path.read_text(encoding=encoding)


@function_tool
def write_file(path: Path, content: str, encoding="utf-8"):
    """创建文本文件, 并写入数据"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
