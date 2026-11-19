# FROM docker.1ms.run/python:3.14.6

# # 设置工作目录
# WORKDIR /app

# # 设置环境变量
# ENV PYTHONFAULTHANDLER=1 \
#     PYTHONUNBUFFERED=1 \
#     PYTHONHASHSEED=random \
#     PIP_NO_CACHE_DIR=off  \
#     PIP_DISABLE_PIP_VERSION_CHECK=on  \
#     POETRY_VERSION=2.4.1

# # 安装 poetry
# RUN pip install "poetry==$POETRY_VERSION"

# # 配置poetry不创建虚拟环境
# RUN poetry config virtualenvs.create false

# # 安装 ping 和 curl 命令
# RUN  apt-get update && apt-get install -y iputils-ping curl

# # 复制项目文件
# COPY pyproject.toml poetry.lock* /app/

# # 复制应用代码
# COPY . /app/

# # 安装依赖RUN poetry install --no-interaction
# RUN poetry install

# # 创建启动脚本并设置执行权限
# COPY start.sh /app/
# RUN chmod +x /app/start.sh

# # 暴露需要的端口
# EXPOSE 8000

# # 启动命令
# CMD [ "/app/start.sh" ]


FROM docker.1ms.run/python:3.14.6

# 1. 设置工作目录
WORKDIR /app

# 2. 设置环境变量
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=2.4.1

# 3. 安装 Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# 4. 配置 Poetry 不创建虚拟环境 (容器本身就是隔离环境)
RUN poetry config virtualenvs.create false

# 5. 安装系统工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping curl && \
    rm -rf /var/lib/apt/lists/*

# ==========================================
# 🌟 关键优化：利用 Docker 缓存层加速构建
# ==========================================

# 6. 仅复制依赖配置文件
COPY pyproject.toml poetry.lock* ./

# 7. 仅安装第三方依赖，不安装当前项目 (--no-root)
RUN poetry install --no-interaction --no-ansi --no-root

# 8. 最后复制应用源代码
COPY . .

# 9. 🌟 安装当前项目本身 (此时会正确识别 src 目录，并生成 dingtalk/server 命令)
RUN poetry install --no-interaction --no-ansi

# ==========================================

# 创建启动脚本并设置执行权限
COPY start.sh /app/
RUN chmod +x /app/start.sh

# 暴露需要的端口
EXPOSE 8000

# 启动命令
CMD [ "/app/start.sh" ]