# AIdeator Design System — Implementation Source of Truth

Local design spec for engineers, designers, and Cursor. This file mirrors Notion and should be treated as canonical for PH‑A/PH‑B UI.

---

## 1. Project and Audience Summary

AIdeator is a **local-first idea validation engine** that turns a startup idea into an investor‑grade, privacy‑safe report with four core cards:

- Demand
- Competition
- Risk
- Next Steps

plus a deep markdown artifact (`docs/idea-{id}.md`).

Primary audiences:

- **Indie founders / solo builders** – want to de‑risk ideas before committing time.
- **Product teams** – want a consistent way to evaluate new bets.
- **Investors/advisors** – want a structured way to sanity‑check pitches.

Primary users of this document:

- **Engineers** implementing UI and theming.
- **Designers** creating visuals and components.
- **Technical writers** aligning docs with product behavior.
- **Cursor sessions** that need design context without chat backscroll.

---

## 2. Brand Identity and Tone (design-identity)

### 2.1 Positioning

> AIdeator is a **local-first idea validation engine** that gives founders and teams investor‑grade, privacy‑safe market signals and reports they can actually trust.

### 2.2 Brand personality

**Core adjectives**

- Analytical
- Precise
- Private
- Authoritative
- Composed

**Anti‑adjectives (avoid)**

- Hype
- Noisy
- Cute

### 2.3 Voice & messaging

- Tone: calm, expert, slightly formal; “staff‑engineer explaining a system”.
- Person: sparing “we”, clear “you” when giving guidance.
- Style:
  - Short/medium sentences.
  - Explain how and why, including constraints.
  - Lean on words like signals, invariants, tests, modes, traceability.

**Do**

- “Run a local‑only validation — no idea text leaves your machine.”
- “See where your risk score came from: underlying signals, citations, and tests.”
- “You control which modes call external APIs and when.”

**Don’t**

- “Become a unicorn in 20 seconds.”
- “Our bot loves your idea.”
- Vague “best, smartest, most powerful” claims without context.

### 2.4 Visual identity

- **Primary logo (recommended):** Signal Grid Monogram
  - Abstract **A** constructed from 3–4 vertical bars and one diagonal crossbar.
  - Represents structured signals → synthesis.
  - Works from favicon to print.

- **Fallback logo concept (secondary, not primary):** Local Shield
  - Simple shield + internal node/circuit lines forming an A path.
  - Emphasizes local‑first privacy and trust boundary.

**Logo usage constraints**

- Clearspace:
  - Minimum 0.5 × symbol width around the full lockup.
- Minimum size:
  - Full lockup: ≥120 px wide (desktop), ≥96 px (mobile).
  - Symbol only: ≥16 px favicon, ≥24 px in UI.
- Monochrome:
  - Use all‑black on light, all‑white on dark.
  - No gradients or dual‑tone in pure mono contexts.
- Backgrounds:
  - Solid brand colors (`color-bg`, `color-surface`, `color-bg-light`, `color-surface-light`).
  - Avoid busy photography and high‑contrast gradients.

---

## 3. Token System (tokens)

**All values must be implemented via tokens, not hardcoded.**

### 3.1 Colors

**Core**

```text
color-bg           = #080B10   // App background
color-surface      = #0F141C   // Cards, panels
color-border       = #232A35
color-text         = #F5F7FA
color-text-muted   = #9BA4B5

color-primary      = #4A7DFF
color-primary-soft = #2F4F99
color-accent       = #D9A441   // Muted gold accent

color-chip-local   = #3F9F6C
color-chip-hybrid  = #D98C2B
color-chip-cloud   = #9B59FF
```

**Semantic**

```text
color-success = #3FBF7F
color-warning = #E3A63A
color-danger  = #FF5C5C
color-info    = color-primary
```

**Light-shell (for docs/markdown)**

```text
color-bg-light       = #F5F7FA
color-surface-light  = #FFFFFF
color-text-light     = #111319
color-border-light   = #D4D8E0
```

### 3.2 Typography

**Families**

```text
font-family-sans = "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
font-family-mono = "JetBrains Mono", "Roboto Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace
```

**Styles (desktop baseline)**

```text
font-h1      = 40px / 1.1
font-h2      = 28px / 1.2
font-h3      = 20px / 1.25
font-body    = 16px / 1.6
font-caption = 13px / 1.4
font-mono    = 13px / 1.5
```

Guidelines:

- H1 only once per page.
- H2 for major sections, H3 for card titles.
- Use mono for IDs (`FR-001`, `TC-U-010`), error codes, and code snippets.

### 3.3 Spacing (4px grid)

```text
space-xxs  = 4px
space-xs   = 8px
space-sm   = 12px
space-md   = 16px
space-lg   = 24px
space-xl   = 32px
space-xxl  = 48px
```

### 3.4 Shadows

```text
shadow-none     = none
shadow-soft     = 0 6px 18px rgba(0,0,0,0.32)   // Cards, dropdowns
shadow-elevated = 0 16px 32px rgba(0,0,0,0.48)  // Modals, sticky nav
shadow-focus    = 0 0 0 1px color-primary,
                  0 0 0 6px rgba(74,125,255,0.25)
```

### 3.5 Motion

Durations:

```text
motion-fast   = 120–160ms
motion-normal = 200–250ms
motion-slow   = 300–350ms
```

Easing:

```text
ease-standard = cubic-bezier(0.2, 0.0, 0.2, 1.0)
ease-decel    = cubic-bezier(0.0, 0.0, 0.2, 1.0)
ease-accel    = cubic-bezier(0.4, 0.0, 1.0, 1.0)
```

### 3.6 Gradients (modern polish)

```text
grad-hero   = linear-gradient(135deg, #080B10, #101930, rgba(74,125,255,0.1))
grad-cta    = linear-gradient(90deg, #4A7DFF, #6C8FFF)
grad-signal = radial-gradient(circle at 30% 0%, rgba(217,164,65,0.18), transparent 60%),
              linear-gradient(135deg, #101930, #1C2436)
```

Usage:

- `grad-hero`: landing hero background wash only.
- `grad-cta`: primary button hover/active.
- `grad-signal`: occasional highlight panel (signals or cards).

---

## 4. Component and State System (components)

### 4.1 Buttons

**Variants**

- `primary`: main actions (Run validation, New idea).
- `secondary`: secondary actions (View report).
- `ghost`: text/outline-only, low emphasis.
- `destructive`: for delete/irreversible.

**Sizes**

- `sm`, `md` (default), `lg`.

**States**

| State    | Behavior / Tokens                                      |
|----------|--------------------------------------------------------|
| default  | bg: `color-primary` (primary), text: `color-text`; radius 8px; `shadow-soft` |
| hover    | bg: `grad-cta`, scale 1.02, `motion-fast` + `ease-standard` |
| focus    | add `shadow-focus`, no layout shift                    |
| active   | scale 0.98 briefly, darker primary, `motion-fast`      |
| disabled | bg: `color-border`, text: `color-text-muted`, no pointer |
| loading  | spinner replaces icon, width fixed, text visible       |

Secondary / ghost follow same state logic but with outline/transparent styles.

### 4.2 Inputs

Types:

- Text input
- Textarea
- Select/dropdown
- Toggle
- Checkbox

States:

| State    | Behavior / Tokens                                      |
|----------|--------------------------------------------------------|
| default  | border: `color-border`, bg: `color-bg`, text: `color-text` |
| hover    | border: slightly lighter `color-border`                |
| focus    | border: `color-primary`, `shadow-focus`, `motion-fast` |
| disabled | bg: `color-surface`, text: `color-text-muted`, no pointer |
| error    | border: `color-danger`, helper text in `color-danger`  |
| success  | optional border: `color-success` (subtle)              |

### 4.3 Cards

Types:

- Idea card
- Run card
- Report card
- Metric card

Variants:

- `compact` (list) → minimal info.
- `detailed` (detail page) → full info.

States:

| State     | Behavior / Tokens                                      |
|-----------|--------------------------------------------------------|
| default   | bg: `color-surface`, border: `color-border`, `shadow-soft` |
| hover     | border: `color-primary-soft`, `motion-normal`          |
| focus     | `shadow-focus`                                         |
| selected  | left border: `color-primary`; or top border for horizontal layout |
| error     | small red indicator and message; card bg remains `color-surface` |

### 4.4 Tables

- Use for Ideas, Runs, Signals.

States:

- `loading`: skeleton rows (matching row height).
- `empty`: dedicated empty state row/card (“No runs yet; create your first run.”).
- `error`: page-level banner above table + stale data if safe, otherwise skeleton + error.
- `row-hover`: bg slightly lighter than `color-surface`.
- `row-selected`: left border `color-primary`.

Pagination:

- Controls at top-right (Prev/Next or numbered).
- Header row sticky on scroll.

Mobile:

- Collapse rows into stacked cards:
  - Each “row” becomes a card with labels and values.

### 4.5 Alerts

Types:

- `info`, `success`, `warning`, `error`.

Visual:

- Left 3–4 px color bar (info/success/warning/danger).
- Optional icon.
- Body text uses `font-body` or `font-caption`.

Behavior:

- Inline (within forms/sections).
- Or toast (top-right stack) for background events.

### 4.6 Modals

Types:

- Confirm (destructive, run with external mode).
- Info (first-run explanation, etc).

Behavior:

- Backdrop: semi‑transparent, blur optional.
- Content: `color-surface`, `shadow-elevated`, consistent padding (`space-xl`).
- Close: Esc and explicit close button (icon top-right).

States:

- `open`, `loading` (e.g., on confirmation), `success`, `error`.

---

## 5. Screen and Flow Specs (screen-specs)

### 5.1 Navigation architecture

**Top bar**

- Left: logo (Signal Grid + wordmark).
- Middle: primary nav links:
  - Dashboard
  - Ideas
  - Runs
  - Reports
  - Docs
- Right: mode pill (Local-only / Hybrid / Cloud-enabled), profile/settings icon, optional theme toggle.

**Sidebar (desktop)**

- Narrow rail with icons and tooltips for:
  - Dashboard
  - Ideas
  - Runs
  - Reports
  - Docs
  - Settings

**Mobile**

- Top bar: logo, title, overflow menu.
- Bottom tab bar: Dashboard, Ideas, Runs, Settings.

### 5.2 Key screens

**Landing**

Sections in order:

1. Hero (value prop + CTA + mode pills + report mock).
2. How it works (3 steps).
3. Why local-first & trustworthy (privacy + rigor).
4. Report deep‑dive (cards + markdown preview).
5. Use cases.
6. Methodology & limits.
7. Pricing / access.
8. Final CTA band.
9. Footer (links/legal).

**Dashboard**

- Summary cards:
  - “Ideas” (count, new idea CTA).
  - “Runs” (recent status summary).
  - “Last run” mini card with quick link to report.
- Mode indicator area: current default mode with quick switch (where safe).

**Ideas**

- **List**:
  - Table: Idea name, created date, runs count, last run status, actions.
  - Empty state: “Create your first idea.”
- **Detail**:
  - Idea metadata (title, description, tags).
  - New run form (mode, tier).
  - Run history table/cards.

**Runs**

- **List**:
  - Table: Idea, status pill, mode, tier, started, duration, actions.
- **Detail**:
  - Status timeline (pending → running → succeeded/failed).
  - Cards: Demand, Competition, Risk, Next Steps.
  - Links to signals, docs artifact.
  - Error block if failed (code + human message).

**Reports viewer**

- Side list of ideas/reports; main panel shows markdown rendered from `docs/idea-{id}.md`.
- Light-shell theme (`color-bg-light`/`color-surface-light`).

**Settings**

- Modes default and restrictions.
- API keys / external deps.
- Logging/telemetry switches (where user is allowed to see).

---

## 6. Motion and Polish Rules (landing-page-blueprint+modern-polish)

### 6.1 Gradient strategy

- Use gradients only in:
  - Landing hero (`grad-hero`).
  - Primary CTA hover (`grad-cta`).
  - Occasional highlight panel (`grad-signal`).
- App interior (dashboard, runs, etc.) stays mostly flat with solid backgrounds.

### 6.2 Depth strategy

- Cards, dropdowns: `shadow-soft`.
- Modals, sticky nav: `shadow-elevated`.
- Focus: `shadow-focus` for all interactive elements.
- Optional nav blur using `backdrop-filter` on landing only; avoid deep glassmorphism layers.

### 6.3 Motion language

- All animations use the timing/easing tokens.
- Typical patterns:
  - Hover/press: `motion-fast` + `ease-standard`.
  - Modal/Toast: `motion-slow` + `ease-decel` on enter, `ease-accel` on exit.
  - Section entrance (landing): subtle fade + slight upward move.

### 6.4 Key micro-interactions

- **Buttons**:
  - Hover: gradient, scale 1.02.
  - Active: scale 0.98 then snap back.
- **Form validation**:
  - Error messages fade/slide up small distance; no shake animations.
- **Nav**:
  - Active indicator slides with `motion-normal`, `ease-standard`.
- **Run success**:
  - Toast slide in; card statuses update smoothly without big motion.

### 6.5 Signature brand moment

- On first successful report view per idea:
  - Background grid line animates behind cards.
  - Cards fade/slide in sequence (Demand → Competition → Risk → Next Steps).
  - Scores animate from 0 → final over ~600 ms.
- Interaction is not blocked; user can still click and scroll.

### 6.6 Reduced-motion behavior

When `prefers-reduced-motion: reduce`:

- Disable grid sweep and score counting:
  - Cards appear fully rendered instantly.
- Remove section and hero scroll animations:
  - Content simply appears.
- Maintain focus and feedback; you only remove motion, not state cues.

---

## 7. Accessibility and Responsive Behavior (a11y-checklist)

### 7.1 General accessibility

- Follow WCAG 2.1 AA:
  - Ensure text vs background contrast meets AA.
- Keyboard:
  - All interactive elements reachable via Tab/Shift+Tab.
  - Space/Enter activate buttons and clickable cards.
- Focus:
  - Use `shadow-focus` for visible focus on all interactive components.

### 7.2 ARIA and roles

- Buttons:
  - Icon-only buttons must have `aria-label`.
- Alerts:
  - Use `role="alert"` for important, immediate errors.
- Modals:
  - `role="dialog"`, `aria-modal="true"`, labelled via `aria-labelledby`.
- Tables:
  - `<th scope="col">` for headers; use proper table semantics.
- Inputs:
  - Labels use `for`/`id`; error messages referenced via `aria-describedby`.

### 7.3 Responsive behavior

**Breakpoints (suggested)**

```text
sm: < 640px
md: 640–1023px
lg: ≥ 1024px
```

Behavior:

- Multi-column layouts → stacked sections at `sm`.
- Tables → card lists at `sm`:
  - Each row becomes a card with label/value pairs.
- Padding reduces one token on mobile:
  - Section: `space-xxl` → `space-xl`.
- Type scales down one step for H1/H2 on small screens.

---

## 8. Developer Implementation Notes

- **Source of truth**:
  - This file and the token tables are canonical.
  - Do not introduce new colors or ad‑hoc styles without updating this doc.

- **Token implementation**:
  - Export tokens (colors, type, spacing, shadows, motion, gradients) into JSON/TS.
  - Map tokens to CSS variables or theme objects.
  - Only refer to tokens (e.g., `var(--color-primary)`), not raw hex.

- **Component library**:
  - Implement base components (Button, Input, Card, Table, Alert, Modal, Nav) with props that map directly to variants and states described above.
  - Keep business logic out; composition over config when possible.

- **Theming**:
  - Implement dark app theme and light docs theme from same token set.
  - Support future theming by staying semantically named (no `blue-500` style references).

- **Motion**:
  - Centralize animation durations/easings.
  - Wrap major animations with `prefers-reduced-motion` checks and provide instant fallback paths.

- **Iconography**:
  - Choose a base icon set (e.g., Phosphor, Lucide) plus custom brand icons (logo, mode icons).
  - Respect line thickness and color usage (primary/Muted only).

---

## 9. QA Checklist and Known Risks (qa-checklist)

### 9.1 QA checklist

**Tokens**

- [ ] All colors are used via tokens (`color-*`) with no stray hex codes.
- [ ] Typography uses tokenized styles (`font-*`).
- [ ] Spacing uses `space-*` tokens.
- [ ] Shadows and motion use `shadow-*`, `motion-*`, and `ease-*` tokens.

**Components**

- [ ] Buttons support default/hover/focus/active/disabled/loading.
- [ ] Inputs support default/hover/focus/disabled/error/success.
- [ ] Cards show hover/focus/selected/error semantics correctly.
- [ ] Tables implement loading, empty, error, row-hover, row-selected.
- [ ] Alerts show proper variant colors and are dismissible where expected.
- [ ] Modals trap focus, close on Esc, and are labelled correctly.

**Accessibility**

- [ ] All interactive elements have a visible focus state.
- [ ] Keyboard navigation works across all main flows.
- [ ] Contrast passes AA on all text.
- [ ] `prefers-reduced-motion` honored (no major motion when enabled).
- [ ] ARIA roles/labels implemented for modals, alerts, icon buttons.

**Responsiveness**

- [ ] No horizontal scroll at `sm` and `md`.
- [ ] Layout transitions at `sm`, `md`, `lg` are as specified.
- [ ] Tables degrade to card lists at `sm`.
- [ ] CTA buttons and tap targets meet minimum touch sizes.

**Brand**

- [ ] Only approved logo and color palette used.
- [ ] No mascot illustrations or off-brand gradients.
- [ ] Signature brand moment appears only on first report view and is skippable.

**Motion**

- [ ] Animation timings and easings match tokens.
- [ ] No long blocking animations; UI remains responsive.

### 9.2 Known risks

- Drift between this file and implemented tokens/components if changes are made ad‑hoc.
- Overuse of gradient and motion by future contributors; guard with code review + lint rules.
- Ambiguities:
  - Mobile table layout (card vs scroll) – should be documented explicitly in implementation.
  - Icon set choice – must be standardized.
  - Exact breakpoints – should be locked in CSS/theme and referenced here.

---