from pydantic import BaseModel


class OutreachRequest(BaseModel):
    job_id: int
    user_profile: str


class OutreachResponse(BaseModel):
    recruiter_message: str
    cold_email: str
