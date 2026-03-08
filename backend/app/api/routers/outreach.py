from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, is_admin
from app.db import get_db
from app.models.company import Company
from app.models.job import Job
from app.models.outreach_log import OutreachLog
from app.models.source import Source
from app.models.user import User
from app.outreach.engine import OutreachEngine
from app.schemas.outreach import OutreachRequest, OutreachResponse

router = APIRouter(prefix="/outreach", tags=["outreach"])
outreach_engine = OutreachEngine()


@router.post("/draft", response_model=OutreachResponse)
def generate_outreach(
    payload: OutreachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutreachResponse:
    job = db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not is_admin(current_user):
        source = db.get(Source, job.source_id)
        if not source or source.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed for this job")
    company = db.get(Company, job.company_id) if job.company_id else None

    draft = outreach_engine.generate(job, company, payload.user_profile)
    db.add(
        OutreachLog(
            job_id=job.id,
            message=draft.recruiter_message + "\n\n" + draft.cold_email,
            status="draft",
        )
    )
    db.commit()
    return OutreachResponse(
        recruiter_message=draft.recruiter_message,
        cold_email=draft.cold_email,
    )
