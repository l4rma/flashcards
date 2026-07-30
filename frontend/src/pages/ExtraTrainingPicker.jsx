import { useEffect, useState } from "react";
import { getPrebuiltDeck, getPrebuiltDecks, listCards } from "../api";

function toQueue(cards) {
  return cards.map((c, i) => ({ id: c.id ?? `prebuilt-${i}`, english: c.english, french: c.french }));
}

// Fisher-Yates — order only needs to be scrambled for the practice queue
// itself, not persisted or reproducible, so no seed handling.
function shuffle(cards) {
  const result = [...cards];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

const ORDER_OPTIONS = [
  { key: "ordered", label: "Ordered" },
  { key: "shuffled", label: "Shuffled" },
];

// Same row shape for "your decks" and pre-built decks — title + card
// count on the left, Preview/Practice on the right — per explicit
// request that the two sections shouldn't look different from each
// other. Own-deck rows never need `disabled` for pending-network reasons
// (their cards are already in hand, no fetch), only for an empty deck.
function DeckRow({ title, count, onPreview, onPractice, previewDisabled, practiceDisabled }) {
  return (
    <div className="bg-surface rounded-2xl shadow-md ring-1 ring-ink/10 px-4 py-3.5 flex items-center justify-between gap-3">
      <div>
        <p className="font-display font-medium text-ink leading-tight">{title}</p>
        <p className="text-xs text-ink-soft">
          {count} card{count === 1 ? "" : "s"}
        </p>
      </div>
      <div className="flex gap-2 shrink-0">
        <button
          type="button"
          disabled={previewDisabled}
          onClick={onPreview}
          className="rounded-full bg-primary-light text-primary-dark font-semibold px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Preview
        </button>
        <button
          type="button"
          disabled={practiceDisabled}
          onClick={onPractice}
          className="rounded-full bg-primary text-white font-semibold px-3 py-1.5 text-sm disabled:opacity-50"
        >
          Practice
        </button>
      </div>
    </div>
  );
}

export default function ExtraTrainingPicker({ onStart, onClose }) {
  const [cards, setCards] = useState(null);
  const [prebuiltDecks, setPrebuiltDecks] = useState(null);
  const [preview, setPreview] = useState(null); // { title, cards } | null
  const [pendingKey, setPendingKey] = useState(null); // deck key currently loading (preview or practice)
  const [order, setOrder] = useState("ordered");

  function orderCards(list) {
    return order === "shuffled" ? shuffle(list) : list;
  }

  useEffect(() => {
    listCards().then(setCards);
    getPrebuiltDecks().then(setPrebuiltDecks);
  }, []);

  const labels = cards ? [...new Set(cards.map((c) => c.label).filter(Boolean))].sort() : [];

  function previewOwn(title, ownCards) {
    setPreview({ title, cards: ownCards });
  }

  async function handlePreview(deck) {
    setPendingKey(deck.key);
    try {
      setPreview(await getPrebuiltDeck(deck.key));
    } finally {
      setPendingKey(null);
    }
  }

  async function handlePractice(deck) {
    setPendingKey(deck.key);
    try {
      const full = await getPrebuiltDeck(deck.key);
      onStart(toQueue(orderCards(full.cards)), full.title, "prebuilt");
    } finally {
      setPendingKey(null);
    }
  }

  return (
    <div className="flex-1 flex flex-col items-center px-4 pt-8 pb-10 gap-6">
      <div className="w-full max-w-sm flex items-start justify-between gap-3">
        <div>
          <h1 className="font-display font-semibold text-2xl text-ink">Extra Training</h1>
          <p className="text-sm text-ink-soft mt-0.5">Practice without changing your due dates.</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Extra Training"
          className="rounded-full w-9 h-9 flex items-center justify-center bg-surface shadow-md ring-1 ring-ink/10 text-ink-soft hover:text-ink active:scale-90 transition shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="w-full max-w-sm flex bg-background rounded-full p-1 gap-1">
        {ORDER_OPTIONS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setOrder(key)}
            aria-pressed={order === key}
            className={`flex-1 rounded-full py-2 text-sm font-bold transition active:scale-95 ${
              order === key ? "bg-primary text-white" : "text-ink-soft hover:text-ink"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {cards === null || prebuiltDecks === null ? (
        <p className="text-center py-10 text-ink-soft">Loading…</p>
      ) : (
        <>
          <div className="w-full max-w-sm flex flex-col gap-3">
            <p className="text-xs font-bold uppercase tracking-wide text-ink-soft px-1">Your decks</p>
            <DeckRow
              title="All my cards"
              count={cards.length}
              previewDisabled={cards.length === 0}
              practiceDisabled={cards.length === 0}
              onPreview={() => previewOwn("All my cards", cards)}
              onPractice={() => onStart(toQueue(orderCards(cards)), "All my cards", "own_deck")}
            />
            {labels.map((l) => {
              const inLabel = cards.filter((c) => c.label === l);
              return (
                <DeckRow
                  key={l}
                  title={l}
                  count={inLabel.length}
                  onPreview={() => previewOwn(l, inLabel)}
                  onPractice={() => onStart(toQueue(orderCards(inLabel)), l, "sub_deck")}
                />
              );
            })}
            {cards.length === 0 && (
              <p className="text-xs text-ink-soft text-center">Add cards in Deck first.</p>
            )}
          </div>

          {prebuiltDecks.length > 0 && (
            <div className="w-full max-w-sm flex flex-col gap-3">
              <p className="text-xs font-bold uppercase tracking-wide text-ink-soft px-1">
                Pre-built decks
              </p>
              {prebuiltDecks.map((deck) => (
                <DeckRow
                  key={deck.key}
                  title={deck.title}
                  count={deck.card_count}
                  previewDisabled={pendingKey === deck.key}
                  practiceDisabled={pendingKey === deck.key}
                  onPreview={() => handlePreview(deck)}
                  onPractice={() => handlePractice(deck)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {preview && (
        <div
          className="fixed inset-0 bg-ink/40 flex items-center justify-center px-4 z-20"
          onClick={() => setPreview(null)}
        >
          <div
            className="bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 max-w-xs w-full max-h-[75vh] flex flex-col gap-3"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-display font-semibold text-lg text-ink">{preview.title}</h3>
              <button
                type="button"
                onClick={() => setPreview(null)}
                aria-label="Close preview"
                className="rounded-full w-7 h-7 flex items-center justify-center text-ink-soft hover:text-ink shrink-0"
              >
                ✕
              </button>
            </div>
            <div className="overflow-y-auto flex flex-col gap-1.5 pr-1 -mr-1">
              {preview.cards.map((c, i) => (
                <p key={i} className="text-sm text-ink-soft border-b border-primary-light/60 pb-1.5">
                  {c.english}
                </p>
              ))}
            </div>
            <button
              type="button"
              onClick={() => setPreview(null)}
              className="mt-1 rounded-full bg-primary-light text-primary-dark font-bold px-6 py-2 text-sm self-center"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
