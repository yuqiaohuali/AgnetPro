"""RAG 组件编排服务。"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from src.tools.rag.Document_splitter import DocumentSplitter
from src.tools.rag.Embedding_model import EmbeddingModel
from src.tools.rag.Qdrant_client import QdrantClientManager
from src.tools.rag.RAG_config import RAGConfig
from src.tools.rag.RAG_indexer import RAGIndexer
from src.tools.rag.RAG_searcher import RAGSearcher


class RAGService:
    """组装配置、向量模型、Qdrant、入库和检索组件。"""

    def __init__(self) -> None:
        """初始化一次 RAG 服务及其全部依赖。"""

        self.config = RAGConfig.from_env()
        self.embedding_model = EmbeddingModel(self.config)
        self.qdrant_client = QdrantClientManager(self.config)
        self.vector_store = self.qdrant_client.create_vector_store(
            self.embedding_model.embeddings
        )
        self.document_splitter = DocumentSplitter(self.config)
        self.indexer = RAGIndexer(
            document_splitter=self.document_splitter,
            vector_store=self.vector_store,
            qdrant_client=self.qdrant_client,
        )
        self.searcher = RAGSearcher(self.vector_store, self.config)

        # 保留原服务对象的常用属性，方便已有代码平滑迁移。
        self.collection_name = self.config.collection_name
        self.embeddings = self.embedding_model.embeddings
        self.client = self.qdrant_client.client
        self.reader = self.document_splitter.reader
        self.splitter = self.document_splitter.splitter
        self.retriever = self.searcher.retriever

    def index_file(self, file_path: str | Path) -> dict:
        """导入或更新一个文件的向量索引。"""

        return self.indexer.index_file(file_path)

    def search(self, query: str) -> list[Document]:
        """检索相关文档片段。"""

        return self.searcher.search(query)

    def search_context(self, query: str) -> str:
        """检索并生成 Agent 使用的 JSON 上下文。"""

        return self.searcher.search_context(query)
