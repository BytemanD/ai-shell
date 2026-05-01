# import io
# import logging
# import subprocess
# import sys

# import dotenv
# from agents import set_tracing_disabled

# logging.basicConfig(level=logging.INFO)
# dotenv.load_dotenv()

# set_tracing_disabled(True)

# from rich.console import Console


# class MultyWriter:
    
#     def __init__(self, *writers):
#         self.writeres = writers

#     # def write(self, data):
#     #     print("yyyyyyyyyyyyyyyy")
#     #     for writer in self.writeres:
#     #         writer.write(data)
#     #         writer.flush()
#     # def read(self, data):
#     #     print("xxxxxxxxxxxxxx")
#     #     for writer in self.writeres:
#     #         writer.read(data)

#     def fileno(self):
#         return self.writeres[0].fileno()

#     def flush(self):
#         for writer in self.writeres:
#             if hasattr(writer, "flush"):
#                 writer.flush()


# console = Console()

# binary_buffer = io.StringIO()

# multi_writer =  MultyWriter(sys.stdout, binary_buffer)

# # status, stdout, stderr = system.execute('dir')
# # proc = subprocess.run("dir", shell=True)
# proc = subprocess.Popen(
#     "ls",
#     shell=True,
#     stdout=111,
#     stderr=subprocess.STDOUT,
#     text=True,
#     bufsize=1
# )
# print('111111111111111111')
# proc.communicate()
# print('2222222222222222')

# # print(stdout)
# # print(stdrrr)
# # for line in proc.stdout:
# #     multi_writer.write(line)

# print('==================')
# binary_buffer.write("111111111")
# print(binary_buffer.getvalue())

# sys.stdout.write("helloworld")

from typing import Literal

from pydantic import BaseModel


class User(BaseModel):
    role: Literal["admin", "user", "tool"]


User(role="xxx")