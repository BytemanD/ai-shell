from collections.abc import Sequence
from urllib.parse import parse_qs

from agents import function_tool
from pystonic.utils import httpclient

from ai_shell.common.conf import CONF

DEFAULT_CLIENT = httpclient.default_client(
    raise_for_status=True,
    timeout=CONF.http_client.timeout,
)


@function_tool
def web_get(
    url: str,
    params: str | None = None,
    headers: Sequence[tuple[str, str]] | None = None,
) -> str:
    """HTTP GET请求

    Args:
        url: 网页地址
        params: 请求参数(例如： name='张三'&age=18)
        headers: 请求头, JSON格式(例如： {"Authorization": "Bearer xxxxxxx})

    Returns:
        网页内容
    """
    resp = DEFAULT_CLIENT.get(
        url, params=parse_qs(params) if params else None, headers=headers
    )
    return resp.text


# @function_tool
# def web_post(url: str,
#              content: Optional[str]=None,
#              json: Optional[Dict]=None,
#              params: Optional[Dict]=None,
#              headers: Optional[Dict]=None,
# ) -> str:
#     """HTTP POST请求

#     参数:
#         url: 网页地址
#         content: 请求内容
#         json: 提交JSON数据
#         params: 请求参数
#         headers: 请求头
#     返回值:
#         网页内容
#     """

#     resp = DEFAULT_CLIENT.post(url, content=content, json=json, params=params, headers=headers)
#     return resp.text
