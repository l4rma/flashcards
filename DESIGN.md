# Flash Cards App — Design Brief

Visual direction for the frontend: calm, friendly, encouraging — a
Duolingo/chess.com feel, not clinical or corporate.

## Palette

- **Primary green**: muted sage/emerald (not neon) — used for the "Correct"
  button, primary actions, active states.
- **Background**: warm off-white/cream, not stark white.
- **Text**: dark charcoal, not pure black.
- **Wrong**: soft coral/red, used only for the "Wrong" button.
- **Cards/surfaces**: white, sitting on the cream background with a soft
  drop shadow instead of a hard border.

Suggested starting values (adjust to taste once we see it rendered):
- Primary green: `#4C9A6A` (hover/darker: `#3E8058`)
- Background: `#FAF7F0`
- Surface (card) white: `#FFFFFF`
- Text: `#2B2B26`
- Wrong/coral: `#E0665A`

## Navigation

The top nav bar has its own visual identity rather than blending into the
page background: a pale sage-green fill (`primary-light`) with a
slightly darker green bottom border (`primary`) — both colors already in
the palette above, no new ones introduced. Tabs are icon-only (no text
labels), rendered as emoji to match the app's existing icon language
(achievements/quests already use emoji badges throughout): 🏋️ Train, 📚
Deck, 📈 Progress, ⚙️ Admin. Each tab button keeps an `aria-label`/`title`
of its full name for accessibility/hover since there's no visible text.
Tab buttons are `rounded-2xl` squares (not `rounded-full` circles) —
deliberately breaking from the pill-button shape used elsewhere in the
app for this one spot, per explicit request.

## Shape language

- Large border radii throughout — cards `rounded-2xl`/`rounded-3xl`,
  buttons fully pill-shaped (`rounded-full`).
- Soft shadows (`shadow-md`/`shadow-lg`, low opacity) instead of visible
  borders wherever possible.
- Generous padding/whitespace — avoid a dense, cramped feel.

## Typography

- A rounded, friendly sans-serif: **Nunito** or **Quicksand** (Google
  Fonts) rather than a neutral system font.
- Bold, large headings; medium-weight body text.

## Layout

- Single centered column, mobile-first, max content width (~480–560px)
  even on desktop — this is a personal study app, not a dashboard.
- Train page: the flashcard dominates the screen center; grading buttons
  are fixed to the bottom of the viewport, like Duolingo's answer bar.

## Interaction

- The flashcard **flips** (simple CSS 3D flip transform) when clicked to
  reveal the English translation, rather than just swapping text.
- Buttons have a subtle press/scale animation on click.
- Micro-celebration on "Correct" is a nice-to-have for later (not MVP-blocking).

## Tech choice

- **Tailwind CSS** with a small custom theme (colors, border radius,
  font family) — fastest way to get this exact look without fighting a
  heavier component library's default style.
