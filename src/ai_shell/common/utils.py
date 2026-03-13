import re
from typing import List


def find_code_blocks_from_markdown(markdown_text: str) -> List[str]:
    """Match command"""
    code_patterns = [
        r"```\w+\n(.*?)\n```",
        r"```\n(.*?)\n```",
        r"```(.*?)```",
    ]
    for pattern in code_patterns:
        code_blocks = re.findall(pattern, markdown_text, re.DOTALL)
        if code_blocks:
            return code_blocks
    return []
