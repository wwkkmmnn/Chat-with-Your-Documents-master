from __future__ import annotations

from fastapi import APIRouter

from backend.app.dependencies import get_app_services

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    services = get_app_services()
    return {
        "status": "ok",
        "app": services.settings.app_name,
        "version": services.settings.app_version,
        "skills": services.skill_registry.list_names(),
        "llmConfigured": services.llm_service.is_configured(),
    }
