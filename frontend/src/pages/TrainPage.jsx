import { useEffect, useState } from "react";
import { completeSession, gradeCard, getQuests, listDueCards } from "../api";
import FlipCard from "../components/FlipCard";
import ProgressBar from "../components/ProgressBar";
import ExtraTrainingPicker from "./ExtraTrainingPicker";
import PracticeSession from "./PracticeSession";

function ExtraTrainingLink({ onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-sm font-bold text-primary-dark hover:text-primary-dark/90 transition underline-offset-4 hover:underline"
    >
      🎲 Extra Training
    </button>
  );
}

export default function TrainPage({
  onGraded,
  onAchievementsUnlocked,
  onQuestsCompleted,
  onLeveledUp,
  onDailyBonusAwarded,
}) {
  const [queue, setQueue] = useState(null); // null while loading
  const [trainQuest, setTrainQuest] = useState(null);
  const [flipped, setFlipped] = useState(false);
  const [busy, setBusy] = useState(false);
  // "train" (the real due-card loop) | "picker" (choosing an Extra
  // Training source) | "practice" (running one). Extra Training is
  // deliberately a separate mode, not folded into the queue above — it
  // never touches Card scheduling or gamification state (see SPEC.md's
  // Extra Training section), so it needs its own non-persisted queue and
  // grading path entirely.
  const [mode, setMode] = useState("train");
  const [practice, setPractice] = useState(null); // { queue, title } | null

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

  function startPractice(practiceQueue, title, source) {
    setPractice({ queue: practiceQueue, title, source });
    setMode("practice");
  }

  function exitPractice() {
    setPractice(null);
    setMode("train");
  }

  if (mode === "picker") {
    return <ExtraTrainingPicker onStart={startPractice} onClose={() => setMode("train")} />;
  }

  if (mode === "practice" && practice) {
    return (
      <PracticeSession
        queue={practice.queue}
        title={practice.title}
        source={practice.source}
        onExit={exitPractice}
        onAchievementsUnlocked={onAchievementsUnlocked}
        onLeveledUp={onLeveledUp}
      />
    );
  }

  if (queue === null) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-ink-soft">Loading…</p>
      </div>
    );
  }

  if (queue.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 px-4 text-center">
        <span className="text-5xl">🌿</span>
        <h1 className="font-display font-semibold text-3xl text-ink mt-2">Session complete</h1>
        <p className="text-ink-soft max-w-xs">
          No cards due right now — nice work. Add more in Deck to keep growing today's stack.
        </p>
        <div className="mt-2">
          <ExtraTrainingLink onClick={() => setMode("picker")} />
        </div>
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
      onLeveledUp?.(updated.newly_leveled_up);
      onDailyBonusAwarded?.(updated.newly_awarded_daily_bonus);
      const rest = queue.slice(1);
      const newQueue = result === "wrong" ? [...rest, updated] : rest;
      setQueue(newQueue);
      setFlipped(false);
      onGraded?.();
      await refreshTrainQuest();
      if (newQueue.length === 0) {
        const sessionStats = await completeSession();
        onAchievementsUnlocked?.(sessionStats.newly_unlocked_achievements);
        onLeveledUp?.(sessionStats.newly_leveled_up);
        onGraded?.();
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 pt-8 pb-10 gap-7">
      <div className="w-full max-w-sm flex flex-col items-center gap-2">
        <div className="w-full flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wide text-ink-soft">
            {queue.length} left today
          </span>
          {trainQuest && (
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft">
              🎯 {trainQuest.progress_current}/{trainQuest.progress_target}
            </span>
          )}
        </div>
        <ProgressBar percent={percent} />
      </div>
      <FlipCard
        key={current.id}
        front={current.english}
        back={current.french}
        flipped={flipped}
        stackDepth={Math.min(2, queue.length - 1)}
        onClick={() => setFlipped((f) => !f)}
      />
      {flipped && (
        <div className="flex justify-center gap-4">
          <button
            type="button"
            disabled={busy}
            onClick={() => grade("wrong")}
            className="rounded-full bg-wrong hover:brightness-90 active:scale-95 transition text-white font-bold px-8 py-3 disabled:opacity-50"
          >
            Wrong
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => grade("correct")}
            className="rounded-full bg-primary hover:brightness-90 active:scale-95 transition text-white font-bold px-8 py-3 disabled:opacity-50"
          >
            Correct
          </button>
        </div>
      )}
      <ExtraTrainingLink onClick={() => setMode("picker")} />
    </div>
  );
}
