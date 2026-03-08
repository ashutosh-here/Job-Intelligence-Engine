type Props = {
  totalJobs: number;
  jobsToday: number;
  avgSemantic: number;
  avgFinal: number;
};

export function OverviewCards({ totalJobs, jobsToday, avgSemantic, avgFinal }: Props) {
  const cards = [
    { label: "Total Jobs", value: totalJobs.toLocaleString() },
    { label: "Jobs Today", value: jobsToday.toLocaleString() },
    { label: "Avg Semantic", value: avgSemantic.toFixed(3) },
    { label: "Avg Final", value: avgFinal.toFixed(3) }
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl border border-white/10 bg-jie-card p-4 shadow-lg shadow-black/20"
        >
          <p className="text-xs uppercase tracking-widest text-jie-muted">{card.label}</p>
          <p className="mt-2 text-2xl font-bold text-white">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
