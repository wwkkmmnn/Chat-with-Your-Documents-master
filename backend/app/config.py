from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _default_allowed_origins() -> tuple[str, ...]:
    raw_value = os.getenv("CHATDOC_ALLOWED_ORIGINS", "")
    if raw_value:
        origins = [item.strip() for item in raw_value.split(",") if item.strip()]
        if origins:
            return tuple(origins)
    return ("http://localhost:5173", "http://127.0.0.1:5173")


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "Multi Tool AI Assistant"
    app_version: str = "2.0.0"
    project_root: Path = PROJECT_ROOT
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    embeddings_model_name: str = os.getenv(
        "EMBEDDINGS_MODEL_NAME",
        "sentence-transformers/all-mpnet-base-v2",
    )
    chunk_size: int = int(os.getenv("CHATDOC_CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHATDOC_CHUNK_OVERLAP", "120"))
    max_search_results: int = int(os.getenv("CHATDOC_MAX_SEARCH_RESULTS", "4"))
    uploads_dir: Path = PROJECT_ROOT / "backend" / "data" / "uploads"
    parsed_dir: Path = PROJECT_ROOT / "backend" / "data" / "parsed"
    indexes_dir: Path = PROJECT_ROOT / "backend" / "data" / "indexes"
    metadata_dir: Path = PROJECT_ROOT / "backend" / "data" / "metadata"
    sessions_dir: Path = PROJECT_ROOT / "backend" / "data" / "sessions"
    files_metadata_path: Path = PROJECT_ROOT / "backend" / "data" / "metadata" / "files.json"
    sessions_path: Path = PROJECT_ROOT / "backend" / "data" / "sessions" / "sessions.json"
    allowed_origins: tuple[str, ...] = field(default_factory=_default_allowed_origins)
