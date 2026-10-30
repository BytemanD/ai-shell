import asyncio
import functools

from pystonic import set_app_name

set_app_name("aishell")


def async_cmd(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper
