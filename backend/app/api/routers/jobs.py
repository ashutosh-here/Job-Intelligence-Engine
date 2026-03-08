from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_admin
from app.db import get_db
from app.models.job import Job
from app.models.source import Source
from app.models.user import User
from app.schemas.job import JobRead
from app.vector.engine import VectorEngine

router = APIRouter(prefix="/jobs", tags=["jobs"])
vector_engine = VectorEngine()


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=500),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
) -> list[Job]:
    stmt = select(Job)
    if not is_admin(current_user):
        stmt = stmt.join(Source, Source.id == Job.source_id).where(Source.user_id == current_user.id)
    stmt = stmt.order_by(Job.first_seen.desc()).limit(limit)
    if min_score is not None:
        scoped = select(Job).where(Job.final_score >= min_score)
        if not is_admin(current_user):
            scoped = scoped.join(Source, Source.id == Job.source_id).where(Source.user_id == current_user.id)
        stmt = scoped.order_by(Job.final_score.desc(), Job.first_seen.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not is_admin(current_user):
        source = db.get(Source, job.source_id)
        if not source or source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed for this job")
    return job


@router.get("/similar/{job_id}")
def get_similar_jobs(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    root_job = db.get(Job, job_id)
    if not root_job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not is_admin(current_user):
        root_source = db.get(Source, root_job.source_id)
        if not root_source or root_source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed for this job")

    matches = vector_engine.find_similar_job_ids(db, job_id=job_id, limit=limit)
    if not matches:
        return {"job_id": job_id, "matches": []}

    ids = [row[0] for row in matches]
    stmt = select(Job).where(Job.id.in_(ids))
    jobs = {job.id: job for job in db.execute(stmt).scalars().all()}

    payload = []
    for similar_id, similarity in matches:
        job = jobs.get(similar_id)
        if job:
            if not is_admin(current_user):
                source = db.get(Source, job.source_id)
                if not source or source.user_id != current_user.id:
                    continue
            payload.append({"job": JobRead.model_validate(job), "similarity": similarity})
    return {"job_id": job_id, "matches": payload}
