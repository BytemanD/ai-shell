import sqlite3
from typing import Any, Dict, Tuple

from agents import function_tool

# 全局数据库连接（在 Agent 对话期间保持）
_global_conn = None


@function_tool
def connect_db(db_path: str = ":memory:") -> str:
    """
    建立 SQLite 数据库连接，并保存为全局连接（供后续 execute_sql 使用）。

    Args:
        db_path: 数据库文件路径，默认为内存数据库（:memory:）

    Returns:
        状态信息，例如 "Connected to database: test.db"
    """
    global _global_conn
    if _global_conn:
        _global_conn.close()
    _global_conn = sqlite3.connect(db_path)
    _global_conn.row_factory = sqlite3.Row
    return f"Connected to database: {db_path}"


@function_tool
def execute_sql(
    sql: str, parameters: Tuple[Any, ...] = ()
) -> Dict[str, Any]:
    """
    执行任意 SQL 语句（SELECT / INSERT / UPDATE / DELETE / CREATE TABLE 等）。
    自动提交事务，如果尚未连接则自动连接内存数据库。

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
        # 未调用 connect 时自动连接内存数据库
        connect_db(":memory:")

    cursor = _global_conn.cursor()
    try:
        cursor.execute(sql, parameters or ())

        # 判断是否是 SELECT 查询
        if sql.strip().upper().startswith("SELECT"):
            return {'rows': [dict(x) for x in cursor.fetchall()]}
        else:
            _global_conn.commit()
            last_id = cursor.lastrowid
            return {
                "affected_rows": cursor.rowcount,
                "last_row_id": last_id if last_id != 0 else None,
            }
    except Exception as e:
        _global_conn.rollback()
        raise RuntimeError(f"SQL execution failed: {e}") from e
