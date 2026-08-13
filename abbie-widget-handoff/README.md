# Abbie chat widget — handoff package

Design handoff for the Institute for Protein Innovation's chatbot widget. Everything here is settled design; nothing in it needs re-deciding.

## How to use this package

**Read `SPEC.md` first, then write the implementation plan yourself.** The division of labour is deliberate: the spec says *what* to build and why, because those decisions are made and signed off. The plan — sequencing, file-level diffs, checkpoints — should come from you after reading the actual current code, because you can verify function names and catch anything that has drifted since the design was written.

Suggested opening prompt:

> Read SPEC.md in full, then read apps/api/static/index.html and apps/api/main.py. Produce an implementation plan that sequences the work into reviewable steps, names the exact functions and CSS blocks each step touches, and flags anything in the spec that no longer matches the code. Do not start editing until I approve the plan.

## What the design touches

One file for almost everything: **`apps/api/static/index.html`** (single file, vanilla JS, no build step).

Two small server-side additions in **`apps/api/main.py`**, both approved:

1. Add `form` to the `route` SSE frame (the router already computes it; it just isn't sent).
2. Add `short`, `journal` and `title` to each `done.sources` item. IPI has confirmed the corpus holds this metadata.

Nothing else server-side changes. The SSE parser, routing pipeline, scrubber contract and markdown rendering are all out of scope.

## Anchor points in the existing widget

Worth locating before you start: `createTurn()` (where the three grey dots live), `clearThinking()`, `onRoute` / `onDelta` / `onDone`, `renderSources` / `renderFollowups`, `send()` and its `inFlight` guard, and `announce()`.

## Files

| file | what it is |
|---|---|
| `SPEC.md` | **The specification.** 14 sections, matching the kit's numbered sections. |
| `Abbie Widget Kit.dc.html` | **Visual reference.** Open in a browser — every state rendered at real size, with live animation. Sections 01–12. |
| `Abbie Widget Explorations.dc.html` | Record of rejected options and why. Context only — **never build from this file.** |
| `assets/mark-solid.svg` | The mark below 48 px. Launcher, avatar, activity, favicon. |
| `assets/mark-expressive.svg` | The mark at 48 px and up. Greeting, hero, print. |
| `assets/ipi-logo-dark.png` | IPI lockup for light backgrounds. |
| `assets/ipi-logo-light.png` | IPI lockup for dark backgrounds. |
| `Abbie.dc.html` | **Marketing only.** Animated cartoon mascot — LinkedIn, slides, stickers. Never on the site, not part of this build. |
| `abbie-flat.svg` | Static export of the cartoon mascot. |
| `support.js` | Runtime that lets the two `.dc.html` files open directly in a browser. |

## The five decisions most likely to be second-guessed

Stated here so they survive the handoff:

1. **No cartoon mascot on the website.** The site is white, spacious and institutional; a cartoon face in the corner reads as a different company. The mark carries Abbie instead — and it stays upright so the mark and the cartoon remain one character.
2. **Answers at 15 px, not 13 px.** The single biggest reason the current widget reads as dated.
3. **No orange in the widget.** Focus is an ink ring plus the send button turning red. `#F49B0B` stays a site CTA colour.
4. **Errors are never red.** Red is the brand — launcher, send, citations. A red error block reads as furniture, not a warning.
5. **Abstain, redirect and refuse are not errors.** They are the product working correctly and render as ordinary answers.

## Accessibility rules that are part of the design, not extras

- Text ≤12 px: `#6E737B` or darker on white, `#5C6169` or darker on tinted fills.
- Small red text: `#B3161C`, never `#EC1D24`.
- Non-text cues (focus rings, state boundaries): 3:1 against their own background.
- Touch targets 44 px minimum, with `flex:none` so they cannot shrink.
- The composer input is 16 px on mobile — anything smaller makes iOS Safari zoom and never zoom back.
- `prefers-reduced-motion`: all activity states show a static mark and keep the words.
- Every status change and notice goes through the existing `announce()` live region.
