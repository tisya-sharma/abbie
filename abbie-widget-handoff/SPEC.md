# Abbie chat widget — design specification

Institute for Protein Innovation. Visual reference: **Abbie Widget Kit.dc.html** (open in any browser; sections 01–12 correspond to the headings below). Rejected explorations are recorded in **Abbie Widget Explorations.dc.html** — do not build from that file.

Target: `apps/api/static/index.html` — single file, vanilla JS, no build step. Everything here lands in that one file unless a change is explicitly marked as touching `apps/api/main.py`.

---

## 0 · The one thing to get right

On the website, **the antibody mark is Abbie**. Her silhouette is the launcher, the header avatar and the activity indicator; her name is the serif wordmark; motion carries her personality. The illustrated cartoon Abbie (`Abbie.dc.html`, `abbie-flat.svg`) is a **marketing-only asset** — LinkedIn, slides, stickers. She is never rendered on proteininnovation.org and is not part of this build.

This is deliberate: the site is white, spacious and institutional. A cartoon face in the corner reads as a different company. The mark keeps the warmth without the tonal clash — and it stays upright specifically so the cartoon and the mark remain the same character.

---

## 1 · The mark

One geometry, two treatments, split at 48 px. Both files are in `assets/`; they differ only by two `opacity` attributes, so they can never drift into two different marks.

- **`mark-expressive.svg` — 48 px and up.** Light chains at `opacity .62`. Hero art, the panel greeting, slides, print.
- **`mark-solid.svg` — below 48 px.** One colour, same paths. Launcher, header avatar, activity mark, favicon, flat print.

Geometry (24 × 24 viewBox, round caps and joins, `currentColor`):

| path | stroke-width |
|---|---|
| `M12 12.4 L9.1 8.4 L6.4 4.9` (left Fab, hinged) | 3.4 |
| `M12 12.4 L14.9 8.4 L17.6 4.9` (right Fab, hinged) | 3.4 |
| `M12 12.2 L12 19.4` (Fc stem, heavier) | 5 |

**Never rotate it.** Upright is what makes it legible as an antibody; sideways reads as a pipe fitting, diagonal as a generic sparkle. It also breaks optical centring in the circle and turns the pulse into a wobble.

Below 48 px the light-chain segment is about two pixels of lighter red on red and reads as a rendering error — that asymmetry is the whole reason for the split. The hinge itself still reads at 22 px.

---

## 2 · Launcher

Bottom-right, every page. 60 px circle, `#EC1D24`, shadow `0 6px 18px rgba(0,0,0,.28)`, white **solid** mark at ~27 px. Hover `scale(1.06)` over .25 s.

Four states, in order:

1. **On load** — mark plus a static label pill to its left: white, 1 px `#E7E9EE`, **radius 3** (square, matching site buttons), padding `6px 11px`, 11.5 px/500 ink "Chat with us", shadow `0 4px 14px rgba(15,17,21,.10)`. Silent, no motion. A static label is not the annoying part — motion and repetition are — and it removes all guesswork about what the button does.
2. **After ~8 s** — the label swaps to a dismissible nudge card: white, radius 4, shadow `0 8px 22px rgba(15,17,21,.12)`, 11 px text, ✕ top-right. Copy: "Questions about our antibodies or courses? Chat with us." **Once per session**, never re-shown after dismissal.
3. **Open** — circle turns ink `#0A0A0B` with a ✕.
4. **Afterwards** — icon-only for good. Persist first open/dismiss in `localStorage`; on later visits show the bare mark. Visitors have learned it by then.

---

## 3 · Panel (docked)

380 px wide, white, 1 px `#ECECE8`, radius 6, shadow `0 14px 34px rgba(15,17,21,.14)`.

**Header** — 30 px red circle with the solid mark; serif wordmark "Abbie" at 19 px (capital A `#EC1D24`, rest `#0F1115`); sub-line 10.5 px `#6E737B`: "IPI antibody assistant · RESEARCH USE ONLY" with the disclaimer in 10 px, weight 600, letterspacing .05em. Expand and minimise icons right, 14 px, `#6E737B`, 2 px stroke. Divider 1 px `#EFEFEB`.

The disclaimer is a regulatory notice: never smaller than 10 px, never lighter than `#6E737B`.

**First-open greeting** — the panel's only mascot moment. Centred **expressive** mark in a 64 px red circle, `ab-pop` .5 s `cubic-bezier(.34,1.56,.64,1)`, then `ab-nod` 1.6 s at .4 s delay, transform-origin `50% 60%`, once. Greeting in red serif `#D8161D` at 20 px: "Hi — I'm Abbie." Sub 13 px `#6E737B`: "Ask me about antibody validation, IPI reagents or courses. I cite my sources." Then three suggested questions: white rows, 1 px `#E7E7E3`, radius 4, 13 px ink, hover border `#C6CBD2`.

**Conversation** — user turns right-aligned, bg `#F2F2F0`, radius 4, 14 px `#4B5058`, max-width 85 %. Assistant turns as flowing text at **15 px / 1.6**, `#1B1E23`, paragraph gap 13 px, **no bubble**. Inline citation chips: bg `#FBEAEA`, text `#B3161C`, 10 px/600, radius 4, padding `1px 5px`, raised 2 px.

The 15 px body size is not cosmetic — the current widget sets answers at 13 px, and that is the single biggest reason it reads as dated.

---

## 4 · Activity indicator

Replaces `.abbie-thinking` / `.abbie-dot` / `@keyframes abbie-pulse`. A 22 px red circle with the white solid mark (~11 px, stroke-width 3.4/5) plus one status line at 12 px `#6E737B`, gap 9, `padding:14px 0 0`.

**Motion maps to state.** Each change corresponds to a real change in the stream, so the change always carries information:

| state | when | motion |
|---|---|---|
| **Breathe** | send → `route` frame | `0%,100% { transform:scale(1); opacity:.62 } 50% { transform:scale(1.13); opacity:1 }`, 1.8 s ease-in-out infinite, on the **circle** |
| **Sway** | `route` frame → first `delta` | `0%,100% { transform:rotate(-7deg) } 50% { transform:rotate(7deg) }`, 2.4 s ease-in-out infinite, on the **mark**, origin `50% 62%` |
| **Still** | first `delta` | motion stops, indicator removed by `clearThinking()` |

Waiting is passive (listening); working is active (a molecule in solution); streaming needs no indicator because the words are the progress signal and motion beside them is noise.

The greeting nod is a **separate one-shot** — panel open only, never during a turn, so it cannot be misread as a working state.

Name the component `AssistantActivity`, not `ThinkingIndicator` — the concept must survive future retrieval or tool stages. Keep `clearThinking()`'s name and call sites; only what it removes changes. Announce status changes through the existing `announce()` live region. Under `prefers-reduced-motion` all three states show a static mark and keep the words.

---

## 5 · Status copy

**The phrase describes this question, not a stock cycle.** `router.md` already classifies every question before generation into a `behavior` (answer / abstain / redirect / refuse) and, for answers, a `form`. The route frame carries `behavior`, `subject` and `fallback` today — **add `form`** (one line in `turn_worker` in `apps/api/main.py`). Approved by IPI.

**Opening beat** (send → route frame), neutral: "Thinking…" or "Getting oriented…".

**Working beat** (route frame → first token), keyed to the route:

| route | working phrase |
|---|---|
| `answer` / `definitional` | Gathering sources… |
| `answer` / `conceptual` | Weighing the evidence… |
| `answer` / `comparative` | Cross-referencing… |
| `answer` / `procedural` | Lining up the evidence… |
| `answer` / `deepening`, `acceptance` | Gathering sources… |
| `abstain`, `redirect`, `refuse` | Getting oriented… |

**Two hard rules:**

1. **Never expose internals.** No corpus, retrieval, routing, tools, documents or model names in user-facing copy. Gerunds, sentence case, one ellipsis, under four words where possible.
2. **Abstain, redirect and refuse never show evidence language.** Those replies carry no sources, so "Gathering sources…" would promise something the answer cannot deliver — the one way a status line can actually lie.

**Rotation as fallback only:** if the route frame is slow or `form` is null, cycle the neutral openers rather than freeze. On a long working stage one second phrase may follow; never more, or it reads as stalling.

---

## 6 · Message actions

**Bare icon row — no capsule, no text labels.** (A pill-wrapped variant was built and rejected as too heavy; it stacked a third grey surface under the answer.)

- Row: `display:flex; align-items:center; gap:1px; margin-top:12px; margin-left:-6px` — the negative margin optically aligns the first icon with the text column above. **Settled turns only** — never mid-stream, never on an incomplete answer.
- Order: **copy · retry · 👍 · 👎 │ •••** — five 28 px buttons, radius 6, transparent at rest, icons 14 px `#6E737B` at stroke-width 1.9. Hover fills `#F4F4F1`. A 1 px `#E7E7E3` divider (14 px tall, 6 px side margins) before the overflow, so a menu never reads as an action.
- The row recedes via the absent hover fill, **not** via low contrast. Icon-only controls must clear 3:1.
- `type="button"`, `aria-label` and `title` on every button. Icons carry the meaning; do not add visible labels.

Behaviour:
- **Copy** → `navigator.clipboard.writeText(turn.els.body.textContent)`; swap to a check for ~1.5 s and `announce("Response copied.")`.
- **Retry** → re-send the turn's question. Guard on `inFlight`.
- **Feedback** → one-shot per turn, `aria-pressed`, icon fills `#B3161C`.
- **•••** → popover: white, 1 px `#E7E7E3`, radius 4, shadow `0 8px 22px rgba(15,17,21,.14)`, 4 px padding; items 12 px `#4B5058`, `padding:7px 10px`, radius 3, hover `#F4F4F1`. Items: **View sources** (omit when none), **Copy as plain text**, **Report an issue**. `role="menu"`/`menuitem`, Escape closes and returns focus, outside click closes, arrows move. Anchor it so it never covers its own trigger.

---

## 7 · Sources

Collapsed to a count by default; expanded on click; **capped at three visible rows**. Two earlier designs (tile row, journal-name chips) were rejected — chips truncated journal names and repeated identically across papers from the same journal.

**Amended 2026-08-15, both clauses.** Inline citation pills now sit in the reply itself, and two rules above had to give way.

*Chips are back.* The objection was never the shape, it was the label. The pill carries the **journal**, falling back through `short` to `title` for a work with no journal, such as a book. A claim resting on several papers shows the first plus `+N`. The pill reuses this section's own collapsed-control tokens, so the two read as one system rather than two.

This was decided against the argument one paragraph down, that "author + year is unique where a journal name is not". That argument still holds, and it is the known cost: two papers from one journal do render identical pills, and the byline in the expanded rows is what separates them. Both labels were built and read side by side in the running demo, and the journal was chosen on that evidence. Do not revert it on the strength of the earlier paragraph alone.

*The three-row cap is gone.* Every pill indexes into the expanded list, so a row the layout hides is a citation the reader cannot follow. Expanding now shows every source and the block's height varies with the count. `MAX_SOURCES` is removed server-side for the same reason, which also settles the open call in section 14: with no cap, the "N more" state that section asked for never occurs and its control has been removed.

**Collapsed (default).** One inline control, `margin-top:15px`, radius 999, no fill at rest, padding `5px 10px 5px 8px`, gap 8: a 13 px document glyph, `N sources` at 12 px/600, a 9 px chevron — all `#B3161C`. Hover fills `#F4F4F1`. This is what users see most of the time, and the count answers the real question: "is this grounded in anything?"

**Expanded.** Hairline `#F2F2EF` top border; header row `N SOURCES` at 10 px/700, letterspacing .1em, `#6E737B`, up-chevron right. Then up to three rows, `display:flex; gap:9px; padding:7px 0`:

- red index numeral, 11 px/700 `#B3161C`, fixed 11 px column, `padding-top:1px`;
- **line 1 — the credibility line:** `Uhlén 2016` at 12 px/600 `#1B1E23`, then ` · Nature Methods` in `#6E737B`;
- **line 2 — the relevance line:** full title at 12.5 px/1.4 `#1B1E23`, `margin-top:2px`, wrapping freely.

Close with **"N more"** at 12 px/600 `#B3161C`, indented 20 px to align with the titles. Height is therefore constant at 3 sources or 70.

**Zero sources renders nothing** — no control, no label, no empty shell.

Why this shape: author + year is unique where a journal name is not (two eLife papers are "Edfors 2018" and "Laflamme 2019", never two identical chips), it never truncates at 380 px, and it is how scientists name a paper out loud. The journal earns trust; the title establishes relevance. Both matter, so both are shown — provenance first, as one spoken phrase.

**Backend.** `done.sources` currently emits `{label, url}`. IPI has confirmed the corpus holds the metadata, so add `short` ("Uhlén 2016"), `journal` and `title` per item. If any field is absent, that piece drops out of the line and the row still renders — the layout must not depend on it. `MAX_SOURCES = 3` today; **do not hardcode three**, the design handles any count.

---

## 8 · Composer

At rest: bg `#F8F8F6`, radius 6, `box-shadow: inset 0 0 0 1px #EDEDE9`, placeholder 14 px `#5C6169` "Ask about antibody validation…". Hint row beneath at 11 px `#5C6169` reading "Enter to send". Send: 28 px circle, bg `#E4E4DF`, white ↑ — disabled until the field has content.

Focused / typing: bg white, `box-shadow: inset 0 0 0 1.5px #1B1E23, 0 0 0 3px rgba(15,17,21,.06)`, text 14 px `#1B1E23`, hint switches to "Shift + Enter for a new line", send becomes `#EC1D24` with `0 3px 10px rgba(236,29,36,.32)`.

**No orange anywhere in the widget.** `#F49B0B` is a site CTA colour; the widget does not use it. Focus is an ink ring plus the send button waking up red — the accent lives on the button, not as a coloured outline. The circular send deliberately echoes the launcher: the same red circle that opened the panel is the one that sends.

The hint row is why this option won over a single-line pill: Shift + Enter has to be teachable, and a research assistant gets long multi-line questions. Field grows to about five lines, then scrolls internally.

---

## 9 · Mobile

**One breakpoint: 640 px.** Above it, the docked panel. Below it, a full-screen sheet — a 380 px floating card on a 390 px phone is a card with no page around it.

- **Sheet:** header pinned, transcript scrolls, composer fixed at the bottom. Expand and minimise are replaced by a single ✕ at a 34 px target.
- **Launcher:** 52 px, bottom-right, safe-area inset. **No label pill and no timed nudge** — a card covering content on a small screen is intrusive and there is no room beside the button.
- **Touch targets:** the action row's 28 px squares become **44 px**, always visible (there is no hover to reveal them). Icons stay 14–15 px; only the tappable area grows. Send goes 28 → 34 px. Set `flex:none` on each target so it cannot shrink at narrow widths.

**Two traps that only appear on a real device:**

1. **The composer input must be 16 px on mobile.** iOS Safari zooms the page when a focused input is smaller, and does not zoom back out. Only the input changes; everything else keeps its desktop size.
2. **`100vh` is wrong.** Mobile browser chrome makes it taller than the visible area, so a `100vh` sheet hides its own composer behind the keyboard. Use `100dvh` and pad the composer with `env(safe-area-inset-bottom)`.

Everything else is identical: answers stay 15 px / 1.6, sources keep the byline-over-title row capped at three, the mark stays solid, activity states are unchanged.

---

## 10 · Expanded panel

A cited answer with seven references is cramped at 380 px. Expanded is a **centred dialog, not a wider dock** — at that point the conversation is the task and the page behind it is not.

- 720 px wide, `min(84vh, 820px)` tall, centred, scrim `rgba(15,17,21,.28)`, radius 6, shadow `0 24px 54px rgba(15,17,21,.20)`.
- Below a 780 px viewport it falls through to the mobile sheet. There is no third layout.
- **Only three things change inside:** text is centred in a 620 px reading measure, sources start expanded in two columns showing six rows, and the expand icon becomes a collapse icon. Type sizes, colours and spacing are identical to the docked panel.
- Escape and scrim click **collapse to the docked panel, never close the conversation**. The transcript persists across both states. Focus moves into the dialog on open and returns to the expand icon on collapse.

---

## 11 · Errors and notices

**Red cannot mean error in this product.** It is the launcher, the send button and every citation numeral — a red error block would read as brand furniture rather than a warning, and it makes an ordinary failure feel institutional. Notices are ink on a neutral fill with a single amber rule.

**Anatomy:** fill `#FBFBF9`, 2 px left rule `#C98A28`, radius `0 4px 4px 0`, padding `12px 14px`. Body 13.5 px `#1B1E23`. Action in 12.5 px/600 `#B3161C` with a 12 px icon. One sentence, one action, optional human fallback.

- **Request failed** — "I couldn't reach the server just now." → **Try again** (re-sends the same question), plus "or email info@ipi.org".
- **Stream interrupted** — keep the partial text, it may still be useful, but mark it explicitly: "This answer stopped early — the connection dropped." → **Ask again**. **Suppress sources and the action row on an incomplete answer** so nobody quotes half a sentence as guidance.

**Abstain, redirect and refuse are not errors.** They are Abbie working correctly — declining a named-reagent question, steering back on topic, refusing clinical use. They render as **ordinary answers** in normal ink, with no notice styling and no sources block. Styling them as failures would tell visitors the product is broken when it is behaving exactly as designed.

**Copy rules:** say what happened and what to do next. Never show status codes, stack traces, model names or the word "unexpected". Announce every notice through the existing live region.

---

## 12 · Tokens

| | |
|---|---|
| Red | `#EC1D24` · deep `#B3161C` for links, citations, numerals, small red text · `#D8161D` serif accents |
| Orange | `#F49B0B` — site CTA colour, **not used in the widget** |
| Ink | `#0A0A0B` · text `#1B1E23` / `#0F1115` · secondary `#6E737B` · on tinted fills `#5C6169` |
| Lines | `#ECECE8` panel · `#EFEFEB` header · `#F2F2EF` hairline · `#E7E7E3` rows · `#EDEDE9` field |
| Fills | `#F8F8F6` field · `#F4F4F1` hover · `#FBFBF9` notice/tile · `#F2F2F0` user turn · `#FBEAEA` citation |
| Amber | `#C98A28` — notice rule only |
| Display type | Source Serif 4 — wordmark and greeting **only** |
| UI + body type | Hanken Grotesk 400/500/600/700 |
| Type scale | 15/1.6 answers · 14 composer and user turn (**16 on mobile**) · 12.5 sources · 12 actions · 11 hints · 10 disclaimer |
| Radius | 3 site-matching buttons and the label pill · 4 fields, chips, notices · 6 panel, tiles, icon buttons · circle launcher and send |
| Breakpoints | 640 px sheet · 780 px expanded-dialog floor |
| Motion | pop .5 s spring · nod 1.6 s once · breathe 1.8 s · sway 2.4 s · hover .15–.25 s |

**Contrast floor.** On white, text at 12 px or below uses `#6E737B` or darker. **On a tinted fill** (`#F8F8F6`, `#F4F4F1`) that is not enough — use `#5C6169` or darker, placeholders included. `#9099A4` is for borders and larger non-essential text only. Small red text uses `#B3161C`, never `#EC1D24`. **Non-text cues** — focus rings, state boundaries, control outlines — need 3:1 against their own background, which is why a focused field takes an ink ring rather than a pale grey one.

**Fonts** are both free (Google Fonts). Self-hosting avoids a third-party request on every page of the site; either delivery is acceptable.

---

## 13 · What not to touch

The SSE parser, the scrubber contract, markdown-lite rendering, follow-up chips, the launcher's `localStorage` keys, and the routing pipeline itself. The only server-side changes anywhere in this spec are adding `form` to the route frame and `short`/`journal`/`title` to source items.

**Amended 2026-08-17.** `POST /feedback` is a third: the thumbs buttons post a verdict, which is recorded as a telemetry span and stored nowhere else. See the open call in section 14.

---

## 14 · Open product calls

None of these block the build; pick a default and note it.

- ~~**Thumbs up/down storage** — no feedback endpoint exists. Keep it local per turn (visual only) or add one. Do not invent an endpoint silently.~~ Settled 2026-08-17: the endpoint exists. A verdict posts to `POST /feedback` and is stored as a telemetry span and nowhere else, no file and no database, and the buttons stay one shot per turn.
- **Retry** — replace the previous answer or append a second one. Appending is safer; replacing is tidier.
- ~~**`MAX_SOURCES`** — leaving it at 3 means the "N more" state never appears in practice. Build it anyway.~~ Settled 2026-08-15: the cap is removed and the expanded list shows every source, so there is no "N more" state. See the amendment in section 7.
- **Font delivery** — self-host or CDN.
