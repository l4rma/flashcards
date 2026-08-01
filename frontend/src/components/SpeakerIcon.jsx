// Small custom speaker/pronunciation icon — plain stroke+fill shape using
// currentColor (so it follows its button's own text color/state), same
// precedent as ThemeIcon.jsx rather than an emoji (cross-platform emoji
// rendering risk, same reasoning as the coin icon).
export default function SpeakerIcon({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9v6h4l5 4V5L7 9H3z" fill="currentColor" stroke="none" />
      <path d="M16 8.5a5 5 0 0 1 0 7" />
      <path d="M18.5 6a8.5 8.5 0 0 1 0 12" />
    </svg>
  );
}
