from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

from charset_normalizer import from_bytes
from docx import Document as WordDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from langchain_core.documents import Document
from openpyxl import load_workbook
from pypdf import PdfReader


class DocumentReader:
    """根据文件扩展名选择读取方式，统一返回 LangChain Document。"""

    SUPPORTED_SUFFIXES = {
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".pdf",
        ".txt",
        ".md",
        ".csv",
    }

    def __init__(self, libreoffice_path: str | None = None):
        self.libreoffice_path = (
            libreoffice_path
            or os.getenv("LIBREOFFICE_PATH")
            or shutil.which("soffice")
        )

    def load(self, file_path: str | Path) -> list[Document]:
        """读取单个文件，并补充统一的来源信息。"""

        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(f"文件不存在：{path}")

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_SUFFIXES:
            raise ValueError(f"不支持的文件类型：{suffix}")

        if suffix == ".docx":
            documents = self._read_docx(path)
        elif suffix == ".xlsx":
            documents = self._read_xlsx(path)
        elif suffix == ".pdf":
            documents = self._read_pdf(path)
        elif suffix in {".doc", ".xls"}:
            documents = self._read_legacy_office(path)
        else:
            documents = self._read_text(path)

        # 清理空内容，并保留原始文件的信息。
        # 即使 .doc 转成了临时 .docx，来源仍然是原始 .doc 文件。
        result: list[Document] = []

        for document in documents:
            document.page_content = document.page_content.strip()

            if not document.page_content:
                continue

            document.metadata.update(
                {
                    "source": str(path),
                    "file_name": path.name,
                    "file_type": suffix,
                }
            )
            result.append(document)

        if not result:
            raise ValueError(
                f"没有提取到有效文本：{path.name}。"
                "如果是扫描版 PDF，需要先进行 OCR。"
            )

        return result

    def _read_text(self, path: Path) -> list[Document]:
        """优先使用 UTF-8，失败后自动推测编码。"""

        raw = path.read_bytes()

        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            detected = from_bytes(raw).best()

            if detected is None:
                raise ValueError(f"无法识别文本编码：{path.name}")

            text = str(detected)

        return [Document(page_content=text)]

    def _read_docx(self, path: Path) -> list[Document]:
        """按正文顺序读取段落和表格，不处理页眉、图片、文本框。"""

        word = WordDocument(str(path))
        parts: list[str] = []

        # 遍历 XML 正文节点，保留段落与表格的相对顺序。
        for element in word.element.body:
            tag = element.tag.rsplit("}", 1)[-1]

            if tag == "p":
                paragraph = Paragraph(element, word)
                text = paragraph.text.strip()

                if text:
                    parts.append(text)

            elif tag == "tbl":
                table = Table(element, word)

                for row in table.rows:
                    cells = [
                        cell.text.strip().replace("\n", "；")
                        for cell in row.cells
                    ]
                    if any(cells):
                        parts.append(" | ".join(cells))

        return [
            Document(
                page_content="\n".join(parts),
                metadata={"section": "正文"},
            )
        ]

    def _read_xlsx(self, path: Path) -> list[Document]:
        """
        按行生成 Document。

        第一条非空行视为表头。
        每条数据都携带列名，避免拆分后只剩数字、不知道数字含义。
        """

        workbook = load_workbook(
            filename=path,
            read_only=True,
            data_only=True,
        )

        documents: list[Document] = []

        try:
            for sheet in workbook.worksheets:
                headers: list[str] | None = None

                for row_number, row in enumerate(
                    sheet.iter_rows(values_only=True),
                    start=1,
                ):
                    values = [
                        "" if value is None else str(value).strip()
                        for value in row
                    ]

                    if not any(values):
                        continue

                    if headers is None:
                        headers = [
                            value or f"第{index + 1}列"
                            for index, value in enumerate(values)
                        ]
                        continue

                    fields = []

                    for index, value in enumerate(values):
                        if not value:
                            continue

                        column = (
                            headers[index]
                            if index < len(headers)
                            else f"第{index + 1}列"
                        )
                        fields.append(f"{column}：{value}")

                    documents.append(
                        Document(
                            page_content=(
                                f"工作表：{sheet.title}\n"
                                + "\n".join(fields)
                            ),
                            metadata={
                                "sheet": sheet.title,
                                "row": row_number,
                            },
                        )
                    )
        finally:
            workbook.close()

        return documents

    def _read_pdf(self, path: Path) -> list[Document]:
        """按页读取 PDF，页码从 1 开始，方便最终引用。"""

        reader = PdfReader(str(path))
        documents: list[Document] = []
        empty_pages: list[int] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                empty_pages.append(page_number)
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={"page": page_number},
                )
            )

        if empty_pages:
            warnings.warn(
                f"{path.name} 以下页面未提取到文本：{empty_pages}。"
                "可能是空白页或需要 OCR 的扫描页。",
                stacklevel=2,
            )

        return documents

    def _read_legacy_office(self, path: Path) -> list[Document]:
        """将旧版 .doc / .xls 转为现代格式，再复用读取逻辑。"""

        if not self.libreoffice_path:
            raise RuntimeError(
                f"读取 {path.suffix} 需要安装 LibreOffice，"
                "并配置 LIBREOFFICE_PATH。"
            )

        target_suffix = "docx" if path.suffix.lower() == ".doc" else "xlsx"

        with tempfile.TemporaryDirectory(prefix="rag_office_") as directory:
            temp_dir = Path(directory)

            # 使用独立的 LibreOffice 用户配置目录，
            # 避免与桌面已打开的 LibreOffice 进程共用配置。
            profile_uri = (temp_dir / "profile").as_uri()

            completed = subprocess.run(
                [
                    self.libreoffice_path,
                    f"-env:UserInstallation={profile_uri}",
                    "--headless",
                    "--convert-to",
                    target_suffix,
                    "--outdir",
                    str(temp_dir),
                    str(path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )

            converted = temp_dir / f"{path.stem}.{target_suffix}"

            if completed.returncode != 0 or not converted.is_file():
                raise RuntimeError(
                    f"文件转换失败：{path.name}\n"
                    f"{completed.stdout}\n{completed.stderr}"
                )

            if target_suffix == "docx":
                return self._read_docx(converted)

            return self._read_xlsx(converted)