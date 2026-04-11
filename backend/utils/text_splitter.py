from __future__ import annotations

from langchain_text_splitters import CharacterTextSplitter

# 创建一个文本分割器，使用换行符作为分隔符，将文本分割成指定大小的块，并允许一定程度的重叠，以便在处理长文本时保持上下文连贯性和信息完整性
def create_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 120) -> CharacterTextSplitter:
    return CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
