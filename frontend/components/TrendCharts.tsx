"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

type Trend = { date: string; discovered_jobs: number };
type Bucket = { bucket: string; count: number };

type Props = {
  postingTrends: Trend[];
  salaryDistribution: Bucket[];
};

export function TrendCharts({ postingTrends, salaryDistribution }: Props) {
  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div className="h-80 rounded-xl border border-white/10 bg-jie-card p-4">
        <h3 className="mb-3 text-sm uppercase tracking-widest text-jie-muted">Posting Trends</h3>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={postingTrends}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30486e" />
            <XAxis dataKey="date" stroke="#8da1c7" />
            <YAxis stroke="#8da1c7" />
            <Tooltip />
            <Legend />
            <Bar dataKey="discovered_jobs" fill="#ff7b39" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="h-80 rounded-xl border border-white/10 bg-jie-card p-4">
        <h3 className="mb-3 text-sm uppercase tracking-widest text-jie-muted">
          Salary Distribution
        </h3>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={salaryDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30486e" />
            <XAxis dataKey="bucket" stroke="#8da1c7" />
            <YAxis stroke="#8da1c7" />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#33d17a" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
