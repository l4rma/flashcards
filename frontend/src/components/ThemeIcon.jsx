// Small custom icons for the theme toggle — plain stroke/fill shapes using
// currentColor (so they follow the toggle button's own active/inactive
// text color) rather than sun/moon emoji, which would carry the same
// cross-platform rendering risk the coin icon fix addressed.
export default function ThemeIcon({ variant, className = "w-4 h-4" }) {
  if (variant === "light") {
    return (
      <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
        <circle cx="12" cy="12" r="4.5" />
        <line x1="12" y1="2.5" x2="12" y2="5" />
        <line x1="12" y1="19" x2="12" y2="21.5" />
        <line x1="2.5" y1="12" x2="5" y2="12" />
        <line x1="19" y1="12" x2="21.5" y2="12" />
        <line x1="5.1" y1="5.1" x2="6.8" y2="6.8" />
        <line x1="17.2" y1="17.2" x2="18.9" y2="18.9" />
        <line x1="5.1" y1="18.9" x2="6.8" y2="17.2" />
        <line x1="17.2" y1="6.8" x2="18.9" y2="5.1" />
      </svg>
    );
  }
  if (variant === "dark") {
    return (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
      </svg>
    );
  }
  // "system" — a disc split evenly into a filled and an outlined half.
  return (
    <svg viewBox="0 0 24 24" className={className}>
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.75" />
      <path d="M12 3a9 9 0 0 1 0 18Z" fill="currentColor" />
    </svg>
  );
}
