import { useEffect, useState } from "react";
import { deleteAllCards, getStats, resetAllProgress, updateProfile } from "../api";
import { AVATARS } from "../avatars";
import { changePassword, logout } from "../auth";
import ThemeToggle from "../components/ThemeToggle";

export default function SettingsPage({ onChanged }) {
  const [message, setMessage] = useState(null);

  const [username, setUsername] = useState("");
  const [avatarKey, setAvatarKey] = useState(null);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [profileStatus, setProfileStatus] = useState(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordStatus, setPasswordStatus] = useState(null);

  useEffect(() => {
    getStats().then((stats) => {
      setUsername(stats.username || "");
      setAvatarKey(stats.avatar_key);
      setProfileLoaded(true);
    });
  }, []);

  async function handleSaveUsername(e) {
    e.preventDefault();
    try {
      await updateProfile({ username: username.trim() || null });
      setProfileStatus({ type: "success", message: "Username saved." });
      onChanged?.();
    } catch (err) {
      setProfileStatus({ type: "error", message: err.message });
    }
  }

  async function handleSelectAvatar(key) {
    const previous = avatarKey;
    setAvatarKey(key);
    try {
      await updateProfile({ avatar_key: key });
      onChanged?.();
    } catch (err) {
      setAvatarKey(previous);
      setProfileStatus({ type: "error", message: err.message });
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordStatus({ type: "error", message: "New passwords don't match." });
      return;
    }
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordStatus({ type: "success", message: "Password changed." });
    } catch (err) {
      setPasswordStatus({ type: "error", message: err.message });
    }
  }

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
        Settings
      </h1>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-4">
        <p className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Profile</p>

        {profileLoaded && (
          <>
            <div className="grid grid-cols-6 gap-2">
              {AVATARS.map((a) => (
                <button
                  key={a.key}
                  type="button"
                  onClick={() => handleSelectAvatar(a.key)}
                  aria-label={a.key}
                  aria-current={avatarKey === a.key ? "true" : undefined}
                  className={`rounded-2xl aspect-square flex items-center justify-center text-2xl transition active:scale-90 ${
                    avatarKey === a.key
                      ? "bg-primary/20 ring-2 ring-primary"
                      : "bg-background ring-1 ring-ink/10 hover:bg-primary-light"
                  }`}
                >
                  {a.emoji}
                </button>
              ))}
            </div>

            <form onSubmit={handleSaveUsername} className="flex gap-2">
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                maxLength={24}
                className="flex-1 min-w-0 rounded-2xl border border-primary/20 bg-background px-4 py-2.5 text-ink font-medium outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="submit"
                className="rounded-full bg-primary-light text-primary-dark font-bold px-4 py-2 text-sm shrink-0"
              >
                Save
              </button>
            </form>
            {profileStatus && (
              <p
                className={`text-sm font-semibold ${
                  profileStatus.type === "success" ? "text-primary-dark" : "text-wrong-dark"
                }`}
              >
                {profileStatus.message}
              </p>
            )}
          </>
        )}
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-3">
        <p className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">Appearance</p>
        <ThemeToggle />
      </div>

      <div className="w-full max-w-sm bg-surface rounded-3xl shadow-lg ring-1 ring-ink/10 p-6 flex flex-col gap-3">
        <p className="text-xs font-bold uppercase tracking-wide text-ink-soft/70">
          Change password
        </p>
        <form onSubmit={handleChangePassword} className="flex flex-col gap-2">
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Current password"
            autoComplete="current-password"
            className="rounded-2xl border border-primary/20 bg-background px-4 py-2.5 text-ink outline-none focus:ring-2 focus:ring-primary"
          />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password"
            autoComplete="new-password"
            className="rounded-2xl border border-primary/20 bg-background px-4 py-2.5 text-ink outline-none focus:ring-2 focus:ring-primary"
          />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            autoComplete="new-password"
            className="rounded-2xl border border-primary/20 bg-background px-4 py-2.5 text-ink outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            className="mt-1 rounded-full bg-primary-light hover:bg-primary/20 text-primary-dark font-bold py-2.5 transition"
          >
            Change password
          </button>
        </form>
        {passwordStatus && (
          <p
            className={`text-sm font-semibold ${
              passwordStatus.type === "success" ? "text-primary-dark" : "text-wrong-dark"
            }`}
          >
            {passwordStatus.message}
          </p>
        )}
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
