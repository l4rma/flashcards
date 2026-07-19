import { useState } from "react";
import FlipCard from "../components/FlipCard";

// A single linear pass through `queue`, once — no requeue on Wrong (unlike
// the real Train loop), no backend calls at all: grading here is pure
// self-assessment, tallied locally for the end-of-round summary, never
// sent anywhere. See SPEC.md's Extra Training section for why (this mode
// is entirely schedule-free and earns no coins/xp/streak credit).
export default function PracticeSession({ queue, title, onExit }) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [wrong, setWrong] = useState(0);

  const total = queue.length;
  const done = index >= total;
  const current = queue[index];

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
              className="rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-6 py-3"
            >
              Done
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="w-full max-w-sm flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70 truncate pr-2">
              {title}
            </span>
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70 shrink-0">
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
                className="rounded-full bg-wrong hover:bg-wrong-dark active:scale-95 transition text-white font-bold px-8 py-3"
              >
                Wrong
              </button>
              <button
                type="button"
                onClick={() => grade("correct")}
                className="rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-8 py-3"
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
