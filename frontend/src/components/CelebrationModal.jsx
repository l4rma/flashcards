import { useEffect } from "react";
import confetti from "canvas-confetti";
import CoinIcon from "./CoinIcon";

const HEADINGS = {
  achievement: "Grats! You earned an achievement!",
  quest: "Quest complete!",
  level_up: "Level up!",
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
      className="fixed inset-0 bg-ink/50 flex items-center justify-center px-4 z-50"
      onClick={onDismiss}
    >
      <div
        className="bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 max-w-xs w-full flex flex-col items-center gap-2 text-center"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-xs font-bold uppercase tracking-wide text-primary-dark">
          {HEADINGS[celebration.kind]}
        </p>
        <span className="text-6xl">{celebration.badge}</span>
        <h3 className="font-display font-semibold text-2xl text-ink">{celebration.title}</h3>
        <p className="text-sm text-ink-soft">{celebration.description}</p>
        <p className="text-sm font-bold text-primary-dark flex items-center justify-center gap-1.5">
          <CoinIcon className="w-4 h-4" /> +{celebration.coin_reward} coins
        </p>
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
