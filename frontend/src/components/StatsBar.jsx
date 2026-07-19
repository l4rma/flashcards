import CoinIcon from "./CoinIcon";
import { trainedToday } from "../streak";

export default function StatsBar({ stats }) {
  if (!stats) return null;

  return (
    <header className="flex justify-center gap-8 px-4 py-4 bg-surface shadow-sm shadow-ink/5">
      <div className="flex items-center gap-2">
        <span
          className={`text-2xl leading-none ${trainedToday(stats) ? "" : "grayscale opacity-40"}`}
          title={trainedToday(stats) ? "Trained today" : "Not trained yet today"}
        >
          🔥
        </span>
        <span className="font-display font-semibold text-2xl leading-none text-ink">
          {stats.current_streak}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <CoinIcon className="w-6 h-6" />
        <span className="font-display font-semibold text-2xl leading-none text-ink">
          {stats.coins}
        </span>
      </div>
    </header>
  );
}
