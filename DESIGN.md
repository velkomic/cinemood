---
"name": "CineMood"
"description": "A cinematic screening lounge for choosing a film."
"colors":
  "ground": "#0b1020"
  "surface": "#141e35"
  "surface-raised": "#1d2b49"
  "ink": "#f1f4ff"
  "muted": "#b4c1dc"
  "accent": "#759dff"
  "accent-hover": "#a2bcff"
  "line": "#34415d"
  "warning": "#f5d49a"
  "warning-bg": "#302a23"
  "secondary-hover": "#2d416b"
  "poster-ground": "#080c17"
  "explanation": "#c4cee3"
  "save-bg": "#22375f"
  "save-ink": "#e0e9ff"
  "save-hover": "#304d80"
"typography":
  "headline":
    "fontFamily": "Manrope, sans-serif"
    "fontSize": "25px"
    "fontWeight": 700
    "lineHeight": 1.3
    "letterSpacing": "-.025em"
  "section-title":
    "fontFamily": "Manrope, sans-serif"
    "fontSize": "19px"
    "fontWeight": 700
    "lineHeight": 1.3
    "letterSpacing": "-.025em"
  "film-title":
    "fontFamily": "Manrope, sans-serif"
    "fontSize": "17px"
    "fontWeight": 700
    "lineHeight": 1.3
    "letterSpacing": "-.025em"
  "body":
    "fontFamily": "DM Sans, sans-serif"
    "fontSize": "16px"
    "fontWeight": 400
    "lineHeight": 1.6
  "explanation":
    "fontFamily": "DM Sans, sans-serif"
    "fontSize": "14px"
    "fontWeight": 400
    "lineHeight": 1.5
  "facts":
    "fontFamily": "DM Sans, sans-serif"
    "fontSize": "12px"
    "fontWeight": 400
    "lineHeight": 1.6
  "brand":
    "fontFamily": "Manrope, sans-serif"
    "fontSize": "23px"
    "fontWeight": 800
    "letterSpacing": "-.035em"
  "request":
    "fontFamily": "DM Sans, sans-serif"
    "fontSize": "17px"
    "fontWeight": 400
    "lineHeight": 1.5
"rounded":
  "mark": "3px"
  "save": "8px"
  "control": "8px"
  "surface": "12px"
"spacing":
  "6": "6px"
  "8": "8px"
  "12": "12px"
  "16": "16px"
  "18": "18px"
  "20": "20px"
  "22": "22px"
  "24": "24px"
  "28": "28px"
  "32": "32px"
  "36": "36px"
  "40": "40px"
"components":
  "button-primary":
    "backgroundColor": "{colors.accent}"
    "textColor": "{colors.ground}"
    "rounded": "{rounded.control}"
    "padding": "12px 22px"
  "button-primary-hover":
    "backgroundColor": "{colors.accent-hover}"
  "button-secondary":
    "backgroundColor": "{colors.surface-raised}"
    "textColor": "{colors.ink}"
    "rounded": "{rounded.control}"
    "padding": "12px 22px"
  "button-secondary-hover":
    "backgroundColor": "{colors.secondary-hover}"
  "button-text":
    "backgroundColor": "transparent"
    "textColor": "{colors.muted}"
    "padding": "7px 9px"
  "button-save":
    "backgroundColor": "{colors.save-bg}"
    "textColor": "{colors.save-ink}"
    "rounded": "{rounded.save}"
    "padding": "7px 12px"
  "button-save-hover":
    "backgroundColor": "{colors.save-hover}"
  "request-band":
    "backgroundColor": "{colors.surface}"
    "rounded": "{rounded.surface}"
    "padding": "10px 16px"
  "inline-details":
    "backgroundColor": "transparent"
    "textColor": "{colors.ink}"
    "padding": "12px 0 0"
  "warning":
    "backgroundColor": "{colors.warning-bg}"
    "textColor": "{colors.warning}"
    "rounded": "{rounded.control}"
    "padding": "12px 16px"
---

# Design System: CineMood

## Overview

**Creative North Star: "Screening lounge refined"**

An evening screening lounge: blue-black ground, tinted navy functional surfaces and periwinkle actions leave film imagery in charge. Manrope gives the identity and film titles their rounded character; DM Sans keeps requests, facts and explanations direct and readable.

The interface is spacious across the desktop width while keeping controls compact. Film entries stay open on the ground; stronger surface color belongs to request entry, actions and on-demand details. The same film vocabulary carries through Discover and My collection.

**Key Characteristics:**
- Poster-led, open film comparison.
- Compact functional surfaces with restrained rounding.
- Readable cool text and a deliberate periwinkle action accent.
- Ambient catalog motion that stops on interaction.

## Colors

Cool blue-black and navy provide the room; periwinkle identifies interaction while catalog posters supply varied color. Token values in the frontmatter are authoritative.

### Primary

- **Periwinkle** (`accent`): primary actions, the lounge mark, selected navigation and selected film outlines. `accent-hover` brightens primary hover and keyboard focus.

### Neutral

- **Blue-black** (`ground`): the page ground and dark text on primary actions.
- **Lounge navy** (`surface`): request entry and film details. **Raised navy** (`surface-raised`) supports secondary actions, suggestions and poster fallback frames.
- **Cool white** (`ink`): headings and principal text. **Mist blue** (`muted`) supports facts, help, navigation and secondary actions. `explanation` gives streamed recommendation prose its slightly brighter reading tone.
- **Slate line** (`line`): header/footer dividers and suggestion borders.
- **Poster black** (`poster-ground`): letterboxing behind intact poster art.
- **Save navy / save ice** (`save-bg`, `save-ink`): compact save/remove actions; `save-hover` brightens their background. `secondary-hover` is the separate secondary-action hover tone.
- **Warm warning** (`warning`, `warning-bg`): legible amber text over a brown-tinted inset for requirements and operational warnings; this is a semantic exception to the cool palette.

## Typography

**Display Font:** Manrope, sans-serif. **Body Font:** DM Sans, sans-serif. Both are self-hosted variable fonts with `font-display: swap`; font synthesis is disabled. Local font source and OFL records accompany the files under `cinemood/static/fonts/`.

Rounded headings give the lounge its identity; unembellished sentence-case controls and compact metadata support comparison. There is no separate oversized marketing display style.

### Hierarchy

The frontmatter records repeated desktop roles. The collection page heading uses `headline`; section headings use `section-title`; film titles use `film-title`. Explanations use `explanation` with a maximum width of 65ch; expanded request help reaches 75ch. Facts use tabular numerals.

The wordmark uses `brand` at 23px desktop and 22px on narrow screens. Film titles are 17px desktop and 19px on narrow screens. Request entry uses `request` and reduces to 16px on narrow screens. Additional implemented roles are synopsis (14px / 1.6), synopsis heading (14px), navigation (15px; 14px on narrow screens), helper/control labels (13px), text actions (13px), and fallback title (20px / 1.25; 16px in narrow spotlight frames). Heading weight is 700, brand 800, primary/secondary controls 700 and save controls 600.

## Layout

The desktop shell uses 3.5vw gutters, a 68px header, and 20px top / 28px bottom main padding. Request entry remains one horizontal band with a label, flexible textarea and actions, now inset by 10px / 16px.

Five equal film columns use 18px column and 28px row gaps. Counts below five use bounded adaptive columns: one up to 420px, two up to 360px each, three up to 340px each, four equal columns. This keeps small result sets from stretching. Below 1150px the default becomes three columns (four-result sets use two); below 800px it becomes two, and below 500px recommendations stack. The spotlight shows up to five films, in five desktop columns, three below 1150px or two below 800px; below 500px they become compact single-column entries with a 96px poster beside the title and actions.

Poster frames have a bounded height: `clamp(170px, 26svh, 225px)` for desktop recommendations, `clamp(210px, 34svh, 290px)` for spotlight films. Narrow-screen recommendation frames are 240–245px and spotlight frames are 144px below 500px. Artwork remains intact with `object-fit: contain`; a strongly blended, saturated copy of the same poster fills the spare width with its own colors. Hide the title fallback only after a successful image load.

**The Intact Poster Rule.** Preserve the whole foreground poster and a clear title-led failure state. Background color may come from the same poster.

Poster background strength is controlled by `--poster-background-strength` in
`cinemood/static/style.css`, currently `85%`. Set `0%` to hide it or `100%` for
full strength. The background is a blurred, saturated copy of the actual poster;
it requires no palette extraction or extra image service.

Inline disclosure does not change a card's column or its neighbours' horizontal positions. The selected card receives a tonal highlight and a 2% poster enlargement; synopsis and full metadata appear below the title and facts, replacing the recommendation explanation while expanded. The explanation returns on close. Long synopses have a keyboard-scrollable, bounded reading area; actions remain available below it. On phones, spotlight details span the full entry width. Only one card is expanded at a time, on every screen size. No sidebar or modal is part of this interaction.

## Elevation & Depth

Depth is tonal, without decorative box shadows. Functional navy surfaces separate from the blue-black ground; one-pixel slate dividers organize the shell. A selected poster gains a two-pixel periwinkle inset outline and a quiet navy card background; hover uses a one-pixel outline. Keyboard focus uses a two-pixel light-periwinkle outline with a five-pixel offset.

**The Open Film Rule.** Film entries sit directly on the ground; keep their title, facts and actions outside the poster frame.

## Shapes

The recurring shapes are gently rounded rectangular controls (`control`), larger request/poster/detail surfaces (`surface`) and slightly tighter save controls (`save`). The lounge mark is three narrow periwinkle bars with rounded ends, differing in height. Inline details use a simple top divider within the selected entry. No pill-chip vocabulary is implemented: optional restriction changes are rounded rectangular suggestion buttons.

## Components

### Buttons

Primary and secondary buttons share compact padding and bold text; their frontmatter tokens specify shape and colors. The primary action is periwinkle with blue-black text; secondary actions are raised navy. Save/remove actions are smaller and semibold, with a stable 108px minimum width across pending and success states. Details, Close details and Cancel search use underlined text actions (underline offset 4px). General button minimum height is 40px; compact save and text actions use 36px. Disabled actions have opacity .65, except the persistent Saved state, which remains fully legible. Background and text hover transitions last 160ms with ease-out timing.

### Inputs / Fields

The request textarea is transparent within the navy band, automatically growing with its content up to 160px and set at 17px desktop / 16px narrow. Focus uses only a subtle accent underline on the field, never an outline around the whole band. Keyboard focus remains visible. Enter submits; Shift+Enter adds a visible line; composition events do not submit. The field resizes on input, viewport changes and history restoration. Original request, current/original restrictions, mood/theme interpretation and any selected adjustment remain inside the collapsed Request details disclosure. Unsupported-requirement warnings and clarification prompts stay visible outside it; technical interpretation does not stretch the results header.

### Navigation

Muted links brighten on hover. The current page uses principal text and a three-pixel accent underline; links remain sentence case. The wordmark combines Manrope with the three-bar lounge mark. On narrow screens navigation is a full-width row below the wordmark.

### Cards / Containers

A film entry consists of an interactive intact poster, title, year/runtime/genres, optional explanation and wrapping action row. Its frame is rounded; the entry itself has no surface fill or border. Missing poster images reveal a typographic title and “Poster unavailable” instead of a fabricated cover. Available imagery comes from retained TMDB catalog snapshots through validated fixed `image.tmdb.org` paths, with attribution retained in the footer; no generated or vendored raster artwork defines this system.

### Film details

Poster and Details buttons toggle the card's inline synopsis and full catalog metadata. The selected entry has a slightly enlarged poster, accent outline and tonal ground. Selecting another card closes the former entry without moving columns. Close details and Escape collapse the entry; focus returns to its opener when dismissed. Native buttons expose `aria-expanded` and unique `aria-controls` references. Catalog TMDB identities produce a fixed HTTPS TMDB link that opens in a new tab with `noopener noreferrer`; fixture identities do not invent external links.

### Suggestions and warnings

Optional restriction changes are bordered raised-navy buttons with accent hover borders; they wrap with a 10px gap. Warning blocks use the semantic warm pair, control rounding and compact inset padding. Keep both readable and explicit in the request context.

### Spotlight and replacement

Five spotlight films refresh on homepage entry, browser-history restoration and the explicit Shuffle films button. Previously shown IDs are passed as exclusions; available unseen films are preferred without inventing a relevance/popularity ranking. Keep the old selection during loading and recoverable errors. Empty or exhausted small catalogs show an explanation and disable useless shuffles; failures allow retry.

The header stays sticky, slides away after 12px of downward scrolling below its own height, and returns on upward scrolling, keyboard focus or mouse proximity within 20px of the viewport top. Hover/focus keeps it available; reduced motion removes the slide.

Initial spotlight posters drift vertically by only 2px over 16 seconds and pause on interaction. Titles, metadata and actions remain stationary so their text stays sharp; never apply ambient transforms to the whole track. Replacement results use a 200ms settle; inline disclosure and poster selection use short ease-out transitions. Reduced motion removes animations and transitions.

### Save states

Save uses a bookmark icon, accented border and navy fill. Hover brightens the fill/border without translating the control; press darkens the fill. Pending saves show Saving… and expose busy/disabled state. Success swaps in a checkmark, Saved label and quieter persistent fill without fading the text. Duplicate saves remain disabled. Spotlight films offer the same Save action and share saved state with recommendation cards. Collection grids adapt to their remaining card count after removal. Errors keep the action available with visible retry feedback; successful feedback is announced without duplicating prose beneath the button. Collection removal remains a quieter distinct action.

**The Quiet Motion Rule.** Pause ambient movement when the visitor interacts; disable animation and transitions for reduced motion.

## Do's and Don'ts

### Do:
- **Do** use Manrope for identity and headings and DM Sans for controls and reading text.
- **Do** preserve visible keyboard focus, explicit detail close controls, Escape dismissal and focus return.
- **Do** keep factual metadata and explanations beneath the poster and preserve required TMDB credits.
- **Do** use the same film presentation in Discover and My collection.

### Don't:
- **Don't** crop portrait artwork to fill a landscape comparison frame.
- **Don't** wrap each film entry in another raised card or add decorative shadows.
- **Don't** hide warnings about unchecked requirements in visual decoration.
- **Don't** continue ambient animation after interaction or when reduced motion is requested.
