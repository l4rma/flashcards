export default function StatsBar({ stats }) {
  if (!stats) return null;

  return (
    <div className="flex justify-center gap-6 pb-3 text-sm font-bold text-ink-soft">
      <span>🔥 {stats.current_streak}</span>
      <span>🪙 {stats.coins}</span>
    </div>
  );
}
