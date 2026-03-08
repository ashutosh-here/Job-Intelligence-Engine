from app.extraction.adapters.base import GenericCssAdapter


class GreenhouseAdapter(GenericCssAdapter):
    platform = "greenhouse"
    url_markers = ("greenhouse.io",)
    selectors = {
        "card": ".opening, .job-post, .job",
        "title": ".opening-title, h2, h3",
        "company": ".company-name",
        "location": ".location, .opening-location",
        "description": ".opening-description, .description",
        "posted_date": ".posted-date",
        "apply": "a[href*='jobs'], a[href*='greenhouse']",
    }
