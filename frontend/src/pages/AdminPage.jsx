import { useState } from "react";
import { deleteAllCards, resetAllProgress } from "../api";
import { logout } from "../auth";
import ThemeToggle from "../components/ThemeToggle";

export default function AdminPage({ onChanged }) {
  const [message, setMessage] = useState(null);

  async function handleResetAllProgress() {
    if (
      !window.confirm(
        "Reset all progress? Streak, coins, session baseline, every card's " +
          "scheduling, and all achievement unlocks go back to a fresh start. " +
          "Cards themselves are kept."
      )
    ) {
      return;
    }
    await resetAllProgress();
    setMessage("All progress reset.");
    onChanged?.();
  }

  async function handleDeleteAllCards() {
    if (!window.confirm("Delete ALL cards? This cannot be undone.")) return;
    await deleteAllCards();
    setMessage("All cards deleted.");
    onChanged?.();
  }

  return (
    <div className="flex flex-col items-center px-4 pt-8 pb-10 gap-6">
      <h1 className="font-display font-semibold text-2xl text-ink self-start w-full max-w-sm">
        Admin
      </h1>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-3">
        <p className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Appearance</p>
        <ThemeToggle />
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-3">
        <button
          type="button"
          onClick={handleResetAllProgress}
          className="rounded-full bg-progress-track hover:bg-progress/20 text-progress font-bold py-3 transition"
        >
          Reset all progress
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Log out?")) logout();
          }}
          className="rounded-full bg-primary-light hover:bg-primary/20 text-primary-dark font-bold py-3 transition"
        >
          Log out
        </button>
      </div>

      {message && <p className="text-sm font-semibold text-primary-dark">{message}</p>}

      <div className="w-full max-w-sm rounded-3xl shadow-lg p-6 flex flex-col gap-3 bg-wrong/5 ring-1 ring-wrong/20">
        <p className="text-xs font-bold uppercase tracking-wide text-wrong-dark">Danger zone</p>
        <button
          type="button"
          onClick={handleDeleteAllCards}
          className="rounded-full bg-wrong hover:bg-wrong-dark active:scale-95 transition text-white font-bold py-3"
        >
          Delete ALL cards
        </button>
      </div>
    </div>
  );
}
