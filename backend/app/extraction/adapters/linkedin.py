from app.extraction.adapters.base import GenericCssAdapter


class LinkedInAdapter(GenericCssAdapter):
    platform = "linkedin"
    url_markers = ("linkedin.com/jobs",)
    selectors = {
        "card": "li.jobs-search-results__list-item, div.base-search-card, li.occludable-update",
        "title": "h3.base-search-card__title, a.job-card-list__title, h3",
        "company": "h4.base-search-card__subtitle, a.hidden-nested-link, .job-card-container__company-name",
        "location": "span.job-search-card__location, .job-card-container__metadata-item",
        "description": "div.show-more-less-html__markup, div.description__text",
        "posted_date": "time, span.posted-time-ago__text",
        "apply": "a.base-card__full-link, a[href*='/jobs/view/']",
    }
