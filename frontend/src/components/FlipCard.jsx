// The stack behind the active card is more than decoration — its depth
// (0, 1, or 2 receding edges) is a second, glanceable read of how many
// cards are still queued today, echoing the "N card(s) left" text above it.
function StackEdges({ depth }) {
  if (depth <= 0) return null;
  return (
    <>
      {depth >= 2 && (
        <div className="absolute inset-0 translate-y-5 translate-x-4 rotate-6 rounded-3xl bg-primary-light shadow-md ring-1 ring-ink/5" />
      )}
      <div className="absolute inset-0 translate-y-2.5 translate-x-2 rotate-3 rounded-3xl bg-surface shadow-md ring-1 ring-ink/5" />
    </>
  );
}

function CardFace({ word, hint, variant }) {
  return (
    <div
      className={`absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-3xl shadow-lg ring-1 ring-ink/10 px-6 [backface-visibility:hidden] ${
        variant === "front" ? "bg-surface" : "bg-primary-light [transform:rotateY(180deg)]"
      }`}
    >
      {/* Punch hole — the one recurring "this is an index card" detail. */}
      <span className="absolute top-4 left-4 w-3 h-3 rounded-full bg-background ring-1 ring-ink/10" />
      <span
        className={`font-display font-semibold text-3xl text-center leading-tight ${
          variant === "front" ? "text-ink" : "text-primary-dark"
        }`}
      >
        {word}
      </span>
      <span className="w-10 h-px bg-ink/15" />
      <span className="text-xs font-bold tracking-wide uppercase text-ink-soft">{hint}</span>
    </div>
  );
}

export default function FlipCard({ front, back, flipped, stackDepth = 0, onClick }) {
  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  }

  return (
    <div className="relative w-full max-w-sm h-56">
      <StackEdges depth={stackDepth} />
      <div className="absolute inset-0 [perspective:1200px]">
        <div
          role="button"
          tabIndex={0}
          onClick={onClick}
          onKeyDown={handleKeyDown}
          className={`relative w-full h-full text-left cursor-pointer [transform-style:preserve-3d] transition-transform duration-500 ${
            flipped ? "[transform:rotateY(180deg)]" : ""
          }`}
        >
          <CardFace word={front} hint="tap to flip" variant="front" />
          <CardFace word={back} hint="français" variant="back" />
        </div>
      </div>
    </div>
  );
}
