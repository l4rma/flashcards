import { useState } from "react";
import { getThemePreference, setThemePreference } from "../theme";
import ThemeIcon from "./ThemeIcon";

const OPTIONS = [
  { key: "light", label: "Light" },
  { key: "system", label: "Auto" },
  { key: "dark", label: "Dark" },
];

export default function ThemeToggle() {
  const [preference, setPreference] = useState(getThemePreference);

  function choose(key) {
    setThemePreference(key);
    setPreference(key);
  }

  return (
    <div className="flex bg-background rounded-full p-1 gap-1">
      {OPTIONS.map(({ key, label }) => (
        <button
          key={key}
          type="button"
          onClick={() => choose(key)}
          aria-pressed={preference === key}
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-full py-2 text-sm font-bold transition active:scale-95 ${
            preference === key ? "bg-primary text-white" : "text-ink-soft hover:text-ink"
          }`}
        >
          <ThemeIcon variant={key} className="w-4 h-4" />
          {label}
        </button>
      ))}
    </div>
  );
}
