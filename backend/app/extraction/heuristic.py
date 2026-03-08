import re
from collections import defaultdict

from bs4 import BeautifulSoup, Tag

from app.extraction.common import infer_remote_flag, infer_required_skills, parse_posted_date, parse_salary
from app.schemas.extraction import ExtractedJob


class HeuristicExtractor:
    def __init__(self) -> None:
        self.salary_pattern = re.compile(r"(\$|usd|inr|eur|gbp)\s*\d", re.IGNORECASE)
        self.location_pattern = re.compile(
            r"(remote|hybrid|onsite|on-site|new york|london|bangalore|san francisco)",
            re.IGNORECASE,
        )
        self.date_pattern = re.compile(r"(posted|ago|\d{4}-\d{2}-\d{2})", re.IGNORECASE)
        self.tech_pattern = re.compile(
            r"(python|java|react|node|kubernetes|docker|sql|aws|ml|ai)", re.IGNORECASE
        )
        self.apply_pattern = re.compile(r"(apply|view job|details)", re.IGNORECASE)

    def _signature(self, node: Tag) -> str:
        children = [child.name for child in node.find_all(recursive=False) if child.name]
        class_names = node.get("class", [])[:3]
        return f"{node.name}|{'/'.join(children[:6])}|{'/'.join(class_names)}"

    def _candidate_nodes(self, soup: BeautifulSoup) -> list[Tag]:
        nodes: list[Tag] = []
        for tag in soup.find_all(["article", "li", "div", "section"]):
            text = tag.get_text(" ", strip=True)
            if len(text) < 60:
                continue
            if len(text) > 5000:
                continue
            nodes.append(tag)
        return nodes

    def _score_node(self, node: Tag) -> float:
        text = node.get_text(" ", strip=True)
        score = 0.0
        if self.salary_pattern.search(text):
            score += 1.0
        if self.location_pattern.search(text):
            score += 1.0
        if self.date_pattern.search(text):
            score += 0.7
        if self.tech_pattern.search(text):
            score += 1.2
        if self.apply_pattern.search(text):
            score += 1.1
        if node.find("a", href=True):
            score += 0.8
        return score

    def extract_jobs(self, html: str, source_url: str) -> list[ExtractedJob]:
        soup = BeautifulSoup(html, "html.parser")
        nodes = self._candidate_nodes(soup)
        if not nodes:
            return []

        clusters: dict[str, list[Tag]] = defaultdict(list)
        for node in nodes:
            clusters[self._signature(node)].append(node)

        ranked = sorted(
            clusters.values(),
            key=lambda cluster: len(cluster) * sum(self._score_node(n) for n in cluster) / len(cluster),
            reverse=True,
        )
        if not ranked:
            return []

        best_cluster = ranked[0]
        extracted: list[ExtractedJob] = []
        for node in best_cluster:
            text = node.get_text(" ", strip=True)
            title_el = node.find(["h1", "h2", "h3", "a"])
            link_el = node.find("a", href=True)
            salary_min, salary_max = parse_salary(text)
            location = None
            if self.location_pattern.search(text):
                location = self.location_pattern.search(text).group(1)
            title = title_el.get_text(" ", strip=True) if title_el else "Unknown Role"
            if len(title) < 3:
                continue

            extracted.append(
                ExtractedJob(
                    job_title=title[:300],
                    company_name="Unknown Company",
                    location=location,
                    remote_flag=infer_remote_flag(text),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    job_description=text[:12000],
                    required_skills=infer_required_skills(text),
                    seniority_level=None,
                    employment_type=None,
                    posted_date=parse_posted_date(text),
                    apply_link=link_el["href"] if link_el else source_url,
                    source_url=source_url,
                    extraction_confidence=min(0.72, self._score_node(node) / 5.0),
                )
            )

        return extracted[:100]
