from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_orchestrator
from app.auth.deps import get_current_user, is_admin
from app.db import get_db
from app.models.source import Source
from app.models.user import User
from app.orchestrator.service import PipelineOrchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/run/{source_id}")
def run_pipeline_now(
    source_id: int,
    user_profile: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> dict:
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    result = orchestrator.run_source(db, source_id=source_id, user_profile=user_profile)
    return {
        "source_id": result.source_id,
        "discovered_links": result.discovered_links,
        "extracted_jobs": result.extracted_jobs,
        "failed_links": result.failed_links,
        "errors": result.errors,
    }
