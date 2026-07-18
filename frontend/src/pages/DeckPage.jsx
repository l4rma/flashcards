import { useEffect, useState } from "react";
import { createCard, deleteCard, listCards, listDueCards, updateCard } from "../api";

// A tiny, stable (id-derived, not random) tilt per row so the deck list
// reads as a loose stack of index cards rather than a rigid table row —
// same "physical card" motif as the flip card's punch hole.
function tiltFor(id) {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return ((hash % 100) / 100) * 1.2 - 0.6; // -0.6deg .. 0.6deg
}

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
    <div className="flex flex-col items-center px-4 pt-8 pb-10 gap-10">
      <div className="w-full max-w-sm">
        <h1 className="font-display font-semibold text-2xl text-ink mb-4">Add a card</h1>
        <form
          onSubmit={handleSubmit}
          className="w-full bg-primary-light/60 rounded-3xl shadow-md ring-1 ring-primary/10 p-6 flex flex-col gap-4"
        >
          <label className="flex flex-col gap-1">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Front</span>
            <input
              value={english}
              onChange={(e) => setEnglish(e.target.value)}
              placeholder="hello"
              className="rounded-2xl border border-primary/20 bg-surface px-4 py-3 text-ink font-display font-medium text-lg outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Back</span>
            <input
              value={french}
              onChange={(e) => setFrench(e.target.value)}
              placeholder="bonjour"
              className="rounded-2xl border border-primary/20 bg-surface px-4 py-3 text-ink font-display font-medium text-lg outline-none focus:ring-2 focus:ring-primary"
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
        <div className="flex items-baseline justify-between mb-4">
          <h1 className="font-display font-semibold text-2xl text-ink">Your deck</h1>
          <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">
            {cards.length} card{cards.length === 1 ? "" : "s"} · {dueCount} due
          </span>
        </div>
        {loading ? (
          <p className="text-center py-10 text-ink-soft">Loading…</p>
        ) : (
          <div className="flex flex-col gap-4">
            {cards.length === 0 && (
              <p className="text-center text-ink-soft">No cards yet — add one above!</p>
            )}
            {cards.map((card) => (
              <div
                key={card.id}
                style={editingId === card.id ? undefined : { transform: `rotate(${tiltFor(card.id)}deg)` }}
                className="relative bg-surface rounded-2xl shadow-md ring-1 ring-ink/10 px-4 py-3.5 flex items-center justify-between gap-3"
              >
                <span className="absolute top-3 left-3 w-2 h-2 rounded-full bg-background ring-1 ring-ink/10" />
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
                    <div className="pl-3">
                      <p className="font-display font-medium text-lg text-ink leading-tight">
                        {card.english}
                      </p>
                      <p className="text-sm text-ink-soft">{card.french}</p>
                      <p className="text-xs text-ink-soft/70 mt-1.5">
                        {card.interval_days}d interval · due {card.due_date}
                      </p>
                      <p className="text-xs text-ink-soft/70">
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
