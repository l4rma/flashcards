# Flash Cards App — Design Brief

Visual direction for the frontend: calm, friendly, encouraging — a
Duolingo/chess.com feel, not clinical or corporate. Redesigned mid-2026
(bottom nav + type pairing + "index card" motif), then followed shortly
after by a togglable dark theme and a custom coin icon — keeping this
same mood throughout but executing it with more intention — see each
section below for what changed and why.

## Signature element: the index card

The app's one recurring material motif is the physical flash card itself
— a small punch-hole circle (top-left of every card-shaped surface: the
flip card, each row in the deck list) plus a serif word label with a thin
rule underneath, like a printed index card. This isn't just decoration: on
the Train page, 1-2 receding card edges peek out behind the active
`FlipCard` (`stackDepth` prop, capped at 2), giving a second, glanceable
read of how many cards are left today that echoes the "N left today" text
above it — structure encoding real information, not just visual noise.
The deck list (`DeckPage`) extends the same idea: each row gets a tiny,
stable (id-hashed, not random — doesn't jitter on re-render) tilt of
±0.6°, reading as a loose stack rather than a rigid table.

## Typography

Two faces, deliberately paired for contrast rather than one font doing
everything:
- **Fraunces** (`font-display`, variable, soft optical-size axis) — the
  "printed label" voice: the vocabulary word on both flip-card faces, page
  H1s, stat numbers (streak/coins/cards/accuracy), modal titles. Chosen
  over a high-contrast editorial serif (Playfair-style) specifically to
  avoid reading as an AI-template default paired with this cream
  background — Fraunces' soft axis is warmer/rounder, closer to a stamped
  label than an editorial headline.
- **Nunito** (`font-sans`) — the everyday UI voice: buttons, nav, form
  labels, captions, body copy. Unchanged from the original brief; kept
  because it already worked as a friendly rounded sans, the pairing is
  what needed to change, not this face itself.

## Palette

Unchanged from the original brief — the redesign's brief was "same mood,
executed better," not a palette replacement:
- Primary green: `#4C9A6A` (hover/darker: `#3E8058`)
- Background: `#FAF7F0`
- Surface (card) white: `#FFFFFF`
- Text: `#2B2B26` / soft: `#6B665C`
- Wrong/coral: `#E0665A` (darker: `#C24F44`)
- Progress purple (daily quests / achievement progress bars, kept
  deliberately distinct from primary green so "goal progress" reads as its
  own category, not the same thing as "Correct"): `#8A63D2`, track
  `#ECE5F9`
- Coin gold (`components/CoinIcon.jsx`, replacing the 🪙 emoji — see Dark
  theme section for why a custom SVG at all): `#E8B84B`, rim/detail
  `#C6932B`

## Dark theme

Togglable (Light / Auto / Dark, `components/ThemeToggle.jsx` on the Admin
page), persisted in `localStorage` and defaulting to "Auto" (follows
`prefers-color-scheme`, stays live if the OS theme changes mid-session).
A tiny inline script in `index.html` applies the `dark` class to `<html>`
synchronously before first paint, so there's no flash-of-wrong-theme on
load — `theme.js` duplicates a couple of its lines for exactly this reason
(it has to run before any module import is possible).

**Every color in the app already flows through the named tokens above**
(`bg-primary`, `text-ink`, etc.), so dark mode is implemented as a single
`html.dark { --color-background: ...; ... }` block in `index.css`
overriding those same custom properties — zero `dark:` variants sprinkled
through component files, zero per-component color logic. This works
because Tailwind v4 compiles `@theme` into a *layered* `:root`/`:host`
rule, and unlayered CSS (our plain `html.dark` block) always wins over any
layered rule in the cascade regardless of selector specificity.

Chosen as a warm "studying by lamplight" dark (near-black `#1E1B17`
background, warm dark-taupe `#29241E` surfaces) rather than a cold
blue-black tech dark mode, to stay consistent with the light theme's warm
cream identity rather than reading as a generic inverted palette. Several
tokens deliberately swap which *end* of light/dark they resolve to, not
just invert uniformly: the `-dark` variants (`primary-dark`, `wrong-dark`)
are used far more often as text sitting on a tinted surface (Edit/Delete
pills, ghost buttons, modal captions) than as a button hover-darken, and
text needs to get *lighter* against a dark surface to stay legible — so in
dark mode these resolve lighter than their base color, accepting that the
minority hover-darken usages lighten on hover instead, which reads fine.

**Plain `shadow-md`/`shadow-lg` alone stopped being enough for card
edges once the background went dark** — Tailwind's default shadow color
is a fixed near-black, which is nearly invisible against an
already-dark surface (confirmed by screenshot: the Admin danger-zone card,
which already had a `ring`, read with a clear boundary in dark mode while
every plain `bg-surface` card didn't). Fixed by adding `ring-1
ring-ink/10` to every surface card — since `ink` itself flips between dark
(light mode, a barely-visible dark hairline on white) and light (dark
mode, a visible light hairline on dark), one ring utility gives the
correct subtle boundary in both themes with no dark-mode-specific classes
needed.

## Navigation

**Moved to a floating pill bar fixed to the bottom of the viewport**
(user request, thinking mobile-first) — icon-only, same emoji-badge icon
language as before (🏋️ Train, 📚 Deck, 📈 Progress, ⚙️ Admin), each with an
`aria-label`/`title` for accessibility. Deliberately kept **universal
across all viewport widths, not just mobile** — this app already commits
to a single narrow centered column even on desktop (see Layout, below),
so a bottom bar reads just as natural there as on a phone; a
breakpoint-specific switch to a top nav on wide viewports would be new
complexity this "phone-shaped app" doesn't need. A floating pill (not a
flush edge-to-edge bar) extends the existing pill-button shape language
rather than introducing a foreign shape. Content areas get bottom padding
(`pb-28` on `main`) so the fixed bar never covers the last item in a
scrolling list.

The stats header (streak/coins) moved to the top in the bar's place,
restyled as a compact stat strip using `font-display` numerals rather than
small plain text — it's real content now (today's numbers), not a caption.

## Shape language

- Large border radii throughout — cards `rounded-2xl`/`rounded-3xl`,
  buttons fully pill-shaped (`rounded-full`), nav bar itself now
  `rounded-full` too (was `rounded-2xl` squares in the old top-bar design
  — the floating pill bar's shape already matches the button language, so
  the old "break from pill shape for nav" exception no longer applies).
- Soft shadows (`shadow-md`/`shadow-lg`, low opacity) instead of visible
  borders wherever possible.
- Generous padding/whitespace — avoid a dense, cramped feel.

## Layout

- Single centered column, mobile-first, max content width (~480–560px)
  even on desktop — this is a personal study app, not a dashboard.
- Train page: the flashcard is a true hero now — the page's root fills
  available height and vertically centers the card/progress bar/buttons
  (`flex-1 justify-center`), rather than starting content from the top and
  leaving dead space below on tall viewports.
- Progress page's top-level stats (streak/coins/cards/accuracy) are one
  unified stat strip with four `font-display` numbers side by side, not
  four lines of plain text in a paragraph — the single biggest layout fix
  from the original version, which put nearly everything in a stack of
  identical white boxes with no hierarchy between them.
- Admin page originally consolidated from three separate elevated cards
  down to two (settings grouped together, danger zone kept visually
  separate via a coral-tinted surface) — three cards for four short
  buttons read as noise, not hierarchy. Back up to three since the theme
  toggle was added as its own "Appearance" card above settings — a
  deliberate exception, since a toggle is a different kind of control than
  a row of buttons and reads better with its own space, not folded into
  the settings card.

## Interaction

- The flashcard **flips** (simple CSS 3D flip transform) when clicked to
  reveal the French translation, rather than just swapping text. Unchanged
  — already a good, deliberate piece of motion; not touched.
- Buttons have a subtle press/scale animation on click. Unchanged.
- Confetti + modal on achievement/quest unlock. Unchanged — no new
  animation added on top of it; per the design skill's own restraint
  guidance, this was already the app's "spend your boldness in one place"
  moment and didn't need company.

## Tech choice

- **Tailwind CSS** with a small custom theme (colors, border radius, two
  font families) — fastest way to get this exact look without fighting a
  heavier component library's default style. No icon library or UI
  component library — emoji badges and plain Tailwind utility classes are
  still most of the toolset, matching the original brief's reasoning. The
  one exception: a couple of small hand-drawn inline SVGs (`CoinIcon`,
  `ThemeIcon`) where cross-platform emoji rendering was a real problem
  (different OS emoji fonts drew 🪙 as gold vs. flat silver) rather than
  a stylistic choice — not the start of an icon library, just a targeted
  fix where emoji genuinely couldn't do the job.
