from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from backend.utils.file_parser import parse_file
from backend.utils.text_splitter import create_text_splitter


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    slug = re.sub(r"[^0-9A-Za-z._-]+", "_", stem).strip("._")
    return slug or "document"


class RagService:
    def __init__(
        self,
        uploads_dir: Path,
        parsed_dir: Path,
        indexes_dir: Path,
        files_metadata_path: Path,
        embeddings_model_name: str,
        chunk_size: int,
        chunk_overlap: int,
        max_search_results: int,
    ) -> None:
        self.uploads_dir = Path(uploads_dir)
        self.parsed_dir = Path(parsed_dir)
        self.indexes_dir = Path(indexes_dir)
        self.files_metadata_path = Path(files_metadata_path)
        self.embeddings_model_name = embeddings_model_name
        self.max_search_results = max_search_results
        self._splitter = create_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self._lock = threading.RLock()
        self._embeddings: HuggingFaceEmbeddings | None = None
        self._store_cache: dict[str, FAISS] = {}

        for directory in (
            self.uploads_dir,
            self.parsed_dir,
            self.indexes_dir,
            self.files_metadata_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        if not self.files_metadata_path.exists():
            self._write_metadata({"files": []})

    def list_files(self) -> list[dict[str, Any]]:
        with self._lock:
            files = self._read_metadata()["files"]
            return sorted(files, key=lambda item: item["uploadedAt"], reverse=True)

    def ingest_file(self, filename: str, content: bytes) -> dict[str, Any]:
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".txt", ".docx"}:
            raise ValueError("Only PDF, TXT, and DOCX files are supported.")

        file_id = f"file_{uuid.uuid4().hex[:10]}"
        stored_name = f"{file_id}_{_safe_stem(filename)}{suffix}"
        upload_path = self.uploads_dir / stored_name
        upload_path.write_bytes(content)

        documents = parse_file(upload_path)
        if not documents:
            raise ValueError("No readable content found in the uploaded file.")

        for document in documents:
            document.metadata["file_id"] = file_id
            document.metadata["source"] = filename

        chunks = self._splitter.split_documents(documents)
        if not chunks:
            raise ValueError("Document was parsed but produced no searchable chunks.")

        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
            chunk.metadata.setdefault("source", filename)

        parsed_text = "\n\n".join(doc.page_content for doc in documents)
        (self.parsed_dir / f"{file_id}.txt").write_text(parsed_text, encoding="utf-8")

        vector_store = FAISS.from_documents(chunks, self.embeddings)
        index_dir = self.indexes_dir / file_id
        index_dir.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(index_dir))

        file_record = {
            "id": file_id,
            "name": filename,
            "storedName": stored_name,
            "uploadedAt": _utc_now(),
            "chunkCount": len(chunks),
            "pageCount": len(documents),
            "indexPath": str(index_dir),
            "sourcePath": str(upload_path),
        }

        with self._lock:
            metadata = self._read_metadata()
            metadata["files"].append(file_record)
            self._write_metadata(metadata)
            self._store_cache[file_id] = vector_store

        return file_record

    def search(
        self,
        query: str,
        file_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        selected_files = self._resolve_selected_files(file_ids)
        if not selected_files:
            return []

        k = top_k or self.max_search_results
        all_results: list[dict[str, Any]] = []

        for file_record in selected_files:
            vector_store = self._load_store(file_record)
            for document, score in vector_store.similarity_search_with_score(query, k=k):
                page_value = document.metadata.get("page")
                page_number = page_value + 1 if isinstance(page_value, int) else page_value
                all_results.append(
                    {
                        "fileId": file_record["id"],
                        "fileName": file_record["name"],
                        "score": float(score),
                        "page": page_number,
                        "snippet": document.page_content.strip(),
                        "source": document.metadata.get("source", file_record["name"]),
                    }
                )

        all_results.sort(key=lambda item: item["score"])
        return all_results[:k]

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model_name)
        return self._embeddings

    def _resolve_selected_files(self, file_ids: list[str] | None) -> list[dict[str, Any]]:
        files = self.list_files()
        if not file_ids:
            return files
        selected_ids = set(file_ids)
        return [item for item in files if item["id"] in selected_ids]

    def _load_store(self, file_record: dict[str, Any]) -> FAISS:
        file_id = file_record["id"]
        with self._lock:
            cached = self._store_cache.get(file_id)
            if cached is not None:
                return cached

            vector_store = FAISS.load_local(
                file_record["indexPath"],
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self._store_cache[file_id] = vector_store
            return vector_store

    def _read_metadata(self) -> dict[str, Any]:
        with self.files_metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_metadata(self, metadata: dict[str, Any]) -> None:
        with self.files_metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=2)
