"""RAG 运行配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr


# 当前文件位于 src/tools/rag，向上四级得到项目根目录。
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env", override=False)


@dataclass(frozen=True)
class RAGConfig:
    """集中保存 RAG 各组件共享的配置。"""

    collection_name: str  # Qdrant 集合名称。
    embedding_api_key: SecretStr  # OpenAI 向量模型密钥。
    embedding_model: str  # OpenAI 向量模型名称。
    embedding_base_url: str  # OpenAI 向量接口地址。
    embedding_dimensions: int  # 向量维度，必须与 Qdrant 集合一致。
    qdrant_url: str  # Qdrant 服务地址。
    qdrant_api_key: str | None  # Qdrant 服务密钥，本地服务可以为空。
    chunk_size: int  # 文本片段最大字符数。
    chunk_overlap: int  # 相邻文本片段的重叠字符数。
    top_k: int  # MMR 最终返回的片段数量。
    fetch_k: int  # MMR 初始候选片段数量。
    lambda_mult: float  # MMR 相关性与多样性的平衡系数。

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """从环境变量创建并校验 RAG 配置。"""

        embedding_api_key = os.getenv("OPENAI_EMBEDDING_API_KEY")
        if not embedding_api_key:
            raise ValueError("缺少 OPENAI_EMBEDDING_API_KEY")

        config = cls(
            collection_name=os.getenv(
                "QDRANT_COLLECTION",
                "xiaolang_knowledge",
            ),
            embedding_api_key=SecretStr(embedding_api_key),
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                "text-embedding-3-small",
            ),
            embedding_base_url=os.getenv(
                "OPENAI_EMBEDDING_BASE_URL",
                "https://api.openai.com/v1",
            ),
            embedding_dimensions=int(
                os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")
            ),
            qdrant_url=os.getenv(
                "QDRANT_URL",
                "http://127.0.0.1:6333",
            ),
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "150")),
            top_k=int(os.getenv("RAG_TOP_K", "4")),
            fetch_k=int(os.getenv("RAG_FETCH_K", "20")),
            lambda_mult=float(os.getenv("RAG_LAMBDA_MULT", "0.5")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """检查文本切分、检索和向量配置是否满足约束。"""

        if self.embedding_dimensions <= 0:
            raise ValueError("OPENAI_EMBEDDING_DIMENSIONS 必须大于 0")

        if self.chunk_size <= 0 or not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError(
                "必须满足 0 <= RAG_CHUNK_OVERLAP < RAG_CHUNK_SIZE，"
                "且 RAG_CHUNK_SIZE > 0"
            )

        if self.top_k <= 0 or self.fetch_k < self.top_k:
            raise ValueError("必须满足 RAG_FETCH_K >= RAG_TOP_K > 0")

        if not 0 <= self.lambda_mult <= 1:
            raise ValueError("RAG_LAMBDA_MULT 必须在 0~1 之间")
