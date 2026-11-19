"""Qdrant 客户端和集合操作。"""

from __future__ import annotations

from typing import Any

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from src.tools.rag.RAG_config import RAGConfig


class QdrantClientManager:
    """负责连接 Qdrant、创建集合和清理文档批次。"""

    def __init__(self, config: RAGConfig) -> None:
        """连接 Qdrant，并在首次使用时创建集合。"""

        self.collection_name = config.collection_name

        # 连接 Docker 或其他环境中的 Qdrant 服务。
        self.client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
            timeout=60,
        )

        self._ensure_collection(config.embedding_dimensions)

    def create_vector_store(self, embeddings: Any) -> QdrantVectorStore:
        """创建绑定当前集合和向量模型的向量存储。"""

        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=embeddings,
        )

    def delete_batch(self, batch_id: str) -> None:
        """删除指定批次，用于入库失败后的回滚。"""

        self._delete_by_filter(
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.batch_id",
                        match=models.MatchValue(value=batch_id),
                    )
                ]
            )
        )

    def delete_previous_batches(
        self,
        source_id: str,
        current_batch_id: str,
    ) -> None:
        """删除同一文件不属于当前批次的旧数据。"""

        self._delete_by_filter(
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source_id",
                        match=models.MatchValue(value=source_id),
                    )
                ],
                must_not=[
                    models.FieldCondition(
                        key="metadata.batch_id",
                        match=models.MatchValue(value=current_batch_id),
                    )
                ],
            )
        )

    def _ensure_collection(self, dimensions: int) -> None:
        """创建集合并固定向量维度，避免后续混写不兼容向量。"""

        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=dimensions,
                distance=models.Distance.COSINE,
            ),
        )

    def _delete_by_filter(self, filter_: models.Filter) -> None:
        """按元数据条件同步删除向量。"""

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=filter_),
            wait=True,
        )
