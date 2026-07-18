import { useEffect, useState } from "react";
import { completeSession, gradeCard, getQuests, listDueCards } from "../api";
import FlipCard from "../components/FlipCard";
import ProgressBar from "../components/ProgressBar";

export default function TrainPage({ onGraded, onAchievementsUnlocked, onQuestsCompleted }) {
  const [queue, setQueue] = useState(null); // null while loading
  const [trainQuest, setTrainQuest] = useState(null);
  const [flipped, setFlipped] = useState(false);
  const [busy, setBusy] = useState(false);

  async function refreshTrainQuest() {
    const quests = await getQuests();
    setTrainQuest(quests.find((q) => q.key === "daily_train") ?? null);
  }

  useEffect(() => {
    Promise.all([listDueCards(), getQuests()]).then(([cards, quests]) => {
      setQueue(cards);
      setTrainQuest(quests.find((q) => q.key === "daily_train") ?? null);
    });
  }, []);

  if (queue === null) {
    return <p className="text-center py-10 text-ink-soft">Loading…</p>;
  }

  if (queue.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 px-4 py-16 text-center">
        <h1 className="text-2xl font-extrabold text-ink">Session complete!</h1>
        <p className="text-ink-soft">No cards due right now. Nice work.</p>
        <p className="text-ink-soft">You should add more cards to learn more.</p>
      </div>
    );
  }

  const current = queue[0];
  // Same source (GET /quests' daily_train entry) as the Progress page's
  // Daily Quests bar, so the two are always identical — previously this
  // bar divided by the full due count instead of the quest's min(10, due)
  // target, so they diverged whenever more than 10 cards were due.
  const percent =
    trainQuest && trainQuest.progress_target > 0
      ? Math.min(100, Math.round((trainQuest.progress_current / trainQuest.progress_target) * 100))
      : 0;

  async function grade(result) {
    if (busy) return;
    setBusy(true);
    try {
      const updated = await gradeCard(current.id, result);
      onAchievementsUnlocked?.(updated.newly_unlocked_achievements);
      onQuestsCompleted?.(updated.newly_completed_quests);
      const rest = queue.slice(1);
      const newQueue = result === "wrong" ? [...rest, updated] : rest;
      setQueue(newQueue);
      setFlipped(false);
      onGraded?.();
      await refreshTrainQuest();
      if (newQueue.length === 0) {
        const sessionStats = await completeSession();
        onAchievementsUnlocked?.(sessionStats.newly_unlocked_achievements);
        onGraded?.();
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-center px-4 py-10 gap-6">
      <p className="text-sm font-semibold text-ink-soft">{queue.length} card(s) left to review</p>
      <div className="w-full max-w-sm flex flex-col items-center gap-1">
        <ProgressBar percent={percent} />
        {trainQuest && (
          <span className="text-xs font-semibold text-ink-soft">
            🎯 Daily goal: {trainQuest.progress_current}/{trainQuest.progress_target}
          </span>
        )}
      </div>
      <FlipCard
        key={current.id}
        front={current.english}
        back={current.french}
        flipped={flipped}
        onClick={() => setFlipped((f) => !f)}
      />
      {flipped && (
        <div className="flex justify-center gap-4">
          <button
            type="button"
            disabled={busy}
            onClick={() => grade("wrong")}
            className="rounded-full bg-wrong hover:bg-wrong-dark active:scale-95 transition text-white font-bold px-8 py-3 disabled:opacity-50"
          >
            Wrong
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => grade("correct")}
            className="rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-8 py-3 disabled:opacity-50"
          >
            Correct
          </button>
        </div>
      )}
    </div>
  );
}
