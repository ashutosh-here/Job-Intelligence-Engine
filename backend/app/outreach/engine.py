from dataclasses import dataclass

from app.models.company import Company
from app.models.job import Job


@dataclass
class OutreachDraft:
    recruiter_message: str
    cold_email: str


class OutreachEngine:
    def generate(self, job: Job, company: Company | None, user_profile: str) -> OutreachDraft:
        company_name = company.name if company else "your company"
        opening = f"{job.title} ({job.location or 'location-flexible'})"

        recruiter_message = (
            f"Hi, I am interested in the {opening} role at {company_name}. "
            f"My profile aligns with the stack and scope in this posting. "
            f"Could we schedule a short conversation this week?"
        )

        cold_email = (
            f"Subject: Interest in {job.title} at {company_name}\n\n"
            f"Hello Recruiter,\n\n"
            f"I reviewed the {job.title} opening and it matches my background.\n"
            f"Why I am a fit:\n"
            f"- Relevant experience: {user_profile[:220]}\n"
            f"- Direct alignment with your requirements in the job description\n"
            f"- Ready for immediate interview process\n\n"
            f"If useful, I can share a concise portfolio and project summary.\n\n"
            f"Best,\nCandidate"
        )
        return OutreachDraft(recruiter_message=recruiter_message, cold_email=cold_email)
