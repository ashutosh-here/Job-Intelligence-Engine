from app.extraction.adapters.base import GenericCssAdapter


class AshbyAdapter(GenericCssAdapter):
    platform = "ashby"
    url_markers = ("ashbyhq.com",)
    selectors = {
        "card": "[data-testid='job-card'], .job-post, .job",
        "title": "h2, h3, .job-title",
        "company": ".company-name",
        "location": ".location",
        "description": ".job-description, .description",
        "posted_date": ".posted-date",
        "apply": "a[href*='ashbyhq.com'], a[href*='/jobs/']",
    }
