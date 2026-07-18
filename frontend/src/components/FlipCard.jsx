export default function FlipCard({ front, back, flipped, onClick }) {
  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  }

  return (
    <div className="[perspective:1200px] w-full max-w-sm h-56">
      <div
        role="button"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        className={`relative w-full h-full text-left cursor-pointer [transform-style:preserve-3d] transition-transform duration-500 ${
          flipped ? "[transform:rotateY(180deg)]" : ""
        }`}
      >
        <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-surface shadow-lg px-6 [backface-visibility:hidden]">
          <span className="text-3xl font-bold text-ink text-center">{front}</span>
        </div>
        <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-primary-light shadow-lg px-6 [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <span className="text-3xl font-bold text-primary-dark text-center">{back}</span>
        </div>
      </div>
    </div>
  );
}
