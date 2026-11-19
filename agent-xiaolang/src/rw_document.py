"""将公司文档读取并写入 RAG 向量库。"""

from __future__ import annotations

import sys
from pathlib import Path


# 允许直接执行 `python src/rw_document.py` 时导入项目包。
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.RAG_tool import get_rag_service


# 公司知识库源文件，文件更新后重新执行本文件即可刷新向量库。
COMPANY_DOCUMENT = PROJECT_ROOT / "files_store" / "公司信息.docx"


def index_company_document(
    file_path: str | Path = COMPANY_DOCUMENT,
) -> dict:
    """读取公司文档并更新其在 Qdrant 中的索引。"""

    return get_rag_service().index_file(file_path)


def main() -> None:
    """执行公司文档入库并输出结果。"""

    result = index_company_document()
    print(
        f"已完成文档入库：{result['file_name']}，"
        f"共生成 {result['chunk_count']} 个文本片段。"
    )


if __name__ == "__main__":
    main()
