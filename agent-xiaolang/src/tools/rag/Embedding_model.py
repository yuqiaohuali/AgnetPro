"""RAG 文本向量模型。"""

from langchain_openai import OpenAIEmbeddings

from src.tools.rag.RAG_config import RAGConfig


class EmbeddingModel:
    """创建用于文档入库和查询的 OpenAI 向量模型。"""

    def __init__(self, config: RAGConfig) -> None:
        """根据统一配置初始化向量模型。"""

        # 向量模型只负责把文本转换成向量，不负责聊天回答。
        self.embeddings = OpenAIEmbeddings(
            model=config.embedding_model,
            api_key=config.embedding_api_key,
            base_url=config.embedding_base_url,
            dimensions=config.embedding_dimensions,
            max_retries=2,
            timeout=60,
        )
