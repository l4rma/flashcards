import { useEffect, useState } from "react";
import { getAchievements, getQuests, getStats, listCards } from "../api";
import ProgressBar from "../components/ProgressBar";

function formatDateTime(iso) {
  return new Date(iso).toLocaleString();
}

export default function ProgressPage() {
  const [stats, setStats] = useState(null);
  const [cards, setCards] = useState(null);
  const [achievements, setAchievements] = useState(null);
  const [quests, setQuests] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    Promise.all([getStats(), listCards(), getAchievements(), getQuests()]).then(
      ([statsRes, cardsRes, achievementsRes, questsRes]) => {
        setStats(statsRes);
        setCards(cardsRes);
        setAchievements(achievementsRes);
        setQuests(questsRes);
      }
    );
  }, []);

  if (!stats || !cards || !achievements || !quests) {
    return <p className="text-center py-10 text-ink-soft">Loading…</p>;
  }

  const totalCorrect = cards.reduce((sum, c) => sum + c.times_correct, 0);
  const totalWrong = cards.reduce((sum, c) => sum + c.times_wrong, 0);
  const totalGrades = totalCorrect + totalWrong;
  const accuracy = totalGrades > 0 ? Math.round((totalCorrect / totalGrades) * 100) : null;
  const unlockedCount = achievements.filter((a) => a.unlocked).length;

  return (
    <div className="flex flex-col items-center px-4 py-10 gap-6">
      <h1 className="text-2xl font-extrabold text-ink">Progress</h1>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-2">
        <p className="text-sm text-ink-soft leading-relaxed">
          🔥 Streak: {stats.current_streak} (best {stats.longest_streak})
          <br />
          🪙 Coins: {stats.coins}
          <br />
          📚 Cards: {cards.length}
        </p>
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-4">
        <h2 className="text-lg font-bold text-ink">Daily Quests</h2>
        {quests.map((q) => (
          <div key={q.key} className="flex flex-col gap-1">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-ink flex items-center gap-2">
                <span className="text-xl">{q.badge}</span>
                {q.title}
              </span>
              <span className="text-xs font-semibold text-ink-soft">
                {q.completed ? "✅" : `🪙 ${q.coin_reward}`}
              </span>
            </div>
            <p className="text-xs text-ink-soft">{q.description}</p>
            <ProgressBar percent={Math.round((q.progress_current / q.progress_target) * 100)} />
            <span className="text-xs font-semibold text-ink-soft self-end">
              {q.progress_current}/{q.progress_target}
            </span>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-2">
        <p className="text-sm text-ink-soft leading-relaxed">
          Cards in deck: {cards.length}
          <br />
          Lifetime correct: {totalCorrect} · wrong: {totalWrong}
          <br />
          Accuracy: {accuracy === null ? "—" : `${accuracy}%`}
          <br />
          Achievements: {unlockedCount}/{achievements.length}
        </p>
      </div>

      <div className="w-full max-w-sm">
        <h2 className="text-lg font-bold text-ink mb-3">Achievements</h2>
        <div className="grid grid-cols-3 gap-3">
          {achievements.map((a) => (
            <button
              key={a.key}
              type="button"
              onClick={() => setSelected(a)}
              className={`flex flex-col items-center justify-center gap-1 rounded-2xl shadow-md p-4 aspect-square transition active:scale-95 ${
                a.unlocked ? "bg-surface" : "bg-surface/60 grayscale opacity-50"
              }`}
            >
              <span className="text-3xl">{a.badge}</span>
              <span className="text-xs font-semibold text-ink text-center leading-tight">
                {a.title}
              </span>
            </button>
          ))}
        </div>
      </div>

      {selected && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center px-4 z-10"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-surface rounded-3xl shadow-lg p-6 max-w-xs w-full flex flex-col items-center gap-3 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="text-5xl">{selected.badge}</span>
            <h3 className="text-lg font-extrabold text-ink">{selected.title}</h3>
            <p className="text-sm text-ink-soft">{selected.description}</p>
            <div className="w-full flex flex-col items-center gap-1">
              <ProgressBar
                percent={Math.round((selected.progress_current / selected.progress_target) * 100)}
              />
              <span className="text-xs font-semibold text-ink-soft">
                {selected.progress_current}/{selected.progress_target}
              </span>
            </div>
            <p className="text-xs font-semibold text-primary-dark">
              🪙 {selected.coin_reward} coins
              {selected.unlocked
                ? ` · Unlocked ${formatDateTime(selected.unlocked_at)}`
                : " on unlock"}
            </p>
            {selected.history.length > 0 && (
              <div className="w-full flex flex-col gap-1 border-t border-primary-light pt-3">
                <p className="text-xs font-bold text-ink-soft">Previously completed</p>
                {selected.history.map((h) => (
                  <p key={h.key} className="text-xs text-ink-soft">
                    {h.badge} {h.title} — {formatDateTime(h.unlocked_at)}
                  </p>
                ))}
              </div>
            )}
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="mt-2 rounded-full bg-primary-light text-primary-dark font-bold px-6 py-2 text-sm"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
