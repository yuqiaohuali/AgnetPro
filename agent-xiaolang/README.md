# agent-xiaolang

一个基于 Python、Poetry、LangChain 和钉钉 Stream SDK 的单智能体项目。项目包含 OpenAI 与 DeepSeek 模型客户端、钉钉消息接入、Agent 编排、SerpAPI 联网搜索、Qdrant 知识库检索、提示词上下文注入和会话记忆。

## 项目状态

- Python：`>=3.13,<4.0`
- 包管理：Poetry 2.x
- 虚拟环境：项目根目录下的 `.venv`
- 依赖锁定文件：`poetry.lock`
- 源码目录：`src`
- LLM 模块：`src/common/llm.py`
- Agent 模块：`src/agent/Agent_model.py`
- 提示词模块：`src/prompt/basic.py`
- 工具模块：`src/tools/`
- 钉钉接入模块：`src/dingding_service/`

## 目录结构

```text
agent-xiaolang/
├── .env                         # 本地密钥和服务配置，不提交到 Git
├── .gitignore                   # 忽略虚拟环境、密钥、缓存和构建产物
├── poetry.toml                  # Poetry 虚拟环境配置
├── pyproject.toml               # 项目元数据和依赖声明
├── poetry.lock                  # 锁定后的完整依赖版本
├── pyrightconfig.json           # Pyright/Pylance 源码和虚拟环境配置
├── .vscode/
│   ├── settings.json            # VS Code 解释器、终端和运行配置
│   └── launch.json              # 使用项目虚拟环境调试当前 Python 文件
├── files_store/
│   └── 公司信息.docx             # RAG 默认知识库源文件
└── src/
    ├── __init__.py
    ├── main.py                  # 精简的应用启动入口和业务回调
    ├── rw_document.py            # 将公司文档读取并写入 Qdrant
    ├── agent/
    │   └── Agent_model.py        # Agent、模型回退、工具和短期记忆组装
    ├── common/
    │   ├── __init__.py
    │   ├── filter_answer.py      # 统一处理模型文本和内容块结果
    │   └── llm.py                # OpenAI 和 DeepSeek 模型创建方法
    ├── langSmith/
    │   ├── __init__.py           # 导出 LangSmith 配置和线程标识方法
    │   └── tracing.py            # LangSmith 追踪配置和校验
    ├── prompt/
    │   └── basic.py              # 基础提示词和 RAG 上下文注入
    ├── memory/
    │   ├── _Run.py                # RAG 结果复用会话记忆
    │   └── resdis_memory.py       # Redis 会话持久化和上下文摘要
    ├── tools/
    │   ├── RAG_tool.py           # LangChain RAG 工具和会话记忆复用
    │   ├── rag/
    │   │   ├── __init__.py          # RAG 组件包
    │   │   ├── RAG_config.py        # 环境变量读取和 RAG 配置校验
    │   │   ├── Embedding_model.py   # OpenAI 文本向量模型
    │   │   ├── Qdrant_client.py     # Qdrant 连接、集合和批次清理
    │   │   ├── Document_splitter.py # 文档读取和文本切分
    │   │   ├── RAG_indexer.py       # 文档向量入库和版本更新
    │   │   ├── RAG_searcher.py      # MMR 检索和结果格式化
    │   │   └── RAG_service.py       # RAG 组件统一编排
    │   └── Serpapi.py            # SerpAPI 联网搜索工具
    └── dingding_service/
        ├── __init__.py          # 对外导出服务、存储和业务消息类型
        ├── config.py            # .env 加载、钉钉配置校验和日志初始化
        ├── service.py           # 钉钉 Stream 客户端和处理器组装
        ├── handler.py           # 消息解析、业务回调和 ACK 处理
        ├── replier.py           # 通过 sessionWebhook 回复文字
        ├── storage.py           # 用户与会话的内存存储
        └── model.py              # 用户、会话和业务消息数据模型
```

`.venv`、`__pycache__` 和 `.env` 已加入 `.gitignore`，不会作为项目代码提交。

## 依赖说明

项目依赖写在 `pyproject.toml` 中，并由 `poetry.lock` 锁定具体版本。主要依赖如下：

| 依赖 | 用途 |
| --- | --- |
| `langchain` | LangChain 核心能力 |
| `langchain-openai` | OpenAI 模型集成 |
| `langchain-deepseek` | DeepSeek 模型集成 |
| `langchain-text-splitters` | 文档文本切分 |
| `qdrant-client` | Qdrant 向量数据库客户端 |
| `langchain-qdrant` | LangChain 与 Qdrant 集成 |
| `python-docx` | 读取公司 Word 文档 |
| `openpyxl` | 读取 Excel 文档 |
| `pypdf` | 读取 PDF 文档 |
| `redis` | Redis 客户端 |
| `python-dotenv` | 从 `.env` 加载环境变量 |
| `dingtalk-stream` | 钉钉 Stream 长连接和机器人消息接入 |

代码中使用的是：

```python
from dotenv import load_dotenv
```

对应的安装包名称是 `python-dotenv`，不是 `dotenv`。

## 安装环境

### 1. 安装 Poetry

如果终端中已经可以使用 `poetry`，可跳过此步骤。Poetry 本身可以安装在用户工具环境中，项目业务依赖仍会安装到项目 `.venv`。

安装完成后检查：

```powershell
poetry --version
```

### 2. 安装项目依赖

在项目根目录执行：

```powershell
cd D:\study\python-proj\agent-xiaolang
poetry install
```

`poetry.toml` 已配置项目内虚拟环境。安装完成后，依赖应位于：

```text
D:\study\python-proj\agent-xiaolang\.venv
```

检查 Poetry 使用的环境：

```powershell
poetry env info
poetry env info --path
```

输出路径应指向项目下的 `.venv`。

## 使用虚拟环境运行

### 方式一：激活虚拟环境

PowerShell 中执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

成功后终端提示符前会出现 `(.venv)`，然后可以使用：

```powershell
python src\common\llm.py
```

如果 PowerShell 阻止脚本执行，可以只对当前进程放开策略：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 方式二：不激活，直接指定解释器

这种方式不会受到当前终端 Python 配置影响：

```powershell
.\.venv\Scripts\python.exe src\common\llm.py
```

也可以通过 Poetry 执行：

```powershell
poetry run python src\main.py
```

只检查 LLM 模块时执行：

```powershell
poetry run python src\common\llm.py
```

项目依赖始终应通过项目解释器或 `poetry run` 使用，不要用全局的 `D:\soft\python\python.exe` 运行项目文件。

## 环境变量配置

在项目根目录创建 `.env`。`.env` 已被 Git 忽略，不要提交真实 API Key。

模型相关变量示例：

```dotenv
OPENAI_API_KEY=替换为你的 OpenAI API Key
OPENAI_MODEL_NAME=gpt-5.6-sol
OPENAI_BASE_URL=https://你的 OpenAI 兼容接口地址/v1

DEEPSEEK_API_KEY=替换为你的 DeepSeek API Key
DEEPSEEK_MODEL_NAME=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

当前 `.env` 中还支持以下配置类别：

- Embedding：`OPENAI_EMBEDDING_API_KEY`、`OPENAI_EMBEDDING_BASE_URL`、`OPENAI_EMBEDDING_MODEL`
- LangSmith：`LANGSMITH_TRACING`、`LANGSMITH_API_KEY`、`LANGSMITH_PROJECT`
- Redis：`REDIS_URL`、`REDIS_MEMORY_KEY_PREFIX`、`REDIS_MEMORY_TTL_SECONDS`
- Agent 记忆：`CONTEXT_MAX_TOKENS`、`MEMORY_SUMMARY_TOKENS`
- Qdrant：`QDRANT_URL`、`QDRANT_COLLECTION`
- SerpAPI：`SERPAPI_API_KEY`、`SERPAPI_BASE_URL`
- RAG：`OPENAI_EMBEDDING_DIMENSIONS`、`RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`、`RAG_TOP_K`、`RAG_FETCH_K`、`RAG_LAMBDA_MULT`
- 钉钉：`DINGDING_ID`、`DINGDING_SECRET`、`DINGDING_UNION_ID`、`DINGDING_ROBOT_CODE`

### LangSmith 监控

在项目根目录 `.env` 中设置 `LANGSMITH_TRACING=true`、`LANGSMITH_API_KEY` 和 `LANGSMITH_PROJECT=agent-xiaolang-local`。`src/langSmith/tracing.py` 会在创建 Agent 时加载并校验配置，使用项目模式而不是测试版 Agent Address 路由；钉钉消息触发的运行会记录到 LangSmith，运行名称为 `xiaolang-agent`，并带有 `agent-xiaolang` 和 `dingtalk` 标签。LangGraph 使用原会话 ID 的稳定哈希作为线程标识，不会将原始钉钉用户和会话标识放进 trace。将 `LANGSMITH_TRACING` 设为 `false` 即可关闭追踪。

## LLM 模块

[src/common/llm.py](src/common/llm.py) 提供两个方法：

```python
from src.common.llm import getDeepseekModel, getOpenAIModel

openai_model = getOpenAIModel()
deepseek_model = getDeepseekModel()
```

模块会从项目根目录加载 `.env`。如果对应 API Key 不存在，会抛出明确的 `RuntimeError`。

当前 LangChain 版本使用 `model` 参数创建模型：

```python
ChatOpenAI(model="...")
ChatDeepSeek(model="...")
```

API Key 会转换为 `SecretStr`，以匹配当前 LangChain 类型定义。

验证依赖和模型客户端是否可导入：

```powershell
.\.venv\Scripts\python.exe -c "from src.common.llm import getOpenAIModel, getDeepseekModel; print(type(getOpenAIModel()).__name__); print(type(getDeepseekModel()).__name__)"
```

该命令只创建客户端，不会主动调用模型接口。

## Agent、工具和知识库

`src/agent/Agent_model.py` 使用 `create_agent` 组装小浪助手，包含以下能力：

- 主模型使用 OpenAI，调用失败时自动回退到 DeepSeek。
- `src/tools/Serpapi.py` 提供实时互联网搜索工具 `search`。
- `src/tools/RAG_tool.py` 提供本地知识库检索工具 `rag_search`，并复用会话中的历史检索结果。
- `src/tools/rag/` 将 RAG 配置、向量模型、Qdrant 客户端、文档入库和检索逻辑拆成独立类。
- `RedisMemory` 保存短期会话消息，按钉钉用户和 `session_id` 双重隔离；超出上下文预算时会归纳较早对话。

上下文预算默认 `6000`，摘要预算默认 `800`，完成响应后将历史和摘要写入 Redis。token 使用消息结构和文本长度估算，并为模型输出、工具参数预留空间；不同模型部署应根据实际窗口调整 `CONTEXT_MAX_TOKENS`。`REDIS_MEMORY_TTL_SECONDS` 默认为 `0`（不自动过期），可设置正整数启用会话过期。

### 提示词和 RAG 上下文

`src/prompt/basic.py` 中的 `BasicPrompt` 类负责生成基础系统提示词。Agent 每次调用模型前，动态提示词中间件会检查当前轮次的消息：如果已经执行过 `rag_search`，就把工具返回的 JSON 资料追加到 `<rag_context>` 中，作为本次模型回答的上下文。

RAG 结果同时会被保存为 Agent 会话中的 `ToolMessage`。重复问题再次触发 `rag_search` 时，工具会根据当前会话中最新的原始用户问题，向历史消息查找相同问题对应的 RAG 结果。命中后直接复用历史结果，不再访问 Qdrant；模型改写工具检索词不会影响这项缓存判断。

### RAG 模块拆分

`src/tools/RAG_tool.py` 现在只负责 LangChain 工具适配和会话记忆复用，具体工作由 `src/tools/rag/` 下的类完成：

- `RAGConfig` 统一读取 `.env` 中的向量模型、Qdrant、切分和检索参数，并在启动时校验参数关系。
- `EmbeddingModel` 创建 OpenAI 文本向量模型。
- `QdrantClientManager` 负责连接 Qdrant、首次创建集合，以及按文件批次删除旧数据。
- `DocumentSplitter` 复用 `DocumentReader` 读取文件，再按配置切分文本片段。
- `RAGIndexer` 为片段补充文件和批次元数据，执行新批次写入、失败回滚和旧批次清理。
- `RAGSearcher` 执行 MMR 检索，并将结果整理为带来源信息的 JSON。
- `RAGService` 只负责组装这些组件，对外提供 `index_file`、`search` 和 `search_context` 方法。

入库流程是“读取文件 → 切分文本 → 写入新批次 → 删除旧批次”；检索流程是“问题 → 向量检索 → MMR 筛选 → 返回带来源的候选资料”。

### 公司文档入库

RAG 查询不会在每次调用时读取 Word 文件。默认文档是：

```text
files_store/公司信息.docx
```

首次使用或更新文档后，在项目根目录执行一次入库：

```powershell
.\.venv\Scripts\python.exe src\rw_document.py
```

该脚本会读取文档、切分文本、写入 Qdrant，并删除同一文件的旧版本片段。之后 Agent 的 `rag_search` 只查询已经建立的向量索引。

Qdrant 服务需要先启动，并且 `.env` 中的 `OPENAI_EMBEDDING_*`、`QDRANT_*` 配置必须有效。

### 启动 Agent 服务

完成依赖安装、环境变量配置和文档入库后，在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe src\main.py
```

## 钉钉服务入口

`src/dingding_service` 负责钉钉接入层的基础设施，包括：

- 加载项目根目录 `.env` 中的 `DINGDING_ID` 和 `DINGDING_SECRET`
- 初始化统一日志格式
- 创建默认的 `UserStorage`
- 注册钉钉消息处理器和回复器
- 启动钉钉 Stream 长连接

`src/main.py` 只保留业务消息回调和服务启动代码。配置加载、日志初始化、`UserStorage` 创建和钉钉 SDK 组装都由 `DingDingService` 完成，消息回调会将问题交给复用的 Agent：

```python
from functools import lru_cache

from src.agent.Agent_model import AgentModel
from src.common.filter_answer import filterAnswer
from src.dingding_service import DingDingService, UserMessage


@lru_cache(maxsize=1)
def get_agent_model() -> AgentModel:
    return AgentModel()


async def handle_message(message: UserMessage) -> str:
    question = message.text[:500]
    agent_model = get_agent_model()
    response = agent_model.agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": message.session_id}},
        context={
            "user_id": message.user.user_key,
            "session_id": message.session_id,
        },
    )
    answer = filterAnswer(response["messages"][-1].content)
    return f"你好，{message.user.nickname}！我是小浪助手。\n{answer}"


def main() -> None:
    dingding = DingDingService(on_message=handle_message)

    try:
        dingding.start()
    except KeyboardInterrupt:
        dingding.logger.info("小浪助手已停止。")


if __name__ == "__main__":
    main()
```

`DingDingService` 会自动读取配置并创建存储，不需要在 `main.py` 中重复加载 `.env`、配置日志或创建 `UserStorage`。Agent 使用用户标识与 `message.session_id` 从 Redis 恢复对应会话；服务重启后仍可继续已有会话。

### 消息处理流程

1. `DingDingHandler` 接收钉钉 Stream 回调。
2. 将钉钉 `ChatbotMessage` 转换为项目内部的 `UserMessage`。
3. `UserStorage` 根据机器人、企业、发送者和会话信息创建或复用用户会话。
4. 同一会话通过异步锁串行处理，不同会话可以并发处理。
5. `handle_message` 使用用户标识和会话 `session_id` 调用 Agent，Redis 据此恢复独立记忆，Agent 根据问题选择普通回答、联网搜索或知识库检索。
6. 将 Agent 返回的文字通过 `sessionWebhook` 回复给用户。
7. 回复成功后更新会话回复次数并返回钉钉 ACK。

成功日志包含当前会话用户昵称、钉钉 `senderId` 和当前会话回复次数，例如：

```text
当前会话用户：张三；当前会话用户ID：sender-id；当前会话回复次数=1
```

## VS Code 配置

项目的 `.vscode/settings.json` 已配置：

- 默认解释器为 `${workspaceFolder}\\.venv\\Scripts\\python.exe`
- 新建 PowerShell 终端时自动执行 `.venv\\Scripts\\Activate.ps1`
- `PYTHONPATH` 包含 `src`
- Code Runner 使用项目 `.venv` 中的 Python

如果右上角运行按钮仍执行全局 Python：

1. 执行 `Python: Select Interpreter`。
2. 选择 `poetry (3.13.16) .\\.venv\\Scripts\\python.exe`，或选择“使用 `python.defaultInterpreterPath` 设置中的 Python”。
3. 执行 `Developer: Reload Window`。
4. 关闭旧终端后重新创建终端。

也可以按 `F5`，选择配置：

```text
运行当前 Python 文件（项目虚拟环境）
```

终端验证命令：

```powershell
python -c "import sys; print(sys.executable)"
```

正确输出应为：

```text
D:\study\python-proj\agent-xiaolang\.venv\Scripts\python.exe
```

如果输出 `D:\soft\python\python.exe`，说明当前运行入口仍然使用全局解释器。

## 常用检查命令

```powershell
# 检查依赖是否安装在项目虚拟环境
.\.venv\Scripts\python.exe -c "import dotenv, langchain_deepseek, langchain_openai; print('dependencies ok')"

# 检查钉钉接入模块
.\.venv\Scripts\python.exe -c "from dingding_service import DingDingService, UserMessage; print('dingding service ok')"

# 检查 Poetry 配置
poetry check

# 查看已安装依赖
poetry show

# 编译检查源码
.\.venv\Scripts\python.exe -m compileall -q src
```

## 依赖更新

修改 `pyproject.toml` 后重新生成锁文件并安装：

```powershell
poetry lock
poetry install
```

日常安装应优先使用：

```powershell
poetry install
```

这样可以按照 `poetry.lock` 安装一致的依赖版本。

## 当前限制

当前仓库已经实现钉钉 Stream 接入、Agent 工具调用、Qdrant 向量检索和提示词上下文注入，但仍有以下限制：

- Redis 会话记忆默认不自动过期；生产部署可通过 `REDIS_MEMORY_TTL_SECONDS` 设置保留周期，并配置 Redis 持久化、访问控制和备份策略。
- RAG 重复问题缓存按同一会话中的原始问题匹配，只处理规范化后的文本，不支持语义相似问题。
- 更新 `files_store/公司信息.docx` 后需要重新执行 `src/rw_document.py`；已有会话历史中的旧 RAG 结果可能继续被复用。
- Qdrant 和 SerpAPI 依赖外部服务及有效配置，未配置时对应工具无法正常工作。
