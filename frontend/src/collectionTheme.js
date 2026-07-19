// Applies (or clears) an equipped color/font theme from the Collection
// system (see backend/app/collection.py's ThemeDef) as inline CSS custom
// properties on <html>. Deliberately inline styles, not a class — inline
// styles win the cascade over both the light default `@theme` values and
// the `html.dark { --color-primary: ...; }` override block (see
// index.css), so an equipped theme's accent color reads the same in
// light and dark mode; only the neutral background/surface/ink tokens
// (untouched by any theme here) keep responding to the dark toggle.
const PROPERTIES = ["primary", "primary-dark", "primary-light"];

export function applyCollectionTheme(theme) {
  const root = document.documentElement.style;
  if (!theme) {
    for (const prop of PROPERTIES) root.removeProperty(`--color-${prop}`);
    root.removeProperty("--font-display");
    return;
  }
  for (const prop of PROPERTIES) {
    const value = theme.colors[prop];
    if (value) root.setProperty(`--color-${prop}`, value);
  }
  if (theme.font_display) {
    root.setProperty("--font-display", theme.font_display);
  } else {
    root.removeProperty("--font-display");
  }
}
