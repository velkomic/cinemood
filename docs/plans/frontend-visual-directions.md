# CineMood visual directions

Owner feedback, 2026-11-10: Screening lounge is preferred for its logo and
recommendation layout. Prefer the cleaner, compact top section of Cinematheque
and Familiar movie browser, and the latter's simple text Details action over
the lounge's bordered View details button. A combined `screening-refined.html`
sketch is now the lead option on the reopened local board, alongside the
original comparisons. The owner subsequently selected this combined sketch and authorized
implementation.

Status: concrete desktop sketches presented for owner choice on 2026-11-10.
The owner selected Screening lounge refined; implementation evidence is recorded
in `../progress.md`. The completed
interview was reused; product discovery was not repeated.

The task is to translate an ordinary-language request into three comparable
catalog films with specific explanations, then save promising alternatives.
The scene is an individual or friends choosing a movie on a desktop, often
in the evening. The visual world should belong to film discovery and keep
request entry and comparison immediately usable. Mode: Operate.

The category rut is a narrow streaming-service shelf with a marketing hero;
its predictable opposite is an oversized experimental poster wall that makes
comparison difficult. Neither is the proposed product layout.

## Direction derivation

Grounded candidates considered in order of relevance:

1. Cinematheque programmes: warm black, amber and serif film titles; a compact
   search band gives most of the viewport to three films.
2. Contemporary film indexes: crisp cyan, sans typography and dense metadata;
   clear request context beside the comparison.
3. Film journals: burgundy surfaces, cream text and editorial title hierarchy;
   concise film reasoning supports deliberate reading.
4. Video-shop browsing: dark violet, vivid cover color and compact labels;
   recognisable cover-first browsing extends into saved collections.
5. Film-festival identity: charcoal, vermilion and strong sans type;
   disciplined title/metadata grouping supports a busy comparison.
6. Evening screening lounges: blue-black and periwinkle, humanist sans and open
   spacing; selected-film emphasis connects a recommendation to its detail pane.
7. Animation colour scripts: deep teal, warm accent and precise media framing;
   controlled poster movement settles into a stable comparison.

The skill's direction seed is `seed:31c82424d28a7d6b`, assigning candidate 6.
The network retry succeeded; the direction round includes catalog challengers.
The seed is a source of alternatives, not owner approval.

## Presented choices

| Direction | Character and composition | Tradeoff |
| --- | --- | --- |
| Screening lounge | Blue-black, electric periwinkle, spacious sans; request above three equal film columns | Needs colorful real imagery to avoid a general app appearance |
| Cinematheque | Warm black, amber actions, serif film titles; compact request band and wide comparison | Familiar cinematic treatment; craft carries the distinction |
| Film grid | Black, cyan, flat media tiles; persistent left request area beside three films | Less room for posters on smaller desktops |

The Cinematheque is the designer's pick. A conventional dark movie browser is
also available as a quiet alternative. The direction board offers steering
and a fresh set of alternatives. The refined lounge was selected after owner feedback.

Sketches are in `.impeccable/mocks/decision/`: `screening-lounge.html`,
`cinematheque.html`, `film-grid.html`, and `standard.html`. They are static
1440×900 comparison artifacts, not functioning production pages. They use
explicitly labeled fictional fixtures and authored concept covers. Production
posters, loading states, detail panels, initial motion, responsive layouts,
warnings and collection behavior remain implementation work.

All four desktop sketches were rendered in Chromium and visually inspected.
Their buttons are illustrative. This is no claim of production browser,
mobile, accessibility or regression verification.

## Challenger assessment

The skill's Operate rules retain familiar app controls and layout; outside
references contribute only typography, palette, density and one useful move.
Every palette is constrained by the owner's dark-interface requirement.

- **Metro typographic tiles: competitive.** Strong scanability and familiar
  media browsing, but less breathing room than the lounge. Presented as Film
  grid; cyan signals selection without copying a panoramic navigation system.
  Its reference board was downloaded and inspected.
- **Data field: declined.** Monochrome data art weakens audience identification
  and colorful movie comparison. Keep its rigorous metadata alignment.
- **Lexicon: declined.** Archival reading density weakens movie browsing and
  direct comparison. Keep the separation of concise reasoning and full synopsis.
- **Vertical video: declined.** Full-screen single-item emphasis loses the
  required three-film comparison. Keep the commitment to large imagery.
- **Star atlas: declined.** Coordinates add interpretation without helping
  film choice. Keep quiet secondary controls and clear selection emphasis.
- **Crouwel grid: declined.** Constructed lettering competes with film titles
  and readable controls. Keep cross-surface alignment discipline.

These five disciplines are explicit improvements to the screening-lounge
proposal, not borrowed visual motifs. Declined alternatives remain visible
on the board and may still be requested.

## Next step

The owner selected Screening lounge refined for implementation. Preserve
the existing search and collection contracts. Additional batches and
contextual follow-ups require the decisions and acceptance cases in
[`frontend-redesign-spec-work.md`](frontend-redesign-spec-work.md); their controls
must not imply functioning capabilities before that work is agreed and built.
