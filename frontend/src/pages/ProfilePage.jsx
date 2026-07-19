import { useEffect, useState } from "react";
import { getAchievements, getCollection, getQuests, getStats, listCards } from "../api";
import { avatarEmoji } from "../avatars";
import CoinIcon from "../components/CoinIcon";
import ProgressBar from "../components/ProgressBar";
import { trainedToday } from "../streak";

function formatDateTime(iso) {
  return new Date(iso).toLocaleString();
}

function Stat({ icon, value, label }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-xl leading-none">{icon}</span>
      <span className="font-display font-semibold text-3xl leading-tight text-ink">{value}</span>
      <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">{label}</span>
    </div>
  );
}

export default function ProfilePage() {
  const [stats, setStats] = useState(null);
  const [cards, setCards] = useState(null);
  const [achievements, setAchievements] = useState(null);
  const [quests, setQuests] = useState(null);
  const [collection, setCollection] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    Promise.all([getStats(), listCards(), getAchievements(), getQuests(), getCollection()]).then(
      ([statsRes, cardsRes, achievementsRes, questsRes, collectionRes]) => {
        setStats(statsRes);
        setCards(cardsRes);
        setAchievements(achievementsRes);
        setQuests(questsRes);
        setCollection(collectionRes);
      }
    );
  }, []);

  if (!stats || !cards || !achievements || !quests || !collection) {
    return <p className="text-center py-10 text-ink-soft">Loading…</p>;
  }

  const totalCorrect = cards.reduce((sum, c) => sum + c.times_correct, 0);
  const totalWrong = cards.reduce((sum, c) => sum + c.times_wrong, 0);
  const totalGrades = totalCorrect + totalWrong;
  const accuracy = totalGrades > 0 ? Math.round((totalCorrect / totalGrades) * 100) : null;
  const unlockedCount = achievements.filter((a) => a.unlocked).length;
  const equippedTitle = collection.titles.find((t) => t.equipped);
  const totalLootboxes = collection.lootboxes.reduce((sum, b) => sum + b.count, 0);
  const xpPercent =
    stats.xp_for_next_level > 0
      ? Math.round((stats.xp_into_level / stats.xp_for_next_level) * 100)
      : 0;

  return (
    <div className="flex flex-col items-center px-4 pt-8 pb-10 gap-8">
      <div className="w-full max-w-sm flex items-center gap-3 self-start">
        <span className="text-4xl leading-none">{avatarEmoji(stats.avatar_key)}</span>
        <div>
          <h1 className="font-display font-semibold text-2xl text-ink leading-tight">
            {stats.username || "Your Profile"}
          </h1>
          {equippedTitle && (
            <p className="text-xs font-bold uppercase tracking-wide text-primary-dark">
              {equippedTitle.name}
            </p>
          )}
        </div>
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="font-display font-semibold text-lg text-ink">Level {stats.level}</span>
          <span className="text-xs font-bold text-ink-soft/70">
            {stats.xp_into_level}/{stats.xp_for_next_level} XP
          </span>
        </div>
        <ProgressBar percent={xpPercent} />
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 grid grid-cols-3 gap-y-5 justify-items-center">
        <Stat
          icon={
            <span
              className={trainedToday(stats) ? "" : "grayscale opacity-40"}
              title={trainedToday(stats) ? "Trained today" : "Not trained yet today"}
            >
              🔥
            </span>
          }
          value={stats.current_streak}
          label={`best ${stats.longest_streak}`}
        />
        <Stat icon={<CoinIcon className="w-5 h-5" />} value={stats.coins} label="coins" />
        <Stat icon="📚" value={cards.length} label="cards" />
        <Stat icon="🎯" value={accuracy === null ? "—" : `${accuracy}%`} label="accuracy" />
        <Stat icon="🎁" value={totalLootboxes} label="lootboxes" />
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-5">
        <h2 className="font-display font-semibold text-lg text-ink">Daily quests</h2>
        {quests.map((q) => (
          <div key={q.key} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-bold text-ink flex items-center gap-2">
                <span className="text-xl">{q.badge}</span>
                {q.title}
              </span>
              <span className="text-xs font-bold text-ink-soft flex items-center gap-1">
                {q.completed ? (
                  "✅ done"
                ) : (
                  <>
                    <CoinIcon className="w-3.5 h-3.5" /> {q.coin_reward}
                  </>
                )}
              </span>
            </div>
            <p className="text-xs text-ink-soft">{q.description}</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 min-w-0">
                <ProgressBar percent={Math.round((q.progress_current / q.progress_target) * 100)} />
              </div>
              <span className="text-xs font-bold text-ink-soft/70 shrink-0">
                {q.progress_current}/{q.progress_target}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm">
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="font-display font-semibold text-lg text-ink">Achievements</h2>
          <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">
            {unlockedCount}/{achievements.length}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {achievements.map((a) => (
            <button
              key={a.key}
              type="button"
              onClick={() => setSelected(a)}
              className={`flex flex-col items-center justify-center gap-1 rounded-2xl shadow-md ring-1 ring-ink/10 p-4 aspect-square transition active:scale-95 ${
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
          className="fixed inset-0 bg-ink/40 flex items-center justify-center px-4 z-10"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 max-w-xs w-full flex flex-col items-center gap-3 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="text-5xl">{selected.badge}</span>
            <h3 className="font-display font-semibold text-xl text-ink">{selected.title}</h3>
            <p className="text-sm text-ink-soft">{selected.description}</p>
            <div className="w-full flex items-center gap-2">
              <div className="flex-1 min-w-0">
                <ProgressBar
                  percent={Math.round((selected.progress_current / selected.progress_target) * 100)}
                />
              </div>
              <span className="text-xs font-bold text-ink-soft/70 shrink-0">
                {selected.progress_current}/{selected.progress_target}
              </span>
            </div>
            <p className="text-xs font-semibold text-primary-dark flex items-center justify-center gap-1">
              <CoinIcon className="w-3.5 h-3.5" />
              {selected.coin_reward} coins
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
