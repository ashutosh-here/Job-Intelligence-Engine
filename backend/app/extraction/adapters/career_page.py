from app.extraction.adapters.base import GenericCssAdapter


class CareerPageAdapter(GenericCssAdapter):
    platform = "career_page"
    url_markers = ("careers", "jobs", "join-us", "work-with-us")
    selectors = {
        "card": "article, li, div[class*='job'], div[class*='career']",
        "title": "h2, h3, a",
        "company": "meta[property='og:site_name'], .company-name",
        "location": "span[class*='location'], div[class*='location']",
        "description": "p, div[class*='description']",
        "posted_date": "time, span[class*='date']",
        "apply": "a[href*='apply'], a[href*='job']",
    }
