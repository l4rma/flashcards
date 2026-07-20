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

function normalize(word) {
  return word.trim().toLowerCase();
}

// How long to wait after the user stops typing before checking for a
// duplicate — checking on every keystroke flags half-typed words that
// happen to match while the user is still mid-edit.
const DUPLICATE_CHECK_DELAY_MS = 500;

function useDebounced(value, delayMs) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export default function DeckPage({ onAchievementsUnlocked, onQuestsCompleted, onLeveledUp }) {
  const [english, setEnglish] = useState("");
  const [french, setFrench] = useState("");
  const [label, setLabel] = useState("");
  const [status, setStatus] = useState(null);

  const [cards, setCards] = useState([]);
  const [dueCount, setDueCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ french: "", english: "", label: "" });
  const [activeLabel, setActiveLabel] = useState(null); // null = "All"

  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [bulkLabel, setBulkLabel] = useState("");

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

  function isFrontDuplicate(value) {
    return value.trim() && cards.some((c) => normalize(c.english) === normalize(value));
  }
  function isBackDuplicate(value) {
    return value.trim() && cards.some((c) => normalize(c.french) === normalize(value));
  }

  // Debounced so warnings don't flicker on while the user is still typing —
  // only shown once they pause. handleSubmit still checks the live
  // (non-debounced) values below, so a fast type-then-submit is never
  // let through just because the debounce hadn't caught up yet.
  const debouncedEnglish = useDebounced(english, DUPLICATE_CHECK_DELAY_MS);
  const debouncedFrench = useDebounced(french, DUPLICATE_CHECK_DELAY_MS);
  const frontDuplicate = isFrontDuplicate(debouncedEnglish);
  const backDuplicate = isBackDuplicate(debouncedFrench);

  const labels = [...new Set(cards.map((c) => c.label).filter(Boolean))].sort();
  const filteredCards = activeLabel === null ? cards : cards.filter((c) => c.label === activeLabel);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!french.trim() || !english.trim()) return;
    if (isFrontDuplicate(english) || isBackDuplicate(french)) {
      setStatus({
        type: "error",
        message: isFrontDuplicate(english)
          ? "A card with this front already exists."
          : "A card with this back already exists.",
      });
      return;
    }
    try {
      const created = await createCard(french.trim(), english.trim(), label.trim() || null);
      onAchievementsUnlocked?.(created.newly_unlocked_achievements);
      onQuestsCompleted?.(created.newly_completed_quests);
      onLeveledUp?.(created.newly_leveled_up);
      setEnglish("");
      setFrench("");
      setLabel("");
      setStatus({ type: "success", message: "Card added!" });
      await refresh();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  function startEdit(card) {
    setEditingId(card.id);
    setDraft({ french: card.french, english: card.english, label: card.label || "" });
  }

  async function saveEdit(id) {
    const updated = await updateCard(id, draft);
    onAchievementsUnlocked?.(updated.newly_unlocked_achievements);
    onLeveledUp?.(updated.newly_leveled_up);
    setEditingId(null);
    await refresh();
  }

  async function handleDelete(id) {
    await deleteCard(id);
    await refresh();
  }

  function toggleSelectMode() {
    setSelectMode((v) => !v);
    setSelectedIds(new Set());
    setBulkLabel("");
  }

  function toggleSelected(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAllVisible() {
    setSelectedIds(new Set(filteredCards.map((c) => c.id)));
  }

  async function applyBulkLabel(e) {
    e.preventDefault();
    if (selectedIds.size === 0) return;
    const value = bulkLabel.trim() || null;
    const results = await Promise.all([...selectedIds].map((id) => updateCard(id, { label: value })));
    onAchievementsUnlocked?.(results.flatMap((r) => r.newly_unlocked_achievements));
    onLeveledUp?.(results.flatMap((r) => r.newly_leveled_up));
    toggleSelectMode();
    await refresh();
  }

  async function bulkDelete() {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Delete ${selectedIds.size} selected card(s)? This cannot be undone.`)) return;
    await Promise.all([...selectedIds].map((id) => deleteCard(id)));
    toggleSelectMode();
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
            {frontDuplicate && (
              <span className="text-xs font-semibold text-wrong-dark">
                A card with this front already exists.
              </span>
            )}
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Back</span>
            <input
              value={french}
              onChange={(e) => setFrench(e.target.value)}
              placeholder="bonjour"
              className="rounded-2xl border border-primary/20 bg-surface px-4 py-3 text-ink font-display font-medium text-lg outline-none focus:ring-2 focus:ring-primary"
            />
            {backDuplicate && (
              <span className="text-xs font-semibold text-wrong-dark">
                A card with this back already exists.
              </span>
            )}
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">
              Sub-deck (optional)
            </span>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. animals"
              className="rounded-2xl border border-primary/20 bg-surface px-4 py-3 text-ink text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </label>
          <button
            type="submit"
            disabled={frontDuplicate || backDuplicate}
            className="mt-2 rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold py-3 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-primary"
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
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">
              {cards.length} card{cards.length === 1 ? "" : "s"} · {dueCount} due
            </span>
            {cards.length > 0 && (
              <button
                type="button"
                onClick={toggleSelectMode}
                className="text-xs font-bold uppercase tracking-wide text-primary-dark hover:underline"
              >
                {selectMode ? "Cancel" : "Select"}
              </button>
            )}
          </div>
        </div>
        {selectMode && (
          <div className="bg-surface rounded-2xl shadow-md ring-1 ring-ink/10 p-4 mb-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-ink">{selectedIds.size} selected</span>
              <button
                type="button"
                onClick={selectAllVisible}
                className="text-xs font-bold text-primary-dark hover:underline"
              >
                Select all
              </button>
            </div>
            <form onSubmit={applyBulkLabel} className="flex gap-2">
              <input
                value={bulkLabel}
                onChange={(e) => setBulkLabel(e.target.value)}
                placeholder="Set sub-deck for selected…"
                className="flex-1 min-w-0 rounded-xl border border-primary-light bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="submit"
                disabled={selectedIds.size === 0}
                className="rounded-full bg-primary-light text-primary-dark font-bold px-4 py-2 text-sm shrink-0 disabled:opacity-40"
              >
                Apply
              </button>
            </form>
            <button
              type="button"
              onClick={bulkDelete}
              disabled={selectedIds.size === 0}
              className="rounded-full bg-wrong hover:bg-wrong-dark active:scale-95 transition text-white font-bold py-2.5 text-sm disabled:opacity-40"
            >
              Delete selected
            </button>
          </div>
        )}
        {labels.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              type="button"
              onClick={() => setActiveLabel(null)}
              className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${
                activeLabel === null
                  ? "bg-primary text-white"
                  : "bg-primary-light text-primary-dark hover:bg-primary/20"
              }`}
            >
              All
            </button>
            {labels.map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setActiveLabel(l)}
                className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${
                  activeLabel === l
                    ? "bg-primary text-white"
                    : "bg-primary-light text-primary-dark hover:bg-primary/20"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        )}
        {loading ? (
          <p className="text-center py-10 text-ink-soft">Loading…</p>
        ) : (
          <div className="flex flex-col gap-4">
            {filteredCards.length === 0 && (
              <p className="text-center text-ink-soft">
                {cards.length === 0 ? "No cards yet — add one above!" : "No cards with this label."}
              </p>
            )}
            {filteredCards.map((card) => (
              <div
                key={card.id}
                style={editingId === card.id ? undefined : { transform: `rotate(${tiltFor(card.id)}deg)` }}
                onClick={selectMode ? () => toggleSelected(card.id) : undefined}
                className={`relative bg-surface rounded-2xl shadow-md px-4 py-3.5 flex items-center justify-between gap-3 ${
                  selectMode ? "cursor-pointer" : ""
                } ${
                  selectMode && selectedIds.has(card.id)
                    ? "ring-2 ring-primary"
                    : "ring-1 ring-ink/10"
                }`}
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
                    <input
                      className="rounded-xl border border-primary-light bg-background px-3 py-2 text-sm"
                      value={draft.label}
                      onChange={(e) => setDraft({ ...draft, label: e.target.value })}
                      placeholder="Sub-deck (optional)"
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
                      {card.label && (
                        <span className="inline-block mt-1.5 rounded-full bg-primary-light text-primary-dark text-xs font-bold px-2 py-0.5">
                          {card.label}
                        </span>
                      )}
                    </div>
                    {selectMode ? (
                      <input
                        type="checkbox"
                        checked={selectedIds.has(card.id)}
                        onChange={() => toggleSelected(card.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-5 h-5 accent-primary shrink-0"
                      />
                    ) : (
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
                    )}
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
