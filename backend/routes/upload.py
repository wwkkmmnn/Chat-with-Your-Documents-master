from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.dependencies import get_app_services

router = APIRouter()


@router.get("/files")
def list_files() -> dict:
    services = get_app_services()
    return {"files": services.rag_service.list_files()}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    services = get_app_services()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        file_record = services.rag_service.ingest_file(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {exc}") from exc

    return {
        "message": "Document uploaded and indexed successfully.",
        "file": file_record,
    }
