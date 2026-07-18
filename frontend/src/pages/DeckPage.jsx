import { useEffect, useState } from "react";
import { createCard, deleteCard, listCards, listDueCards, updateCard } from "../api";

export default function DeckPage({ onAchievementsUnlocked, onQuestsCompleted }) {
  const [english, setEnglish] = useState("");
  const [french, setFrench] = useState("");
  const [status, setStatus] = useState(null);

  const [cards, setCards] = useState([]);
  const [dueCount, setDueCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ french: "", english: "" });

  async function refresh() {
    setLoading(true);
    const [allCards, due] = await Promise.all([listCards(), listDueCards()]);
    setCards(allCards);
    setDueCount(due.length);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!french.trim() || !english.trim()) return;
    try {
      const created = await createCard(french.trim(), english.trim());
      onAchievementsUnlocked?.(created.newly_unlocked_achievements);
      onQuestsCompleted?.(created.newly_completed_quests);
      setEnglish("");
      setFrench("");
      setStatus({ type: "success", message: "Card added!" });
      await refresh();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  function startEdit(card) {
    setEditingId(card.id);
    setDraft({ french: card.french, english: card.english });
  }

  async function saveEdit(id) {
    await updateCard(id, draft);
    setEditingId(null);
    await refresh();
  }

  async function handleDelete(id) {
    await deleteCard(id);
    await refresh();
  }

  return (
    <div className="flex flex-col items-center px-4 py-10 gap-10">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-extrabold text-ink mb-6 text-center">Add a card</h1>
        <form
          onSubmit={handleSubmit}
          className="w-full bg-surface rounded-3xl shadow-lg p-6 flex flex-col gap-4"
        >
          <label className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-ink-soft">Front</span>
            <input
              value={english}
              onChange={(e) => setEnglish(e.target.value)}
              placeholder="hello"
              className="rounded-2xl border border-primary-light bg-background px-4 py-3 text-ink outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-ink-soft">Back</span>
            <input
              value={french}
              onChange={(e) => setFrench(e.target.value)}
              placeholder="bonjour"
              className="rounded-2xl border border-primary-light bg-background px-4 py-3 text-ink outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <button
            type="submit"
            className="mt-2 rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold py-3"
          >
            Add card
          </button>
          {status && (
            <p
              className={`text-sm font-semibold text-center ${
                status.type === "success" ? "text-primary-dark" : "text-wrong-dark"
              }`}
            >
              {status.message}
            </p>
          )}
        </form>
      </div>

      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-extrabold text-ink mb-2 text-center">Manage cards</h1>
        <p className="text-sm font-semibold text-ink-soft mb-6 text-center">
          {cards.length} card{cards.length === 1 ? "" : "s"} total ·{" "}
          {dueCount} not yet correct this session
        </p>
        {loading ? (
          <p className="text-center py-10 text-ink-soft">Loading…</p>
        ) : (
          <div className="flex flex-col gap-3">
            {cards.length === 0 && (
              <p className="text-center text-ink-soft">No cards yet — add one!</p>
            )}
            {cards.map((card) => (
              <div
                key={card.id}
                className="bg-surface rounded-2xl shadow-md px-4 py-3 flex items-center justify-between gap-3"
              >
                {editingId === card.id ? (
                  <div className="flex flex-col gap-2 flex-1">
                    <input
                      className="rounded-xl border border-primary-light bg-background px-3 py-2"
                      value={draft.english}
                      onChange={(e) => setDraft({ ...draft, english: e.target.value })}
                      placeholder="Front"
                    />
                    <input
                      className="rounded-xl border border-primary-light bg-background px-3 py-2"
                      value={draft.french}
                      onChange={(e) => setDraft({ ...draft, french: e.target.value })}
                      placeholder="Back"
                    />
                    <button
                      type="button"
                      onClick={() => saveEdit(card.id)}
                      className="rounded-full bg-primary text-white font-bold py-2 text-sm"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <>
                    <div>
                      <p className="font-bold text-ink">{card.english}</p>
                      <p className="text-sm text-ink-soft">{card.french}</p>
                      <p className="text-xs text-ink-soft mt-1">
                        interval: {card.interval_days}d · due {card.due_date}
                      </p>
                      <p className="text-xs text-ink-soft">
                        ✓ {card.times_correct} · ✗ {card.times_wrong}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => startEdit(card)}
                        className="rounded-full bg-primary-light text-primary-dark font-semibold px-3 py-1 text-sm"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(card.id)}
                        className="rounded-full bg-wrong/10 text-wrong-dark font-semibold px-3 py-1 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
