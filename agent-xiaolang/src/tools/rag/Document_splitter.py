"""RAG 文档读取和文本切分。"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.common.document_reader import DocumentReader
from src.tools.rag.RAG_config import RAGConfig


class DocumentSplitter:
    """读取文件并按配置切分为可入库的文本片段。"""

    def __init__(self, config: RAGConfig) -> None:
        """初始化文档读取器和递归文本切分器。"""

        self.reader = DocumentReader()

        # 优先按段落和换行切分，再逐步退化到标点、空格和字符。
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                "。",
                "！",
                "？",
                "；",
                " ",
                "",
            ],
        )

    def load(self, file_path: str | Path) -> tuple[Path, list[Document]]:
        """读取文件并返回规范化路径和原始文档列表。"""

        path = Path(file_path).expanduser().resolve()
        return path, self.reader.load(path)

    def split(self, documents: list[Document]) -> list[Document]:
        """将读取到的文档切分成向量片段。"""

        return self.splitter.split_documents(documents)
