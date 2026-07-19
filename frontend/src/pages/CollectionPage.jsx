import { useEffect, useState } from "react";
import { buyLootbox, equipCollectible, getCollection, openLootbox } from "../api";
import { applyCollectionTheme } from "../collectionTheme";
import CoinIcon from "../components/CoinIcon";

const RARITY_LABEL = {
  common: "Common",
  rare: "Rare",
  epic: "Epic",
  legendary: "Legendary",
};

const REWARD_ICON = { coins: "🪙", xp: "⚡", title: "🏷️", theme: "🎨" };

function rewardLabel(reward) {
  if (reward.kind === "coins") return `+${reward.amount} coins`;
  if (reward.kind === "xp") return `+${reward.amount} XP`;
  return reward.name;
}

export default function CollectionPage({ onChanged, onAchievementsUnlocked, onLeveledUp }) {
  const [collection, setCollection] = useState(null);
  const [busyTier, setBusyTier] = useState(null);
  const [reveal, setReveal] = useState(null);
  const [status, setStatus] = useState(null);

  async function refresh() {
    setCollection(await getCollection());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleBuy(tier) {
    setBusyTier(tier);
    try {
      const updated = await buyLootbox(tier);
      setCollection(updated);
      onChanged?.();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    } finally {
      setBusyTier(null);
    }
  }

  async function handleOpen(tier) {
    setBusyTier(tier);
    try {
      const result = await openLootbox(tier);
      setReveal(result);
      onAchievementsUnlocked?.(result.newly_unlocked_achievements);
      onLeveledUp?.(result.newly_leveled_up);
      await refresh();
      onChanged?.();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    } finally {
      setBusyTier(null);
    }
  }

  async function handleEquipTitle(title) {
    const nextTitle = collection.titles.find((t) => t.key === title.key)?.equipped ? null : title.key;
    try {
      await equipCollectible({ title: nextTitle });
      await refresh();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  async function handleEquipTheme(theme) {
    const isEquipped = collection.themes.find((t) => t.key === theme.key)?.equipped;
    const nextTheme = isEquipped ? null : theme.key;
    try {
      await equipCollectible({ theme: nextTheme });
      applyCollectionTheme(isEquipped ? null : theme);
      await refresh();
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  if (!collection) {
    return <p className="text-center py-10 text-ink-soft">Loading…</p>;
  }

  return (
    <div className="flex flex-col items-center px-4 pt-8 pb-10 gap-8">
      <h1 className="font-display font-semibold text-2xl text-ink self-start w-full max-w-sm">
        Collection
      </h1>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-4">
        <h2 className="font-display font-semibold text-lg text-ink">Lootboxes</h2>
        {collection.lootboxes.map((box) => (
          <div key={box.tier} className="flex items-center justify-between gap-3">
            <div>
              <p className="font-semibold text-ink">{box.name}</p>
              <p className="text-xs text-ink-soft">You have {box.count}</p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                type="button"
                disabled={busyTier === box.tier}
                onClick={() => handleBuy(box.tier)}
                className="rounded-full bg-primary-light text-primary-dark font-bold px-3 py-2 text-sm disabled:opacity-50 flex items-center gap-1"
              >
                <CoinIcon className="w-3.5 h-3.5" /> {box.coin_cost}
              </button>
              <button
                type="button"
                disabled={busyTier === box.tier || box.count === 0}
                onClick={() => handleOpen(box.tier)}
                className="rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-4 py-2 text-sm disabled:opacity-40"
              >
                Open
              </button>
            </div>
          </div>
        ))}
        {status && (
          <p
            className={`text-sm font-semibold ${
              status.type === "success" ? "text-primary-dark" : "text-wrong-dark"
            }`}
          >
            {status.message}
          </p>
        )}
      </div>

      <div className="w-full max-w-sm">
        <h2 className="font-display font-semibold text-lg text-ink mb-3">Titles</h2>
        <div className="grid grid-cols-2 gap-3">
          {collection.titles.map((title) => (
            <button
              key={title.key}
              type="button"
              disabled={!title.owned}
              onClick={() => handleEquipTitle(title)}
              className={`rounded-2xl shadow-md ring-1 p-3 text-left transition active:scale-95 ${
                title.equipped
                  ? "bg-primary/20 ring-2 ring-primary"
                  : title.owned
                    ? "bg-surface ring-ink/10"
                    : "bg-surface/60 ring-ink/10 grayscale opacity-50"
              }`}
            >
              <p className="text-sm font-semibold text-ink">{title.name}</p>
              <p className="text-xs text-ink-soft/70 uppercase tracking-wide">
                {RARITY_LABEL[title.rarity]}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="w-full max-w-sm">
        <h2 className="font-display font-semibold text-lg text-ink mb-3">Card colours</h2>
        <div className="grid grid-cols-2 gap-3">
          {collection.themes.map((theme) => (
            <button
              key={theme.key}
              type="button"
              disabled={!theme.owned}
              onClick={() => handleEquipTheme(theme)}
              className={`rounded-2xl shadow-md ring-1 p-3 flex items-center gap-2 text-left transition active:scale-95 ${
                theme.equipped
                  ? "bg-primary/20 ring-2 ring-primary"
                  : theme.owned
                    ? "bg-surface ring-ink/10"
                    : "bg-surface/60 ring-ink/10 grayscale opacity-50"
              }`}
            >
              <span
                className="w-5 h-5 rounded-full shrink-0 ring-1 ring-ink/10"
                style={{ backgroundColor: theme.colors.primary }}
              />
              <span>
                <p className="text-sm font-semibold text-ink">{theme.name}</p>
                <p className="text-xs text-ink-soft/70 uppercase tracking-wide">
                  {RARITY_LABEL[theme.rarity]}
                </p>
              </span>
            </button>
          ))}
        </div>
      </div>

      {reveal && (
        <div
          className="fixed inset-0 bg-ink/50 flex items-center justify-center px-4 z-50"
          onClick={() => setReveal(null)}
        >
          <div
            className="bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 max-w-xs w-full flex flex-col items-center gap-2 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-xs font-bold uppercase tracking-wide text-primary-dark">You got</p>
            <span className="text-6xl">{REWARD_ICON[reveal.kind]}</span>
            <h3 className="font-display font-semibold text-2xl text-ink">{rewardLabel(reveal)}</h3>
            <button
              type="button"
              onClick={() => setReveal(null)}
              className="mt-2 rounded-full bg-primary hover:bg-primary-dark active:scale-95 transition text-white font-bold px-6 py-2 text-sm"
            >
              Nice!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
