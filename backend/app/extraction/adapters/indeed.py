from app.extraction.adapters.base import GenericCssAdapter


class IndeedAdapter(GenericCssAdapter):
    platform = "indeed"
    url_markers = ("indeed.",)
    selectors = {
        "card": "div.job_seen_beacon, div.cardOutline, li.css-5lfssm",
        "title": "h2.jobTitle, a.jcs-JobTitle, h2",
        "company": "span.companyName, [data-testid='company-name']",
        "location": "div.companyLocation, [data-testid='text-location']",
        "description": "div.job-snippet, #jobDescriptionText",
        "posted_date": "span.date, [data-testid='myJobsStateDate']",
        "apply": "a.jcs-JobTitle, a[href*='/viewjob']",
    }
