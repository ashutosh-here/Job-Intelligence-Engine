from app.extraction.adapters.base import GenericCssAdapter


class NaukriAdapter(GenericCssAdapter):
    platform = "naukri"
    url_markers = ("naukri.com",)
    selectors = {
        "card": "article.jobTuple, div.srp-jobtuple-wrapper, div.jobTuple",
        "title": "a.title, h2 a, a[href*='/job-listings-']",
        "company": "a.comp-name, .comp-name",
        "location": ".locWdth, .location",
        "description": ".job-desc, .job-description, .dots-classes-2",
        "posted_date": ".job-post-day, .fleft.postedon",
        "apply": "a.title, a[href*='/job-listings-']",
    }
