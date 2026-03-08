import { OverviewCards } from "@/components/OverviewCards";
import { TrendCharts } from "@/components/TrendCharts";
import { getJobs, getOverview, getTrends } from "@/lib/api";

async function safeLoad() {
  try {
    const [overview, trends, jobs] = await Promise.all([getOverview(), getTrends(), getJobs()]);
    return { overview, trends, jobs, error: null };
  } catch (error) {
    return {
      overview: { total_jobs: 0, jobs_today: 0, avg_semantic_score: 0, avg_final_score: 0 },
      trends: { posting_trends: [], salary_distribution: [], semantic_distribution: [] },
      jobs: [],
      error: (error as Error).message
    };
  }
}

export default async function Home() {
  const { overview, trends, jobs, error } = await safeLoad();

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 md:px-8">
      <section className="mb-8">
        <h1 className="text-3xl font-bold text-white md:text-5xl">Job Intelligence Engine</h1>
        <p className="mt-2 text-sm text-jie-muted md:text-base">
          Discovery, extraction, semantic ranking, and market intelligence in one pipeline.
        </p>
        {error ? (
          <p className="mt-3 rounded-md border border-red-500/40 bg-red-900/20 p-2 text-sm text-red-300">
            Backend API unavailable: {error}
          </p>
        ) : null}
      </section>

      <section className="mb-8">
        <OverviewCards
          totalJobs={overview.total_jobs}
          jobsToday={overview.jobs_today}
          avgSemantic={overview.avg_semantic_score}
          avgFinal={overview.avg_final_score}
        />
      </section>

      <section className="mb-8">
        <TrendCharts
          postingTrends={trends.posting_trends}
          salaryDistribution={trends.salary_distribution}
        />
      </section>

      <section className="overflow-hidden rounded-xl border border-white/10 bg-jie-card">
        <div className="border-b border-white/10 px-4 py-3">
          <h2 className="text-sm uppercase tracking-widest text-jie-muted">Top Jobs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-black/20 text-jie-muted">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Final Score</th>
                <th className="px-4 py-3">Semantic</th>
                <th className="px-4 py-3">Remote</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-t border-white/10">
                  <td className="px-4 py-3">{job.title}</td>
                  <td className="px-4 py-3 text-jie-muted">{job.location ?? "Unknown"}</td>
                  <td className="px-4 py-3">{job.final_score.toFixed(3)}</td>
                  <td className="px-4 py-3">{job.semantic_score.toFixed(3)}</td>
                  <td className="px-4 py-3">{job.remote_flag ? "Yes" : "No"}</td>
                </tr>
              ))}
              {jobs.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-jie-muted" colSpan={5}>
                    No jobs available yet. Run a source pipeline to populate data.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
