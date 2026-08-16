# `methode_theme`

The Méthode brand identity for the Odoo backend. This module owns **100% of the
visual layer**; `aura_backend_theme` is reduced to theme-settings machinery and
must not style stock Odoo selectors.

See `THEME_PLAN.md` at the repo root for the full plan, the locked decisions
(D1–D3) and the traps (§9). **Read §9.2 before touching colour.**

---

## Palette

| Token | Value | Role |
|---|---|---|
| `$m-bg-primary` | `#FDFAF6` | page / app background |
| `$m-bg-secondary` | `#E9DBCA` | raised surfaces, group headers, hovers |
| `$m-text` | `#000000` | default text; also **primary**, see below |
| `$m-text-secondary` | `#6D6D6D` | labels, placeholders, muted metadata |
| `$m-accent` | `#FAA140` | accent + hover |

**Primary is black, not orange.** `02-display-title.png` is a black plate with
white text and `03-card.png`'s action affordance is a black circular button —
orange appears only inside the illustration. So `$o-brand-primary` is `$m-text`
and the accent is reserved for emphasis.

> ⚠ **`$m-accent` measures 1.97:1 against `$m-bg-primary`** — far below the
> 4.5:1 needed for text. It is a **fill** colour: borders, underlines, active
> indicators, icon chips. Never set it as a text colour on the page background.
> Where an "orange" *text* treatment is wanted, use `$m-warning`.

### Semantic colours (derived)

The brand defines no success/warning/danger, but Odoo needs them for alerts,
statusbars and validation. Odoo's stock values were drawn for a white page and
are unusable here — stock `$o-warning` (`#ffac00`) is both illegible at 1.81:1
*and* a near-twin of `$m-accent` (ΔE 19).

Derived instead at matched lightness (L\* 40–47, spread 7.6) so the four read as
one system. Each clears 4.5:1 **both** as text on `$m-bg-primary` and with white
text on top:

| Role | Value | L\* | On page | White on it | ΔE vs accent |
|---|---|---|---|---|---|
| `$m-success` | `#3E7C4F` | 47.0 | 4.80:1 | 5.00:1 | 75.5 |
| `$m-info` | `#2E6B8A` | 42.7 | 5.63:1 | 5.86:1 | 96.4 |
| `$m-warning` | `#9A6510` | 47.3 | 4.76:1 | 4.95:1 | 30.3 |
| `$m-danger` | `#B3261E` | 39.7 | 6.28:1 | 6.54:1 | 49.8 |

`$m-warning` stays in the accent's hue family — deliberate, and normal for a
warm brand — but is darkened until it separates from `$m-accent` (ΔE 30) and,
critically, from `$m-danger` (ΔE 42). Per §5.1 danger stays unambiguously red
and never borrows the orange accent.

*(These answer §14 open question 2. Supply different values if the brand owner
prefers, but keep the two contrast checks and the danger/warning separation.)*

---

## Typography — Nunito

Vendored at `static/lib/nunito/`, never a Google Fonts CDN link: backend assets
must work offline and behind a CSP.

**One variable file, not three static cuts.** Nunito ships with a single `wght`
axis spanning 200–1000, so 400/600/700 all come from the same 98 KB woff2 —
smaller than three static weights, with every intermediate weight free. Do not
add per-weight `@font-face` blocks; each would re-download the same file.

The font is licensed **SIL OFL 1.1** (`static/lib/nunito/OFL.txt`).

> The brand asset `02-display-title.png` was verified to be **Nunito 700** by
> rendering its own string in both candidate faces and comparing letterforms.
> **Outfit is not used in the backend** — despite
> `methode_demo_tour/static/src/scss/brand.scss` naming it as the title face,
> that is the *marketing* typeface and stays scoped to that module.

### How the font reaches the UI

Through Bootstrap's cascade, **not** through override rules:

```
$o-system-fonts                        ← set in brand_variables.scss
  └→ $o-font-family-sans-serif         (web primary_variables.scss:114)
       └→ $font-family-sans-serif      (web bootstrap_overridden.scss:117)
            └→ Bootstrap body + every component
```

`$o-headings-font-family` is overridden separately because Odoo hardcodes a
`"SF Pro Display"` prefix into it — left alone, **every heading resolves to SF
Pro Display on macOS** and silently ignores Nunito.

`$o-font-weight-medium` is raised 500 → 600 because Bootstrap maps
`$font-weight-bold` onto it, and Nunito's 500 reads weak.

**Consequence for contributors:** there is no `body { font-family: … }` rule and
no `h1`–`h6` size scale in this module. If you find yourself adding one, you are
re-implementing what a variable already does — and only for the selectors you
remembered to list. Set the variable instead.

---

## Material language — measured, not guessed

The brand assets are **2× exports**, so these are the halved, CSS-ready values.

| Element | Radius | Border | Shadow | Surface |
|---|---|---|---|---|
| Primary button (01) | 10.5px | 1px `#898989` | `0 5px 0` `#000` | `#FFFFFF` |
| Display plate (02) | 12.5px | — | offset *outline*, 4px down | `#000000` |
| Card (03) | 34.5px | 1px `#191A22` | `0 5px 0` `#000` | `#F2F2F2` |
| Input (04) | 12px | 1px `#191A22` | none | `#FFFFFF` |

Three rules follow, and getting them right is most of the brand:

1. **Blur is zero — literally.** At the button's shadow edge one pixel row is
   `#000000` and the next is `#FFFFFF`. Never add a blur radius. There is no
   `0 12px 30px` ambient shadow anywhere in this design system.
2. **The offset is straight down (`dx = 0`).** Not diagonal.
3. **Outlines are `#191A22`, fills and shadows are `#000000`.** The navy is
   softer; pure black outlines read harsh at backend density.

Corner radius is **configured, not overridden**: `$o-border-radius` (10/6/14px,
up from Odoo's 4/3/6) feeds Bootstrap's whole `$border-radius` family, so
buttons, inputs, dropdowns, alerts and modals round together.

Buttons, kanban records and `.m-card` all carry the shadow; only its scale
changes (3px at control scale, 5px on `.m-card`, the measured card value).
§8's "one elevation" means one *kind* of shadow, not one component allowed to
use it.

> ⚠ **Never style `.o_kanban_record` without
> `:not(.o_kanban_ghost):not(.o-kanban-button-new)`.** Odoo emits seven empty
> ghost divs to space the last row; a border or background turns each into a
> collapsed box that renders as a heavy dark line across the bottom of the view.
> Odoo guards its own rules the same way (`kanban_record.scss:31`). See §9.8.

### Buttons: raised, and pressed on hover

Every button carries the hard offset shadow and **presses down on hover** —
`translateY` of exactly the shadow offset, so the button lands where its shadow
was. That equality is what makes it read as physical; change one and you must
change the other.

> ⚠ **Shadow and press are one gesture.** Never give a button the transform
> without a visible shadow to press into — the motion reads as drift, not a
> press. This is why the shadow *colour* is a token (`--m-shadow-color`) rather
> than a constant: `.btn-primary` is black, and the default shadow is black too,
> so it overrides the token to grey `#898989` (measured from asset 01's border).
> Without that swap the shadow renders as nothing and the button appears not to
> respond to hover at all. Any new variant on a dark fill must do the same.

**The brand orange is on `.btn-info`** (aliased as `.btn-accent`), replacing
Odoo's blue. Its text **must stay black**: Odoo ships `--btn-color: #FFFFFF`,
and white on `#FAA140` is 2.05:1, far below AA — black on the same orange is
10.3:1. The orange is scoped to the *button* only; `$o-info` stays `#2E6B8A`
for alerts, badges and info text, because the accent is unreadable as text.

Odoo generates buttons through `--btn-*` custom properties (**not** `--bs-btn-*`).
Override those; setting `background-color` directly loses to
`.btn { background: var(--btn-bg) }`. Bootstrap's default pressed state,
`inset 0 3px 5px rgba(0,0,0,.125)`, is a **5px blur** and is killed globally —
it is the one place Bootstrap sneaks blur back into every button.

### Two deliberate departures from the assets

Both exist because the assets are marketing pieces and this is a dense ERP
backend. Neither is an accident:

- **Shadow scale.** The asset's button is a 60px CTA with a 5px shadow (8% of
  its height). Odoo's buttons are ~30px, where a literal 5px reads as a slab.
  `--m-shadow-hard` keeps the *ratio* at control scale (3px);
  `--m-shadow-hard-lg` is the measured 5px, for cards.
- **Input density.** The asset's inputs are 40px tall and generously padded, on
  a four-field contact form. Odoo ships `$o-input-bg: transparent` with 2px/4px
  padding because a form view carries 20–40 fields. The brand's **outline and
  radius** are adopted; Odoo's **padding** is kept. Reproducing the asset
  literally would break the 1280×800 budget in §8.

## File layout

| File | Bundle | Contents |
|---|---|---|
| `scss/brand_variables.scss` | `web._assets_primary_variables` | SCSS vars only — palette, semantics, font stack |
| `scss/css_tokens.scss` | `web.assets_backend` | `:root` `--m-*` custom properties, bridged to `--tbt-*` |
| `scss/typography.scss` | `web.assets_backend` | `@font-face` + rules Bootstrap exposes no variable for |

The two bundles **cannot see each other**, so the palette is restated in both.
That duplication is intentional; keep them in lockstep.

Asset order in `web.assets_backend` is load-bearing: tokens → typography →
components → views → fixes.

---

## Rules for anything added here

- **Configure, don't override.** Prefer setting an Odoo/Bootstrap SCSS variable
  over writing a rule. §0.1 of the plan documents where the opposite habit led.
- **Consume `--tbt-*`, never fight it.** `theme_bootstrap.js` writes ~40 custom
  properties as *inline styles on `<html>`*, which beat every stylesheet rule at
  the same name. Read `var(--tbt-content-bg-dynamic, #FDFAF6)`. Do **not** try
  to out-`!important` it — that breaks D3.
- **4px vertical rhythm.** Every padding/margin is a `--m-space-*` multiple. No
  `0.82rem`, no `0.28rem 0.9rem`.
- **One elevation.** The brand's hard offset shadow, zero blur
  (`--m-shadow-hard`). No `0 12px 30px` ambient blur anywhere.
- **`!important` budget: under 30 for the whole module** (Aura has ~900). Each
  one needs a one-line comment justifying it. If you need it to win, you are
  fighting a rule that should have been deleted.
- **Size budget: ~1,500–2,000 lines total.** Past that, styling is being
  re-implemented rather than adjusted — stop and reassess.
