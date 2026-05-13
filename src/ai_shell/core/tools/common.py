import os

from agents import function_tool


@function_tool
def getcwd(path: str):
    """切换到指定目录"""
    os.chdir(path)
