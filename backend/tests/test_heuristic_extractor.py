from app.extraction.heuristic import HeuristicExtractor


def test_heuristic_extractor_finds_repeated_job_cards() -> None:
    html = """
    <html><body>
      <div class="jobs">
        <article class="job-card">
          <h3>Senior Python Engineer</h3>
          <p>Remote - Posted 2026-03-01</p>
          <p>Salary $120,000 - $150,000. Python, AWS, Docker.</p>
          <a href="/apply/1">Apply</a>
        </article>
        <article class="job-card">
          <h3>Backend Engineer</h3>
          <p>Hybrid - Posted 2026-03-02</p>
          <p>Salary $100,000 - $130,000. FastAPI, SQL, Kubernetes.</p>
          <a href="/apply/2">Apply</a>
        </article>
      </div>
    </body></html>
    """

    extractor = HeuristicExtractor()
    jobs = extractor.extract_jobs(html, "https://example.com/careers")

    assert len(jobs) >= 2
    assert any(job.remote_flag for job in jobs)
    assert any(job.salary_min is not None for job in jobs)
