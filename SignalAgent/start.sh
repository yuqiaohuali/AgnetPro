#!/bin/bash
# 启动钉钉机器人
poetry run dingtalk &
# 启动FastAPI服务
poetry run server &
# 等待所有后台进程
wait