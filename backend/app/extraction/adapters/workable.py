from app.extraction.adapters.base import GenericCssAdapter


class WorkableAdapter(GenericCssAdapter):
    platform = "workable"
    url_markers = ("workable.com",)
    selectors = {
        "card": ".job, .jobs li, .js-job",
        "title": ".job-title, h2, h3",
        "company": ".company",
        "location": ".location",
        "description": ".job-description, .description",
        "posted_date": ".date, .posted-date",
        "apply": "a[href*='workable.com'], a[href*='/jobs/']",
    }
