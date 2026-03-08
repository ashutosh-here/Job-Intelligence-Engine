from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_admin
from app.db import get_db
from app.models.source import Source
from app.models.user import User
from app.queue.tasks import process_source
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Source:
    source = Source(
        user_id=current_user.id,
        url=str(payload.url),
        type=payload.type,
        refresh_interval=payload.refresh_interval,
        status="active",
        keywords=payload.keywords,
        custom_selectors=payload.custom_selectors,
    )
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Source already exists for this user") from exc
    db.refresh(source)
    return source


@router.get("", response_model=list[SourceRead])
def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Source]:
    stmt = select(Source)
    if not is_admin(current_user):
        stmt = stmt.where(Source.user_id == current_user.id)
    stmt = stmt.order_by(Source.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.post("/{source_id}/run")
def enqueue_source_run(
    source_id: int,
    user_profile: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.user_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not allowed for this source")
    task = process_source.delay(source_id=source_id, user_profile=user_profile)
    return {"task_id": task.id, "source_id": source_id, "queued": True}
