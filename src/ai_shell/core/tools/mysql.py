from typing import Any, Dict, Optional, Tuple

import pymysql
from agents import function_tool

_global_conn = None


@function_tool
def connect_db(
    user: str = "root",
    password: Optional[str] = None,
    host: str = "localhost",
    port: int = 3306,
    database: Optional[str]=None,
    charset: str = "utf8mb4",
    autocommit: bool=True,
) -> str:
    """
    建立 Mysql 数据库连接，并保存为全局连接（供后续 execute_sql 使用）。

    Args:
        user: 数据库用户名
        password: 密码
        host: 数据库主机地址
        port: 数据库端口号
        database: 数据库名称
        charset: 编码
        autocommit: 是否自动提交

    Returns:
        状态信息，例如 "Connected to database: DATABASE(host)"
    """
    global _global_conn

    _global_conn = pymysql.connect(
        database=database,
        host=host,
        user=user,
        password=password,
        port=port,
        charset=charset,
        autocommit=autocommit,
    )

@function_tool
def execute_sql(sql: str, parameters: Tuple[Any, ...] = ()) -> Dict[str, Any]:
    """执行Mysql SQL 语句
    
    Args:
        sql: SQL 语句，使用 ? 或 :name 占位符防止注入
        parameters: 可选参数，与占位符匹配

    Returns:
        - 对于 SELECT 语句：返回 {"rows": [...]}
        - 对于非 SELECT 语句：返回 {"affected_rows": 影响行数, "last_row_id": 最后插入行的ID（若适用）}

    Example:
        execute_sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        execute_sql("INSERT INTO users (name) VALUES (?)", ("Alice",))
        result = execute_sql("SELECT * FROM users")  # 得到查询结果
    """
    global _global_conn

    if _global_conn is None:
        raise Exception("数据库未连接")

    cursor = _global_conn.cursor()

    try:
        cursor.execute(sql, parameters or ())

        # 判断是否是 SELECT 查询
        if sql.strip().upper().startswith("SELECT"):
            return {'rows': [dict(x) for x in cursor.fetchall()]}
        else:
            if not _global_conn.autocommit_mode:
                _global_conn.commit()

            last_id = cursor.lastrowid
            return {
                "affected_rows": cursor.rowcount,
                "last_row_id": last_id if last_id != 0 else None,
            }
    except Exception as e:
        _global_conn.rollback()
        raise RuntimeError(f"SQL execution failed: {e}") from e
