import { useEffect, useState } from "react";
import { getCollection, getStats } from "./api";
import { handleRedirectCallback, isAuthenticated, login } from "./auth";
import CelebrationModal from "./components/CelebrationModal";
import StatsBar from "./components/StatsBar";
import { applyCollectionTheme } from "./collectionTheme";
import CollectionPage from "./pages/CollectionPage";
import DeckPage from "./pages/DeckPage";
import ProfilePage from "./pages/ProfilePage";
import SettingsPage from "./pages/SettingsPage";
import TrainPage from "./pages/TrainPage";

const TABS = [
  { key: "train", label: "Train", icon: "🏋️" },
  { key: "deck", label: "Deck", icon: "📚" },
  { key: "profile", label: "Profile", icon: "📈" },
  { key: "collection", label: "Collection", icon: "🎁" },
  { key: "settings", label: "Settings", icon: "⚙️" },
];

function App() {
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [tab, setTab] = useState("train");
  const [stats, setStats] = useState(null);
  const [celebrationQueue, setCelebrationQueue] = useState([]);

  async function refreshStats() {
    setStats(await getStats());
  }

  useEffect(() => {
    async function authenticate() {
      try {
        if (new URLSearchParams(window.location.search).has("code")) {
          await handleRedirectCallback();
        }
        if (!isAuthenticated()) {
          login(); // redirects the page away — this effect never continues
          return;
        }
        setAuthReady(true);
        setStats(await getStats());
        // Applies the equipped color/font theme (if any) at startup — a
        // brief flash of the default green before this resolves is an
        // acceptable, subtle cosmetic gap (unlike light/dark, which has
        // its own synchronous pre-paint script in index.html to avoid a
        // much more jarring full-background flash).
        const collection = await getCollection();
        const equipped = collection.themes.find((t) => t.equipped);
        applyCollectionTheme(equipped || null);
      } catch (err) {
        // A `?code=` can't be exchanged twice, so a failed attempt (e.g. a
        // lost/mismatched PKCE verifier — seen on mobile Safari, where
        // cross-site storage restrictions can drop sessionStorage across
        // the redirect to Cognito and back) must not leave a stale `code`
        // in the URL for a retry to immediately fail on again.
        console.error("Authentication failed:", err);
        const url = new URL(window.location.href);
        url.searchParams.delete("code");
        url.searchParams.delete("state");
        window.history.replaceState({}, "", url.pathname + url.search);
        setAuthError(err.message || "Sign-in failed");
      }
    }
    authenticate();
  }, []);

  // Achievement/level-up rewards pay out coins (and, for level-ups,
  // lootboxes) immediately server-side, but the top stats bar only shows
  // whatever `stats` was last fetched — without this, the coin count
  // visibly lagged until the next action that happened to call
  // refreshStats (e.g. grading a card), even though the reward had
  // already landed. Refreshing here, once, covers every action that can
  // report a reward (add/edit a card, grade, session-complete, equip,
  // profile update, lootbox open, practice completion) without needing
  // each page to remember its own onChanged/onGraded call.
  function handleAchievementsUnlocked(newlyUnlocked) {
    if (newlyUnlocked?.length) {
      setCelebrationQueue((queue) => [
        ...queue,
        ...newlyUnlocked.map((a) => ({ kind: "achievement", ...a })),
      ]);
      refreshStats();
    }
  }

  function handleQuestsCompleted(newlyCompleted) {
    if (newlyCompleted?.length) {
      setCelebrationQueue((queue) => [
        ...queue,
        ...newlyCompleted.map((q) => ({ kind: "quest", ...q })),
      ]);
      refreshStats();
    }
  }

  function handleLeveledUp(newlyLeveledUp) {
    if (newlyLeveledUp?.length) {
      setCelebrationQueue((queue) => [
        ...queue,
        ...newlyLeveledUp.map((l) => ({ kind: "level_up", ...l })),
      ]);
      refreshStats();
    }
  }

  if (authError) {
    return (
      <div className="text-center py-10 text-ink-soft">
        <p>Sign-in failed: {authError}</p>
        <button
          className="mt-3 px-4 py-2 rounded bg-primary text-white"
          onClick={() => {
            setAuthError(null);
            login();
          }}
        >
          Try again
        </button>
      </div>
    );
  }

  if (!authReady) {
    return <p className="text-center py-10 text-ink-soft">Signing in…</p>;
  }

  return (
    <div className="min-h-svh bg-background flex flex-col">
      <StatsBar stats={stats} />
      <main className="flex-1 flex flex-col pb-28">
        {tab === "train" && (
          <TrainPage
            key={tab}
            onGraded={refreshStats}
            onAchievementsUnlocked={handleAchievementsUnlocked}
            onQuestsCompleted={handleQuestsCompleted}
            onLeveledUp={handleLeveledUp}
          />
        )}
        {tab === "deck" && (
          <DeckPage
            key={tab}
            onAchievementsUnlocked={handleAchievementsUnlocked}
            onQuestsCompleted={handleQuestsCompleted}
            onLeveledUp={handleLeveledUp}
          />
        )}
        {tab === "profile" && <ProfilePage key={tab} />}
        {tab === "collection" && (
          <CollectionPage
            key={tab}
            onChanged={refreshStats}
            onAchievementsUnlocked={handleAchievementsUnlocked}
            onLeveledUp={handleLeveledUp}
          />
        )}
        {tab === "settings" && (
          <SettingsPage
            key={tab}
            onChanged={refreshStats}
            onAchievementsUnlocked={handleAchievementsUnlocked}
            onLeveledUp={handleLeveledUp}
          />
        )}
      </main>

      <nav className="fixed bottom-0 inset-x-0 flex justify-center pb-safe pt-2 px-4 pointer-events-none">
        <div className="pointer-events-auto flex gap-1 bg-surface/95 backdrop-blur rounded-full shadow-lg shadow-ink/10 ring-1 ring-ink/5 p-1.5">
          {TABS.map(({ key, label, icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              aria-label={label}
              aria-current={tab === key ? "page" : undefined}
              title={label}
              className={`rounded-full w-14 h-14 flex items-center justify-center text-2xl transition active:scale-90 ${
                tab === key
                  ? "bg-primary text-white shadow-md shadow-primary/30"
                  : "bg-transparent text-ink-soft hover:bg-primary-light hover:text-primary-dark"
              }`}
            >
              {icon}
            </button>
          ))}
        </div>
      </nav>

      {celebrationQueue.length > 0 && (
        <CelebrationModal
          celebration={celebrationQueue[0]}
          onDismiss={() => setCelebrationQueue((queue) => queue.slice(1))}
        />
      )}
    </div>
  );
}

export default App;
