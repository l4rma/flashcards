import { useEffect, useState } from "react";
import { getStats } from "./api";
import { handleRedirectCallback, isAuthenticated, login } from "./auth";
import CelebrationModal from "./components/CelebrationModal";
import StatsBar from "./components/StatsBar";
import AdminPage from "./pages/AdminPage";
import DeckPage from "./pages/DeckPage";
import ProgressPage from "./pages/ProgressPage";
import TrainPage from "./pages/TrainPage";

const TABS = [
  { key: "train", label: "Train", icon: "🏋️" },
  { key: "deck", label: "Deck", icon: "📚" },
  { key: "progress", label: "Progress", icon: "📈" },
  { key: "admin", label: "Admin", icon: "⚙️" },
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

  function handleAchievementsUnlocked(newlyUnlocked) {
    if (newlyUnlocked?.length) {
      setCelebrationQueue((queue) => [
        ...queue,
        ...newlyUnlocked.map((a) => ({ kind: "achievement", ...a })),
      ]);
    }
  }

  function handleQuestsCompleted(newlyCompleted) {
    if (newlyCompleted?.length) {
      setCelebrationQueue((queue) => [
        ...queue,
        ...newlyCompleted.map((q) => ({ kind: "quest", ...q })),
      ]);
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
          />
        )}
        {tab === "deck" && (
          <DeckPage
            key={tab}
            onAchievementsUnlocked={handleAchievementsUnlocked}
            onQuestsCompleted={handleQuestsCompleted}
          />
        )}
        {tab === "progress" && <ProgressPage key={tab} />}
        {tab === "admin" && <AdminPage key={tab} onChanged={refreshStats} />}
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
