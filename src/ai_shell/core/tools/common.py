import os
from pathlib import Path

from agents import function_tool


@function_tool
def getcwd(path: str):
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
