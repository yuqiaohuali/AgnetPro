"""RAG 文档入库。"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from src.tools.rag.Document_splitter import DocumentSplitter
from src.tools.rag.Qdrant_client import QdrantClientManager


logger = logging.getLogger(__name__)


class RAGIndexer:
    """负责读取、切分并安全更新单个文件的向量索引。"""

    def __init__(
        self,
        document_splitter: DocumentSplitter,
        vector_store: QdrantVectorStore,
        qdrant_client: QdrantClientManager,
    ) -> None:
        """组装文档处理器、向量存储和 Qdrant 清理器。"""

        self.document_splitter = document_splitter
        self.vector_store = vector_store
        self.qdrant_client = qdrant_client

        # 防止同一进程内多个线程同时更新同一个文件。
        self._index_lock = Lock()

    def index_file(self, file_path: str | Path) -> dict:
        """写入文件新批次，成功后删除该文件的旧批次。"""

        with self._index_lock:
            path, documents = self.document_splitter.load(file_path)
            chunks = self.document_splitter.split(documents)

            if not chunks:
                raise ValueError(f"文件没有可入库的内容：{path.name}")

            source_id = self._source_id(path)
            batch_id = str(uuid4())
            self._add_metadata(chunks, source_id, batch_id)

            try:
                self.vector_store.add_documents(
                    documents=chunks,
                    ids=[str(uuid4()) for _ in chunks],
                    batch_size=64,
                )
            except Exception:
                # 分批写入可能只成功一部分，失败时清理本次新增数据。
                try:
                    self.qdrant_client.delete_batch(batch_id)
                except Exception:
                    logger.exception("入库失败后的新批次清理也失败")

                raise

            # 新批次完整写入后再清理旧版本，避免更新过程中丢失可用数据。
            self.qdrant_client.delete_previous_batches(source_id, batch_id)

            return {
                "file_name": path.name,
                "document_count": len(documents),
                "chunk_count": len(chunks),
                "collection": self.qdrant_client.collection_name,
            }

    @staticmethod
    def _source_id(path: Path) -> str:
        """根据规范化绝对路径生成稳定的文件标识。"""

        source_key = os.path.normcase(str(path))
        return hashlib.sha256(source_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _add_metadata(
        chunks: list[Document],
        source_id: str,
        batch_id: str,
    ) -> None:
        """为每个文本片段补充文件和批次元数据。"""

        for index, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "source_id": source_id,
                    "batch_id": batch_id,
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                }
            )
