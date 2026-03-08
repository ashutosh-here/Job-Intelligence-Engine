from app.extraction.adapters.base import GenericCssAdapter


class LeverAdapter(GenericCssAdapter):
    platform = "lever"
    url_markers = ("lever.co",)
    selectors = {
        "card": ".posting, .posting-item, .job",
        "title": ".posting-title h5, h2, h3",
        "company": ".company",
        "location": ".posting-categories .location, .location",
        "description": ".posting-description, .description",
        "posted_date": ".posting-date",
        "apply": "a[href*='lever.co']",
    }
