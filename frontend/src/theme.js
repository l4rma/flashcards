// Light/dark/system theme preference — persisted in localStorage (unlike
// the auth token in sessionStorage, this should survive across browser
// sessions, not just the current tab). "system" (the default for a new
// visitor) follows prefers-color-scheme and stays live if the OS theme
// changes while the app is open; "light"/"dark" are explicit overrides.
const KEY = "flashcards_theme";

function prefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function getThemePreference() {
  return localStorage.getItem(KEY) || "system";
}

export function resolveTheme(preference) {
  return preference === "system" ? (prefersDark() ? "dark" : "light") : preference;
}

export function applyTheme(preference) {
  document.documentElement.classList.toggle("dark", resolveTheme(preference) === "dark");
}

export function setThemePreference(preference) {
  localStorage.setItem(KEY, preference);
  applyTheme(preference);
}

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (getThemePreference() === "system") applyTheme("system");
});
