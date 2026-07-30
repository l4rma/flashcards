// Applies (or clears) an equipped color/font theme from the Collection
// system (see backend/app/collection.py's ThemeDef) as inline CSS custom
// properties on <html>. Deliberately inline styles, not a class — inline
// styles win the cascade over both the light default `@theme` values and
// the `html.dark { --color-primary: ...; }` override block (see
// index.css).
//
// Each theme ships *two* color sets (`colors`/`colors_dark`), not one
// shared triple — a WCAG AA audit (see index.css's dark-theme comment)
// found a single set failing badly once dark mode put a light-mode-tuned
// `primary-dark` text color against a dark surface (as low as 1.33:1 for
// Midnight). `themeColorsForCurrentMode` below picks whichever set
// matches the current light/dark toggle, and a MutationObserver re-runs
// it automatically whenever that toggle changes — without this, toggling
// dark mode while a theme was equipped would leave the wrong variant's
// colors applied until the next full page load.
const PROPERTIES = ["primary", "primary-dark", "primary-light"];

export function isDarkMode() {
  return document.documentElement.classList.contains("dark");
}

export function themeColorsForCurrentMode(theme) {
  if (!theme) return null;
  return isDarkMode() ? theme.colors_dark : theme.colors;
}

let currentTheme = null;

function apply() {
  const root = document.documentElement.style;
  if (!currentTheme) {
    for (const prop of PROPERTIES) root.removeProperty(`--color-${prop}`);
    root.removeProperty("--font-display");
    return;
  }
  const colors = themeColorsForCurrentMode(currentTheme);
  for (const prop of PROPERTIES) {
    const value = colors[prop];
    if (value) root.setProperty(`--color-${prop}`, value);
  }
  if (currentTheme.font_display) {
    root.setProperty("--font-display", currentTheme.font_display);
  } else {
    root.removeProperty("--font-display");
  }
}

export function applyCollectionTheme(theme) {
  currentTheme = theme;
  apply();
}

new MutationObserver(() => apply()).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["class"],
});
