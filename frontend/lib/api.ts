const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Overview = {
  total_jobs: number;
  jobs_today: number;
  avg_semantic_score: number;
  avg_final_score: number;
};

export type Trends = {
  posting_trends: Array<{ date: string; discovered_jobs: number }>;
  salary_distribution: Array<{ bucket: string; count: number }>;
  semantic_distribution: Array<{ bucket: string; count: number }>;
};

export type Job = {
  id: number;
  title: string;
  location: string | null;
  final_score: number;
  semantic_score: number;
  remote_flag: boolean;
  first_seen: string;
};

async function call<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API failure on ${path}: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getOverview(): Promise<Overview> {
  return call<Overview>("/analytics/overview");
}

export async function getTrends(): Promise<Trends> {
  return call<Trends>("/analytics/trends");
}

export async function getJobs(): Promise<Job[]> {
  return call<Job[]>("/jobs?limit=20");
}
