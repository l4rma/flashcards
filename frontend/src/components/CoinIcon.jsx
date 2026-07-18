// Custom coin glyph — the app's own artwork instead of the 🪙 emoji, which
// different OS emoji fonts draw very differently (a detailed gold coin on
// some platforms, a flat grey disc on others). This renders identically
// everywhere. The center rule line echoes the same "ruled index card"
// detail used on the flip card and deck rows, tying it into the app's
// one running material motif rather than being a generic coin clip-art.
export default function CoinIcon({ className = "w-5 h-5" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" fill="var(--color-coin)" stroke="var(--color-coin-dark)" strokeWidth="1.25" />
      <circle
        cx="12"
        cy="12"
        r="6.75"
        fill="none"
        stroke="var(--color-coin-dark)"
        strokeWidth="1"
        opacity="0.55"
      />
      <line
        x1="8.25"
        y1="12"
        x2="15.75"
        y2="12"
        stroke="var(--color-coin-dark)"
        strokeWidth="1.25"
        strokeLinecap="round"
        opacity="0.85"
      />
    </svg>
  );
}
