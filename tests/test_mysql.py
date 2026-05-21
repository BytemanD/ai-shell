
from ai_shell.core.tools import mysql

mysql.connect_db(password="root123")

print(mysql.execute_sql("show databases"))
