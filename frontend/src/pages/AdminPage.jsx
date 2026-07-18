import { useState } from "react";
import { deleteAllCards, resetAllProgress } from "../api";
import { logout } from "../auth";

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
    <div className="flex flex-col items-center px-4 py-10 gap-6">
      <h1 className="text-2xl font-extrabold text-ink">Admin</h1>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-3">
        <button
          type="button"
          onClick={handleResetAllProgress}
          className="rounded-full bg-progress-track hover:bg-progress/20 text-progress font-bold py-2 transition"
        >
          Reset all progress
        </button>
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-3">
        <p className="text-sm font-bold text-wrong-dark">Danger zone</p>
        <button
          type="button"
          onClick={handleDeleteAllCards}
          className="rounded-full bg-wrong hover:bg-wrong-dark active:scale-95 transition text-white font-bold py-2"
        >
          Delete ALL cards
        </button>
      </div>

      {message && <p className="text-sm font-semibold text-primary-dark">{message}</p>}

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-3">
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Log out?")) logout();
          }}
          className="rounded-full bg-primary-light hover:bg-primary/20 text-primary-dark font-bold py-2 transition"
        >
          Log out
        </button>
      </div>
    </div>
  );
}
