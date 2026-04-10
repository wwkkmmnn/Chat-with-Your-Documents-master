from __future__ import annotations

from langchain_text_splitters import CharacterTextSplitter


def create_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 120) -> CharacterTextSplitter:
    return CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
