import { useEffect, useRef, useState } from "react";
import { completePractice } from "../api";
import FlipCard from "../components/FlipCard";

// A single linear pass through `queue`, once — no requeue on Wrong (unlike
// the real Train loop), no backend call *per grade*: grading here is pure
// self-assessment, tallied locally for the end-of-round summary, never
// sent anywhere. See SPEC.md's Extra Training section for why (this mode
// is entirely schedule-free and earns no coins/xp/streak credit from the
// grades themselves). Finishing a full pass *does* make one call —
// POST /practice/completed — purely to back the practice-related
// achievements (Field Trip/Full Circle/Specialist/the practice-count
// family); an achievement's own one-time reward on unlock is a separate
// thing from per-grade credit, same as every other achievement.
export default function PracticeSession({ queue, title, source, onExit, onAchievementsUnlocked, onLeveledUp }) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [wrong, setWrong] = useState(0);

  const total = queue.length;
  const done = index >= total;
  const current = queue[index];

  // App.jsx's onAchievementsUnlocked/onLeveledUp are plain functions, not
  // useCallback-memoized, so they get a new identity on every parent
  // re-render — listing them as effect deps would refire this effect (and
  // re-POST /practice/completed) on every such re-render while `done`
  // stays true, not just once per actual completion. A ref always holds
  // the latest versions without needing to be a dependency itself.
  const callbacksRef = useRef();
  callbacksRef.current = { onAchievementsUnlocked, onLeveledUp };

  useEffect(() => {
    if (!done) return;
    completePractice(source).then((result) => {
      callbacksRef.current.onAchievementsUnlocked?.(result.newly_unlocked_achievements);
      callbacksRef.current.onLeveledUp?.(result.newly_leveled_up);
    });
    // Deliberately only [done, source] — see callbacksRef comment above
    // for why the callbacks themselves aren't listed.
  }, [done, source]);

  function grade(result) {
    if (result === "correct") setCorrect((c) => c + 1);
    else setWrong((w) => w + 1);
    setFlipped(false);
    setIndex((i) => i + 1);
  }

  function restart() {
    setIndex(0);
    setFlipped(false);
    setCorrect(0);
    setWrong(0);
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 pt-8 pb-10 gap-7">
      <button
        type="button"
        onClick={onExit}
        aria-label="Exit practice"
        className="fixed top-4 right-4 rounded-full w-10 h-10 flex items-center justify-center bg-surface/95 backdrop-blur shadow-lg ring-1 ring-ink/10 text-ink-soft hover:text-ink active:scale-90 transition z-30"
      >
        ✕
      </button>

      {done ? (
        <div className="flex flex-col items-center gap-3 text-center px-4">
          <span className="text-5xl">📖</span>
          <h1 className="font-display font-semibold text-3xl text-ink mt-2">Practice complete</h1>
          <p className="text-ink-soft max-w-xs">
            {title} · {correct} correct · {wrong} wrong
          </p>
          <div className="flex gap-3 mt-2">
            <button
              type="button"
              onClick={restart}
              className="rounded-full bg-primary-light hover:bg-primary/20 text-primary-dark font-bold px-6 py-3 transition"
            >
              Practice again
            </button>
            <button
              type="button"
              onClick={onExit}
              className="rounded-full bg-primary hover:brightness-90 active:scale-95 transition text-white font-bold px-6 py-3"
            >
              Done
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="w-full max-w-sm flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft truncate pr-2">
              {title}
            </span>
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft shrink-0">
              {index + 1} of {total}
            </span>
          </div>
          <FlipCard
            key={current.id}
            front={current.english}
            back={current.french}
            flipped={flipped}
            stackDepth={Math.min(2, total - index - 1)}
            onClick={() => setFlipped((f) => !f)}
          />
          {flipped && (
            <div className="flex justify-center gap-4">
              <button
                type="button"
                onClick={() => grade("wrong")}
                className="rounded-full bg-wrong hover:brightness-90 active:scale-95 transition text-white font-bold px-8 py-3"
              >
                Wrong
              </button>
              <button
                type="button"
                onClick={() => grade("correct")}
                className="rounded-full bg-primary hover:brightness-90 active:scale-95 transition text-white font-bold px-8 py-3"
              >
                Correct
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
