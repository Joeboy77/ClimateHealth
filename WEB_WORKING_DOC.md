# ClimaHealth Predict — Agency Command Platform

Working doc for the Next.js dashboard. Companion to `WORKING_DOC.md` (backend, complete).

**The bar:** a panel of judges and health-agency officers looks at this and assumes a
design team built it. Nothing on screen should read as generated, templated, or default.

**Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done and reviewed

---

## 1. What this product is

A command platform for health agencies. An officer opens it to answer three questions,
in this order:

1. **Where is risk rising?** — the national picture, at a glance.
2. **Why, and how long do I have?** — the ranked risks for a district, with the exact
   climate conditions that fired and the lag window before cases appear.
3. **What do I do, and am I ready?** — assigned actions, resource stock against demand.

Every design decision serves that sequence. If an element does not help answer one of
those three questions, it does not ship.

This is not a generic analytics dashboard. It is an early-warning instrument. It should
feel closer to an operations console than to a SaaS marketing page.

---

## 2. Non-negotiable quality rules

### Things that make work look machine-made — banned

| Banned | Instead |
| --- | --- |
| Emoji anywhere in the UI | `lucide-react` icons, one set, consistent stroke width |
| Purple/violet gradients, gradient text | Flat, considered colour with real semantic meaning |
| Glassmorphism, heavy blur, neon glow | Solid surfaces, one-pixel borders, restrained elevation |
| `rounded-2xl` + `shadow-lg` on every element | A radius and elevation scale, used deliberately |
| Raw Tailwind palette (`blue-500`, `gray-100`) | Project tokens only; no default palette in components |
| Even 3-across card grids of equal weight | Asymmetric layouts with a clear primary element |
| "Welcome back!", "Overview", "Analytics" | Domain language: "National risk picture", "Madina district" |
| Big numbers with no unit or comparison | Every figure carries unit, timeframe, and a reference point |
| Everything fading and sliding in on load | Motion only where it communicates a state change |
| Decorative illustrations, stock imagery | Data is the imagery |
| Centred body text, generous empty whitespace | Information density appropriate to an operations tool |

### Things that signal craft — required

- **Optical alignment**, not just mathematical. Icons and text baselines line up.
- **Tabular numerals** on every figure that sits in a column or changes in place.
- **Real states for everything**: loading (skeleton matching final layout, never a spinner
  alone), empty (explains what would appear here), error (says what failed and offers a
  retry), stale (shows when data was last fetched).
- **Keyboard operable end to end**, with visible focus rings that are designed, not default.
- **Colour is never the only carrier of meaning.** Every risk level pairs colour with a
  label and a distinct icon — this is a health tool, and red/green colour blindness affects
  roughly 1 in 12 men.
- **Content-first copy.** Written as a health officer would say it, in British English to
  match the backend's existing strings ("diarrhoea", "prioritise").

---

## 3. Design system

### Typography

Self-hosted via `next/font`, variable weights, no external requests.

- **UI and display:** Geist Sans — neutral, modern, excellent at small sizes, strong
  tabular figures. Alternative if a more institutional tone is wanted: IBM Plex Sans.
- **Data and identifiers:** Geist Mono — scores, coordinates, timestamps, IDs.

Scale (rem, 16px base), deliberately tight — this is a dense tool, not a landing page:

```
display   2.0    / 1.15  weight 600  tracking -0.02em
h1        1.5    / 1.2   weight 600  tracking -0.015em
h2        1.125  / 1.3   weight 600
h3        0.9375 / 1.4   weight 600
body      0.875  / 1.55  weight 400
small     0.8125 / 1.45  weight 400
micro     0.75   / 1.4   weight 500  tracking 0.02em  uppercase (labels only)
metric    1.75   / 1.0   weight 600  tabular-nums
```

### Colour

Warm-tinted neutrals, never pure grey. One brand accent. Risk semantics carry the weight.

```
Neutrals (light)          Neutrals (dark)
canvas    #FBFAF8         canvas    #0C0E0D
surface   #FFFFFF         surface   #151817
raised    #F5F4F1         raised    #1D211F
border    #E4E2DC         border    #2A2F2C
muted     #6F6D66         muted     #8B8F8A
ink       #1A1D1B         ink       #ECEEEB

Accent (interactive, brand)
accent        #0E6E63   deep teal — links, focus, primary actions
accent-hover  #0B564D
accent-subtle #E6F2F0 / dark #10241F

Risk scale — perceptually ordered, cool to hot
low       #1F7A5C   surface #E8F3EE   dark-surface #0F2A22
moderate  #B07908   surface #FBF1DC   dark-surface #2E230A
high      #C4551F   surface #FBEBE1   dark-surface #33190C
severe    #A32118   surface #FAE7E5   dark-surface #33110F

Confidence
live      accent
partial   moderate      (dashed border treatment)
demo      #5B54A8       (distinct, clearly marked as simulated)
```

**Risk icons** (paired with colour, always): low `shield-check`, moderate `alert-circle`,
high `alert-triangle`, severe `octagon-alert`.

Both themes ship. Dark is the default — this is a wall-mounted operations tool as much as
a desktop one — with a designed toggle, not an afterthought.

### Space, radius, elevation

```
space   2 4 6 8 12 16 20 24 32 40 56 72        (px, 4pt grid with a tight low end)
radius  sm 4 · md 6 · lg 10 · pill 999          (no 16px+ blobs)
border  1px solid, always — elevation comes second
shadow  1  0 1px 2px rgba(0,0,0,.06)            cards at rest
        2  0 4px 12px rgba(0,0,0,.08)           popovers, dropdowns
        3  0 12px 32px rgba(0,0,0,.12)          modals only
```

### Motion

```
instant   90ms   cubic-bezier(.2,0,.38,.9)   hover, focus, press
short     160ms  cubic-bezier(.2,0,.38,.9)   disclosure, tab change
medium    260ms  cubic-bezier(.2,0,0,1)      route transition, map fly-to
risk      420ms  cubic-bezier(.4,0,.2,1)     a risk level changing — the only "look at me"
```

Everything respects `prefers-reduced-motion`. A district changing risk level is the one
moment that earns real animation, because it is the product's entire thesis.

---

## 4. Stack

| Concern | Choice | Why |
| --- | --- | --- |
| Framework | Next.js 15, App Router, TypeScript `strict` | Server components for the data-heavy shell |
| Styling | Tailwind CSS v4, tokens in `@theme` | Tokens only; no raw palette in components |
| Primitives | shadcn/ui (Radix) | Accessible, unstyled, owned in-repo — not a themed kit look |
| Icons | `lucide-react` | One consistent set. No emoji, ever |
| Server state | TanStack Query | Cache, refetch on WebSocket event, stale indicators |
| Map | `react-simple-maps` + Ghana TopoJSON | A bespoke SVG map. See §5 — deliberately not Mapbox |
| Charts | Recharts, heavily restyled | Only where a chart earns its place |
| Types | `openapi-typescript` from `/openapi.json` | Contract cannot drift. **Do this first** |
| Theme | `next-themes` | Class strategy, no flash on load |

Deliberate omissions: no component kit with its own visual identity (MUI, Chakra, Ant),
no animation library until something needs it, no state manager beyond Query.

---

## 5. The map — and why it needs care

Ghana has 261 districts. The backend seeds **7**. A district-boundary choropleth would
render 7 filled shapes and 254 grey ones, which reads as broken, not as early-stage.

**Approach:** a clean Ghana outline with subtle region boundaries, and the seeded districts
as data points sized and coloured by risk, each labelled. It looks intentional at 7
districts and scales honestly to 261 later by switching the fill layer on.

- No tile basemap. No roads, no satellite, no attribution bar — those make it look like
  every other dashboard.
- Region boundaries at low contrast for geographic orientation only.
- District markers: risk colour fill, size by score, label with name and leading condition.
- Selected district gets a ring and pulls its detail into the side panel.
- A severe-risk marker animates once when its level rises — the `risk` motion token.

Fallback if TopoJSON handling proves fiddly: an accurate hand-traced Ghana SVG path with
positioned markers. Same visual result, less machinery.

---

## 6. Screens

### Shell
Persistent left rail (icon + label, collapsible), top bar with district search, theme
toggle, scope badge, and account. Scope badge is important: a district officer must always
see that they are scoped to Madina.

### 1 — National risk picture `/`
Primary: the map. Secondary: a ranked district table (sortable, keyboard navigable) with
name, region, overall level, leading condition, last updated. Above: three figures that
earn their place — districts at high or above, active alerts, districts with stale data.

### 2 — District detail `/districts/[id]` — the money screen
This is what wins the room. It must be the best-designed page in the product.

- Header: district, region, overall level, confidence badge, last updated.
- **Ranked risk list.** Each row: condition, level chip, score, lag window rendered as an
  actual timeline ("cases expected 3–8 weeks from now" as a small horizontal scale, not
  just text), vulnerable group. Expanding a row reveals the exact reasons the engine gave,
  verbatim — that transparency is the product's credibility.
- Climate snapshot: rainfall 7d/14d, consecutive dry days, humidity, temperature, dust,
  PM10. Each with unit and a plain-language reading.
- Citizen forecast card: the friendly headline, summary, and today's action, with a
  language switcher when the translation key is configured.

### 3 — Alerts `/alerts`
Ranked list, filterable by district and condition. Detail shows reasons and the
officer-facing recommended action. Never a generic "You have 3 notifications" pattern.

### 4 — Incident room `/incident/[id]`
Assigned agency actions grouped by agency, with status transitions inline. Optimistic
update, reconciled by the WebSocket event. Overdue actions surfaced without shouting.

### 5 — Readiness `/readiness/[id]`
Required units versus stock per resource, as a proportional bar, not a pie. Shortfall
stated in units, not just colour. This screen exists to make a gap undeniable.

### 6 — Reports `/reports`
Community reports, filterable, with location. New reports arrive live.

### 7 — Presenter control (hidden)
A keyboard-shortcut panel to fire `POST /demo/set-conditions`. Not in the navigation.
Used on stage to turn Madina red on cue. Must look like part of the product if seen.

---

## 7. Slices

Each slice is done when it is tested, keyboard operable, has loading/empty/error states,
and has been looked at in both themes at 1280px and 1440px.

### 0. Foundation `[x]`
- [x] Next.js 15 + TypeScript strict in `web/` (plus `noUncheckedIndexedAccess`, `typedRoutes`)
- [x] `openapi-typescript` generation wired to `npm run types:api`, types committed
- [x] Tailwind v4 with the full token set in `@theme` — light and dark
- [x] Geist Sans/Mono self-hosted, tabular numerals on tables and metrics
- [x] Base primitives owned in-repo: `Card`, `Button`, `Skeleton`, `RiskBadge`
- [x] Typed API client covering every endpoint, with `ApiError` and readable messages
- [x] Session provider: token persistence, `/me` revalidation, 401 cleanup
- [x] App shell: rail, top bar, theme toggle, scope badge
- [x] **`npm run design:audit`** — fails the build on any banned pattern from §2
- [x] `npm run verify` = typecheck + design audit + build

**Done:** build passes, 102 kB shared JS, zero npm vulnerabilities, design audit clean.

### 1. Access `[x]`
- [x] Split-layout sign-in: form left, product framing right over a subtle Ghana silhouette
- [x] One-tap demo account fills — practical for the panel, styled as product
- [x] Token storage, `/me` revalidation, 401 cleanup, `RequireSession` guard
- [x] Scope-aware navigation and routing (see D9)

### 2. National picture `[x]`
- [x] The map (§5) — real geoBoundaries geometry, pre-projected at build time
- [x] Label deconfliction so Madina and Accra Metropolitan do not collide
- [x] Ranked district table, keyboard navigable, hover syncs with the map
- [x] Three headline figures, each with unit and reference point
- [x] Skeletons matching final layout; typed error state with retry

### 3. District detail `[x]`
- [x] Ranked risk list with lag-window timelines rendered on a 10-week scale
- [x] Expandable engine reasons, verbatim
- [x] Climate snapshot, every reading with unit; missing readings say "not reported"
- [x] Citizen forecast card with the action-for-today callout
- [x] **District map** — real ADM2 boundary for each seeded district, district centre,
      and community-report pins fanned apart when they cluster within ~90 m
- [x] **Climate data source control** — switch between live Open-Meteo and a reproducible
      scenario, with the current source stated plainly. See D8.
- [ ] Language switcher — waits on a GhanaNLP key

### 4. Alerts `[ ]`
- [x] List, filters, detail with recommended action

### 5. Live `[ ]`
- [x] WebSocket client with reconnect and backoff
- [x] Query invalidation on event; subtle "updated just now" indicator
- [x] Risk-level change animation

### 6. Agency response `[ ]`
- [x] Incident room with inline status transitions
- [x] Readiness with proportional shortfall bars

### 7. Reports `[ ]`
- [x] List, filters, detail, live arrival

### 8. Polish `[ ]`
- [x] Presenter control
- [ ] Full keyboard pass; visible designed focus states throughout
- [ ] `prefers-reduced-motion` and `prefers-contrast` honoured
- [ ] Lighthouse ≥ 95 accessibility, ≥ 90 performance
- [ ] Every figure has unit and timeframe; every empty state written
- [ ] Read every string aloud — no placeholder copy survives

---

## 8. Review gate before demo

Sit down and check each honestly:

1. Could this be mistaken for a template? If any screen could, redesign it.
2. Is there a single emoji, gradient, or raw Tailwind colour? Remove it.
3. Does every number carry a unit and a reference point?
4. Tab through every screen — is the focus order sensible and always visible?
5. Grayscale the district detail screen — is risk still readable?
6. Unplug the network — does every screen fail gracefully?
7. Does the demo work at 1280px on a projector, in a bright room?

---

## 8b. Honesty rules

**Nothing on screen is fabricated.** Every number comes from either a live Open-Meteo
observation or an explicitly-labelled scenario, and the engine does identical work in both
cases. Two consequences that must hold:

- The provenance is always visible. `Live climate data` and `Simulated conditions` are
  distinct badges in distinct colours, on the district header and in the source control.
- A viewer can switch to live at any time and watch the numbers change. On 3 August 2026
  Madina read **high** on live data (19.2 mm rain over 7 days, 86.1% humidity) and
  **severe** under the heavy-rain scenario. Both are real engine output.

Seeded records (incident actions, stock levels, guardian profiles, the quiz bank) are
demonstration data and live under `infrastructure/seed/` in the backend. They are never
presented as observations.

---

## 8c. Known issues

**S1 — The access token travels in the WebSocket URL.** Browsers cannot set headers on a
WebSocket handshake, so `/ws?token=…` is the standard workaround, but the token then lands
in browser history and server access logs, and it appears in console warnings. Acceptable
on localhost with 12-hour demo tokens; before any real deployment the fix is a short-lived
single-use ticket: `POST /ws-ticket` returns a 30-second token that `/ws` exchanges once.

**S2 — `pkill -f "next start"` does not match the running process.** Next names it
`next-server`, so stale servers accumulate and an old one can hold the port while you
believe you are testing a fresh build. This cost a round of false performance numbers.
Use `pkill -f next-server`, and confirm with
`curl -s localhost:PORT | grep -o '/_next/static/chunks/[^"]*'` — production chunks carry
a content hash, dev chunks do not.

---

## 8d. National scale — what changed

The product moved from 7 hand-picked districts to **all 260 MMDAs across all 16 regions**,
which forced four changes:

- **Districts are generated, not typed.** `scripts/build-national-districts.mjs` reads
  geoBoundaries ADM2, assigns each district to its region by **spatial containment** against
  ADM1, and emits `backend/…/seed/data/districts.json`. Counts match Ghana's real structure:
  Ashanti 43, Greater Accra 29, Volta 18, Northern 16.
- **Open-Meteo is batched.** 260 districts across two endpoints would be 520 calls. The
  client now sends up to 50 locations per request, so a national sweep is ~12 calls and
  returns in **5 seconds against live data**.
- **The national map became a true choropleth.** A label column and leader lines worked at
  7 districts and produced an unreadable hairball at 260. All 260 district shapes are now
  filled by risk, with region boundaries over the top for orientation, hover for detail.
  Geometry is fetched from `/ghana-choropleth.json` (328 KB) rather than bundled.
- **Unsourced context attributes became null, not zero.** Sanitation, unsafe-water and
  stagnant-water indices were my estimates for 7 districts and do not exist for 260.
  A `0.0` claims "we measured this and it is zero"; `null` says "unknown". They are now
  optional, the engine already treats a missing signal as unfireable, and confidence
  degrades to `partial`. **This is the honest position and it lowers cholera and diarrhoeal
  scores** until a real WASH dataset (Ghana Statistical Service / DHS) is supplied.

**D10 — Agencies are first-class.** Users carry an agency (GHS, EPA, GMet, NADMO, Assembly)
and a job title. Four demo accounts across three agencies, shown on the sign-in card, in the
top bar, and in the sidebar profile, so it is never ambiguous who is signed in.

---

## 8e. Climate layers on the map

The map carries five layers, switched in place: **Health risk**, **Rainfall**, **Humidity**,
**Peak heat**, **Dust & PM10**. Each has its own sequential colour ramp — the risk ramp is
reserved for risk and never reused for a climate reading.

Above the choropleth sits an animated field: rain streaks fall over wet districts, dust
drifts over hazy ones, heat shimmers, humidity rises. Particle density is driven by the
actual reading, capped at 190 elements so 260 districts stay smooth, and positions are
seeded deterministically so they do not jump on re-render. The whole field is suppressed
under `prefers-reduced-motion`.

**Measured on 3 August 2026 (live Open-Meteo, all 260 districts):**

| Layer | min | max | mean |
| --- | --- | --- | --- |
| Rainfall, 7 days | 12.0 mm | 201.0 mm | 39.8 mm |
| Humidity | 80.5 % | 91.9 % | 85.9 % |
| Peak temperature | 26.2 °C | 34.8 °C | 29.6 °C |
| Dust | 1.4 µg/m³ | 17.6 µg/m³ | 5.1 µg/m³ |

The dust layer renders almost empty, and that is correct: August is the wet season, and
harmattan dust arrives from November. Switching Wa to the `dry_and_dusty` scenario fills it.
An empty layer here is the system telling the truth, not a bug.

---

## 8f. What is still not built

- **3D.** Not attempted. The maps are SVG and render 260 districts plus a live particle
  field at 28 ms first paint. WebGL would add a dependency and bundle weight; it should only
  go in if it earns its place, not as novelty. Worth a decision.
- **Gamification screens.** Backend is complete and tested; these are citizen-facing and
  probably belong in Dawuro.
- **Deployment.** Both stacks still run only on localhost.
- **S1, the WebSocket token in the URL.** Still outstanding, still needs the ticket exchange
  before any real deployment.

---

## 8g2. Nobody waits to be assigned

An earlier version required a coordinator to type in every action, which was wrong twice
over: it invented bureaucracy the agencies do not need, and it left the incident room empty
until someone filled it.

**The prediction is the instruction.** `services/playbook.py` holds a standing mandate per
condition per agency — 13 conditions, all 5 agencies. When the engine raises a condition to
high or severe in a district, every agency with a mandate for it finds its task already
waiting, marked `origin: playbook`, tagged with the condition that caused it, and due on a
date derived from that condition's lag window.

Madina under heavy rain generates **16 tasks across 4 agencies** with no human involved:
GHS 8, District Assembly 5, NADMO 2, EPA 1. Each carries a lead-or-support flag, because
cholera has GHS *and* the Assembly as joint leads while NADMO supports.

Task ids are derived (`district:condition:agency`), so a task keeps its status and its whole
history across recomputation, and disappearing conditions do not orphan work in progress.

**A coordinator is now for exceptions, not the baseline** — adding an action the playbook
does not cover, and overriding a status when an agency cannot.

## 8g3. Append-only transition log

Each action previously stored only its latest change. There is now an immutable
`ActionTransition` per move: from-status, to-status, actor name, actor agency, actor role,
timestamp. `record` only appends; nothing edits or deletes. A test proves a later move never
rewrites earlier entries. The interface renders it as a trail under each task.

**Still not built:** persistence. The log lives in memory and resets with the process, like
every other store. That is a swap behind the existing port, not a rewrite.

## 8g. Who assigns work, and who moves a status

This was unguarded until now: any user with district access could move any action, and
nothing recorded who did it. An EPA officer could close a Ghana Health Service action and
leave no trace. There are now two roles.

**Coordinator** owns the response for their scope.
- Assigns actions to agencies (`POST /incident/{district}/assign`)
- May move **any** status within their scope, including another agency's, because
  coordination sometimes means closing work on someone's behalf
- Seeded: Akosua Mensah (GHS, national) and Kwame Boateng (GHS, Madina district)

**Responder** carries out work.
- May move **only their own agency's** actions
- Cannot assign work to anyone, including themselves
- Seeded: Yaa Ofori (EPA, national) and Ibrahim Alhassan (NADMO, Madina)

Enforcement is in `IncidentService`, not the UI: `update_action` checks
`actor.may_update_action_of(action.agency)` and raises `ActionNotAssignedToYou` (403);
`assign_action` raises `NotACoordinator` (403). The interface disables the buttons a
responder cannot use and says "GHS owns this", so the rule is visible before it is hit,
but the server refuses regardless of what the client sends.

**Every action carries its own history:** `assigned_by`, `assigned_by_role`, `assigned_on`,
then `updated_by`, `updated_by_agency` and `updated_at` once someone moves it. The row
reads "Assigned by Akosua Mensah on 2026-08-01 · Last moved by Kwame Boateng (GHS)".
District scope still applies on top: nobody can touch another district's actions at all.

**Not built:** a full audit log of every transition. Each action holds only its most recent
change. If an agency needs to prove when work started, that needs an append-only trail.

---

## 9. Open questions

**W1 — Design ownership: resolved.** No Figma exists. The design system in §3 is the
source of truth for the dashboard, owned in this repo.

**W2 — Backend URL.** The dashboard needs a deployed API, or every developer runs the
backend locally. Deploying unblocks this and Dawuro at once.

**D9 — A district officer never sees the national map.** This overrides CLAUDE.md §7, which
granted district users a read-only national view. Signing in as a district officer now lands
on `/districts/{their-district}`; the rail reads "My district"; the national back-link is
hidden; and incident and readiness render their district directly with no chooser. The
backend already refused cross-district data — this stops the interface from implying access
the account does not have.

**D8 — The demo toggle is a product feature, not a hidden presenter trick.** The working
doc originally planned a concealed keyboard-shortcut panel. It is now a labelled control on
the district page, because being able to flip to live data in front of a panel is stronger
evidence than any claim of realism.

**W5 — d3-geo winding order cost a whole render.** The first map looked empty: d3-geo reads
polygons spherically, so rings wound the wrong way are read as *the whole globe minus the
shape*. `fitExtent` then scaled the planet into the viewBox and collapsed all seven districts
into a four-pixel dot. `scripts/build-map.mjs` now reverses any ring whose `geoArea` exceeds
half the sphere, and refuses to emit unless the resulting bounds fall inside Ghana. Both
guards are permanent; this class of bug is invisible until you look at the render.

**W3 — Ghana boundaries: resolved.** Using geoBoundaries ADM1 (CC BY 4.0), all 16 current
regions. Pre-projected to SVG paths at build time by `scripts/build-map.mjs`: 269 KB of
source geometry becomes 25 KB of path data, with the runtime projection verified against
d3-geo to 0px before it will emit. District-level boundaries remain unavailable, and §5 is
designed not to need them.

**W4 — Demo hardware.** Screen size and whether the room is bright decides contrast and
default theme. Dark is assumed.


**W6 — CORS origin exactness bit twice.** `backend/.env` pinned `http://localhost:3000`,
so a dashboard opened on `127.0.0.1:3000` failed every request with a bare "Could not
reach the prediction service". Both spellings of both ports are now in `.env` and
`.env.example`. The browser treats them as different origins even though they are the
same machine.

**D11 — Prevention record on the national picture and the district page.** The panel lists
districts by how reliably they closed mandated actions before onset, with the national
averted count in the header. The district card carries the same figures plus the hazards
met in full. Both read `GET /prevention`; nothing on this screen is typed in by a human.


**D12 — `/overview` and `/matrix` are the two unauthenticated screens.** Sign-in links
to the public picture directly. Both read endpoints that expose no district-officer
data, so there is no scope surface to get wrong.

**W7 — Never `pkill` while a Next build is running.** Killing `next-server` mid-build
leaves `.next` with an empty BUILD_ID and no route chunks; `next start` then serves
400 for every asset and the dashboard renders as a permanent spinner with no console
error worth the name. Build to completion (the route table prints), then restart.
