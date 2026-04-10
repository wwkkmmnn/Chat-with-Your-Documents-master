from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from backend.app.config import AppSettings
from backend.services.chat_service import ChatService
from backend.services.llm_service import LLMService
from backend.services.rag_service import RagService
from backend.services.router_service import RouterService
from backend.services.session_service import SessionService
from backend.skills.doc_search_skill import DocSearchSkill
from backend.skills.registry import SkillRegistry
from backend.skills.summarize_skill import SummarizeSkill
from backend.skills.web_search_skill import WebSearchSkill


@dataclass(frozen=True)
class AppServices:
    settings: AppSettings
    rag_service: RagService
    llm_service: LLMService
    router_service: RouterService
    session_service: SessionService
    skill_registry: SkillRegistry
    chat_service: ChatService


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_app_services() -> AppServices:
    settings = get_settings()

    rag_service = RagService(
        uploads_dir=settings.uploads_dir,
        parsed_dir=settings.parsed_dir,
        indexes_dir=settings.indexes_dir,
        files_metadata_path=settings.files_metadata_path,
        embeddings_model_name=settings.embeddings_model_name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        max_search_results=settings.max_search_results,
    )
    llm_service = LLMService(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
    )
    router_service = RouterService()
    session_service = SessionService(settings.sessions_path)

    skill_registry = SkillRegistry()
    skill_registry.register(DocSearchSkill(rag_service))
    skill_registry.register(WebSearchSkill())
    skill_registry.register(SummarizeSkill(llm_service))

    chat_service = ChatService(
        router_service=router_service,
        skill_registry=skill_registry,
        llm_service=llm_service,
        session_service=session_service,
        rag_service=rag_service,
    )

    return AppServices(
        settings=settings,
        rag_service=rag_service,
        llm_service=llm_service,
        router_service=router_service,
        session_service=session_service,
        skill_registry=skill_registry,
        chat_service=chat_service,
    )
