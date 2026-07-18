import { useEffect } from "react";
import confetti from "canvas-confetti";

const HEADINGS = {
  achievement: "Grats! You earned an achievement!",
  quest: "Quest complete!",
};

export default function CelebrationModal({ celebration, onDismiss }) {
  useEffect(() => {
    confetti({
      particleCount: 150,
      spread: 100,
      startVelocity: 40,
      origin: { y: 0.3 },
    });
  }, [celebration.kind, celebration.key]);

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center px-4 z-50"
      onClick={onDismiss}
    >
      <div
        className="bg-surface rounded-3xl shadow-lg p-6 max-w-xs w-full flex flex-col items-center gap-2 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-lg font-extrabold text-primary-dark">
          {HEADINGS[celebration.kind]}
        </p>
        <span className="text-6xl">{celebration.badge}</span>
        <h3 className="text-xl font-extrabold text-ink">{celebration.title}</h3>
        <p className="text-sm text-ink-soft">{celebration.description}</p>
        <p className="text-sm font-bold text-primary-dark">🪙 +{celebration.coin_reward} coins</p>
        <button
          type="button"
          onClick={onDismiss}
          className="mt-2 rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-6 py-2 text-sm"
        >
          Nice!
        </button>
      </div>
    </div>
  );
}
