# ClimaHealth Predict — Backend Working Doc

Living plan for the backend and engine. One slice at a time, each slice green before the
next begins. `CLAUDE.md` defines the standards; this file tracks the sequence.

**Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done and tested

---

## Repository layout

```
ClimateHealth/
  CLAUDE.md
  WORKING_DOC.md          this file
  backend/                Python API + engine
  web/                    Next.js agency dashboard (later, separate workstream)
```

Inside `backend/`:

```
climahealth/
  domain/                 pure engine — imports nothing but stdlib + pydantic
  services/               use cases, ports (interfaces), scope enforcement
  infrastructure/         Open-Meteo, AI narrator, stores, event broadcaster, seed data
  api/                    FastAPI routers, schemas, DI wiring, WebSocket
tests/                    mirrors the package tree
```

Dependency direction is inward and enforced by a test: `domain` knows nothing,
`services` knows `domain` + ports, `infrastructure` implements ports, `api` wires it up.

---

## Slices

### 1. Prediction engine `[x]`

Pure domain core. Pathway abstraction, five Tier 1 pathways as configuration, scoring,
ranking, reasons, confidence mode.

- [x] Frozen Pydantic domain models, full type hints
- [x] `SignalName` namespace spanning climate features and district context
- [x] Gate → weighted triggers → normalised score → context multipliers → level
- [x] Malaria, cholera, meningitis, diarrhoeal disease, respiratory/heat illness
- [x] Ranking by score desc, alphabetical tie-break for determinism
- [x] Confidence: `live` / `partial` (missing signal) / `demo` (overridden features)
- [x] Table-driven tests: gating, trigger boundaries, scoring, ranking, reasons
- [x] Demo scenarios: Madina rain → malaria severe; Wa dust → meningitis severe;
      malaria falls as conditions dry out
- [x] Purity test — AST-scans domain modules, fails on any infrastructure import

**Done:** 84 tests green, ruff and black clean.

---

### 2. Climate feed `[x]`

Open-Meteo behind a provider interface, with a deterministic demo override.

- [x] `ClimateFeatureProvider` port in `services/ports.py`
- [x] `District` entity (id, name, region, coordinates, context attributes)
- [x] Seeded districts: Madina, Wa, Accra Metro, Tamale, Kumasi, Cape Coast, Bolgatanga
- [x] Open-Meteo client (httpx) — weather + air-quality endpoints, hourly humidity and
      dust aggregated to daily means
- [x] Pure feature derivation: 7d/14d rainfall, consecutive dry days, humidity mean,
      temperature mean/max, dust, PM10
- [x] Demo override provider wrapping the real one, same interface, `provenance=demo`
- [x] `season_for(day, latitude)` — north and south have different dry seasons
- [x] Tests with mocked HTTP only, plus an autouse fixture that blocks sockets suite-wide

**Done:** 151 tests green. Air-quality failure degrades to `partial` confidence rather
than failing the request; weather failure raises `ClimateDataUnavailable`.

---

### 3. Access and scope `[x]`

- [x] `Scope` model: national, or a single district id
- [x] Seeded users: one national, one Madina district officer
- [x] PBKDF2 password hashing (stdlib, no extra dependency)
- [x] JWT issue and decode, with a minimum secret length enforced at construction
- [x] `POST /login`, `GET /me`
- [x] Single reusable scope dependency `PermittedDistrict` used by every district route
- [x] Tests: cross-district 403, unknown district 404, bad/forged/expired token 401,
      scope-claim tampering rejected

**Done:** enforcement lives in `ScopeGuard` and is reached through one FastAPI dependency.

---

### 4. Risk, districts, forecast, demo `[x]`

Real engine output. This is the critical path.

- [x] `RiskService`: district → provider → engine → ranked risks + overall level
- [x] `GET /districts`, `GET /districts/{id}`, `GET /risk/{district_id}`
- [x] `GET /forecast/{district_id}` — citizen wording + single action for today
- [x] `POST /demo/set-conditions` and `DELETE /demo/set-conditions/{id}`
- [x] TTL cache in front of Open-Meteo so the national map is one call per district
- [x] Error mapping: 401 / 403 / 404 / 503 from typed service exceptions
- [x] Tests: success, scope enforcement, unknown district, demo round-trip, contract shape

---

### 5. AI communication layer `[x]`

The mouth. Phrases decisions; never changes them.

- [x] `RiskNarrator` port
- [x] Template narrator — deterministic, no network, always available
- [x] Citizen and officer phrasing from a phrasebook (config, not logic)
- [x] `CachingRiskNarrator` — pre-primes demo text so nothing waits on a live call
- [x] `FallbackRiskNarrator` — an unreachable model silently degrades to templates
- [x] Tests: risk level, score and reasons pass through unaltered

**Local languages (added):** GhanaNLP Khaya API integration — free tier, purpose-built for
Ghanaian languages. Twi, Ga, Ewe and Dagbani via `?language=tw` on the forecast endpoint.
- [x] `Translator` port; `GhanaNlpTranslator` (Khaya), `NoTranslation`, `CachingTranslator`
- [x] `TranslatingRiskNarrator` — narrates in English, then translates the three text fields
- [x] Activated only by `CLIMAHEALTH_GHANANLP_API_KEY`; absent key changes nothing
- [x] A failed or rate-limited translation returns English **and reports `language: "en"`**,
      so a client is never told text is Twi when it is not
- [x] Tests with mocked HTTP: pair codes, response shapes, 429/503, cache, risk untouched

**Not done:** no LLM narrator. The port and fallback exist so one can be added without
touching the engine or API.

---

### 6. Alerts and agency response `[x]`

- [x] Alerts derived from engine output at `high`/`severe` (real, not seeded), ranked by score
- [x] Alerts carry officer-audience wording, not citizen wording
- [x] `GET /alerts`, `GET /alerts/{id}` — scope-filtered; another district's alert reads 404
- [x] `GET /incident/{district_id}`, `POST /incident/{district_id}/action` (seeded)
- [x] `GET /readiness/{district_id}` — required units scale with risk level, compared to stock
- [x] Tests: scope enforcement on every route, action status transitions, cross-district refusal

---

### 7. Community reports `[x]`

- [x] `POST /reports`, `GET /reports` (filter by district and type), `GET /reports/{id}`
- [x] In-memory store behind a `ReportStore` port
- [x] Reports feed the readiness report's open-report count
- [x] Tests: district user blocked from another district's reports, validation, attribution

---

### 8. Gamification `[x]`

- [x] `GET /guardian/{user_id}`, `GET /rewards/{user_id}` with a five-level ladder
- [x] `GET /quiz/daily/{district_id}` — question chosen by the district's real leading hazard
- [x] `POST /quiz/answer` — points plus the correct explanation; the answer is never leaked
      in the quiz payload, and a question cannot be farmed twice for points
- [x] `POST /guardian/mission` — 409 on a repeat completion
- [x] `GET /shield/{district_id}` — strength from guardians, missions and reports
- [x] Tests: points, promotion, scope (a user always reads their own profile)

---

### 9. WebSockets `[x]`

Domain events only — see decision D1.

- [x] `EventPublisher` port + typed `DomainEvent` envelope (type, district, resource, summary)
- [x] In-memory broadcaster, scope-filtered per connection, thread-safe queue per subscriber
- [x] `/ws` — token in query parameter, scope enforced at connect, 1008 close on a bad token
- [x] Services publish: incident action updated, report submitted, conditions overridden
- [x] Subscribers are released when the socket closes
- [x] Tests with the WebSocket test client, including cross-district filtering

---

### 10. Hardening and handover `[x]`

- [x] Full suite green: **434 tests in under 5 seconds**, ruff + black clean
- [x] Layer-dependency test — nothing points outward
- [x] Domain purity test — AST scan for forbidden imports
- [x] Network-free guard — autouse fixture blocks sockets suite-wide
- [x] `backend/README.md`: run, test, demo script, configuration, real-vs-seeded
- [x] Contract test asserts **every endpoint in CLAUDE.md Section 8** is published, and
      that every district-scoped route returns 401 unauthenticated and 403 cross-district

**Backend complete.** All ten slices done.

---

## Decisions log

**D1 — WebSockets carry domain events, not risk scores.** Open-Meteo updates hourly and
risk moves over days, so streaming scores pushes unchanged numbers. The socket broadcasts
events and clients re-fetch over REST, which stays the source of truth. Avoids a second
contract that drifts from the first.

**D2 — Non-climate signals live in `DistrictContext`.** Sanitation and unsafe-water are not
weather; Open-Meteo cannot supply them. They are static per-district attributes, resolved
through the same `SignalName` namespace so pathways stay uniform config.

**D3 — Confidence mode means data provenance.** `live` = complete Open-Meteo data,
`partial` = a referenced signal was missing, `demo` = features were overridden.

**D4 — Gate failure omits a pathway; a zero score still reports.** Meningitis never appears
outside the belt or in the wet season. Malaria in Wa appears at `low`.

**D5 — Purity is enforced by a test, not by discipline.** An AST scan fails the build if
the domain imports FastAPI, httpx, or any AI SDK.

**D7 — A demo scenario overrides the season as well as the climate.** Discovered by a
failing test: `dry_and_dusty` on Wa produced no meningitis in July, because the gate
correctly closes in the wet season. Calendar-derived season is right for live data but
makes the demo un-runnable outside November–April. Scenarios now carry an implied season
(`heavy_rain` → wet, `dry_and_dusty` → dry) applied through a `SeasonOverrideContextProvider`,
symmetric with the climate override. Live behaviour is unchanged.

**D6 — Seeded vs real is explicit in the tree.** Everything under `infrastructure/seed/` is
demo data. Risk, forecast, climate and alerts are computed by the engine.

---

## D11 — Triggers are graded, not binary

A trigger used to contribute its full weight the moment its published threshold was
crossed. In the August wet season that put every one of the 260 districts on the same
score: malaria 50/100 everywhere, 747 alerts, and a uniformly red map that told an
officer nothing. `TriggerDefinition` now carries an optional `saturation`: the reading at
which that trigger is as bad as it can describe. Crossing the threshold earns half the
weight, the rest is earned across the span to saturation. The published threshold is still
the decision boundary; intensity only separates districts that have all crossed it.

All 65 triggers across the 16 pathways carry a saturation. Effect on live August data:
177 moderate / 46 high / 37 severe, 196 alerts spread over eight conditions.

## D12 — District distinctions come from the action log

`services/prevention.py` derives each district's standing from the append-only incident
log: actions on record, how many closed on or before their due date, how many are overdue.
Three or more actions earns a rating (Exemplary at 90% on time, Reliable at 70%).

A hazard counts as *averted* when every mandated lead action for that condition closed
before its onset window ran out. That is deliberately a claim about the response, never
about cases that did not happen: the platform can evidence the first and never the second.
Exposed at `GET /prevention` and `GET /prevention/{district_id}`.

---

## D13 — Urgency is what the clock says, status is what the agency said

`services/action_urgency.py` derives an urgency for every incident action at read
time: closed, overdue (the onset window ran out), stalled (nobody has touched it in
36 hours), due soon, or on track. Status alone hides the failure mode that matters,
because an action nobody has opened looks identical to one somebody is working on.
The national board and each district room carry the escalation count, and every row
shows when it last moved.

## D14 — A public overview with no login

`GET /public/overview` serves the national warning picture unauthenticated: how many
districts are raised, which conditions, and the twelve most severe with the leading
condition's own onset window and the group most at risk. Climate-derived risk is
computed from open weather data against published thresholds, and a household cannot
act on a warning it is not allowed to read. Agency workload, community reports and
the action log stay behind the login.

---

## D15 — Tier A is a real seam, trained on synthetic data and honest about it

Proposal section 6.3 promises three tiers. Tier A now exists rather than being a
label nothing sets. `domain/model/logistic.py` holds a pure logistic model per
condition; `scripts/train_tier_a.py` trains it offline and writes the coefficients
to `domain/model/trained.py` as committed configuration, the same way thresholds
are configuration. Five conditions are modelled: malaria, cholera, meningitis,
diarrhoeal disease and respiratory heat illness, at 73–79% holdout accuracy.

Three constraints keep it defensible:

- **It refines, it does not decide.** The rules produce the score. The model
  adjusts it by at most 15 points either way, so it can move a number but cannot
  carry a pathway across a level boundary on its own.
- **It only speaks above the coverage floor.** Below 50% readable signal weight the
  answer stays Tier C baseline and the model is not consulted, because there is too
  little to read for a learned model to add anything honest.
- **It says so.** A modelled risk reports Tier A and carries a reason line naming
  the adjustment, the sample count and the holdout accuracy. No score moves silently.

The training set comes from a documented latent process, not observed cases, because
Ghana surveillance line-lists were not available to us. The process is deliberately
smooth where the rules are stepped, so the model learns how risk rises *between*
published thresholds, which is exactly what a step function cannot express.
Swapping in real case data is a training run, not an engine change.

This is not a contradiction of the brain/mouth rule in CLAUDE.md section 3. The rule
bars an LLM from deciding risk, and that still holds absolutely. This is a committed
set of coefficients evaluated by pure arithmetic: deterministic, inspectable in the
repository, and bounded.

---

## D16 — SMS and USSD through Moolre

`GET /outreach/sms/{district}` composes the district's warning; `POST` broadcasts it.
`POST /ussd/moolre` is the real callback Moolre invokes when somebody dials the
shortcode, driven by a pure state machine in `services/ussd.py` (language, region,
district, answer) that pages long lists eight at a time.

Four decisions worth keeping:

- **Preview is the default.** `CLIMAHEALTH_SMS_DELIVERY=preview` composes and records
  but never sends. A message that has gone cannot be recalled and costs money per
  recipient, so sending takes a deliberate setting, not merely a present credential.
- **Broadcasting is coordinator-only**, enforced in the service, not the router.
- **One risk, one action, no link.** The leading risk is the whole message; the rest
  of the ranking stays in the app. A test asserts every one of the 16 conditions fits
  a single segment, because a second segment doubles the cost of a national broadcast.
- **GSM-7 versus UCS-2 is modelled.** One non-GSM character, such as the Twi ɔ,
  moves the whole message to UCS-2 and cuts a segment from 160 characters to 70. The
  preview reports the encoding and the segment count.

Verified against the live API: the VAS key authenticates, and `/open/sms/query`
reports `Klare` **Approved** and `ClimaHealth` **Not Found**. The preview surfaces
that status, so an unapproved sender is caught before a broadcast rather than by one.
We send under **Klare**, the approved sender on this account, and that is now the
code default too rather than only an `.env` value: a name that is not registered is
rejected by the network, so defaulting to the product name would be defaulting to
failure. Registering ClimaHealth later is a dashboard task plus one setting.

The message still signs off `-ClimaHealth`. The sender ID is the technical
from-address; the signature is what tells a citizen which service is warning them,
and those do not have to be the same string.

## D17 — Emergency readiness carries a deadline

`ReadinessStatus` gains `EMERGENCY` below 20% coverage, separate from critical
because they call for different actions: critical means order more, emergency means
the shortfall lands before the cases do. Every shortfall now carries
`hours_to_dispatch`, measured against the soonest onset window of anything raised in
that district. A shortfall does not matter in the abstract; it matters against the
date the ward fills up.

## D18 — Coastal proximity, computed rather than declared

`scripts/add_coast_distance.py` measures every district centroid against a polyline
of the Ghanaian coast and writes `distance_to_coast_km` into the seed. 50 of 260
districts fall within 25 km of the sea. Cholera and leptospirosis carry a coastal
multiplier: saline intrusion and tidal flooding change what the same rainfall means.

This also fixed a quiet bug. `flood_prone` was never set from data, so every district
defaulted to false and the flood multipliers had been dead the whole time. Districts
within 10 km of the sea are now flood-prone on tidal and storm-surge grounds. Riverine
flood plains stay false: that needs a hydrology source we do not hold, and a guess
would be worse than a gap.

## D19 — The event stream takes a ticket, not the bearer token

A browser cannot set headers on a WebSocket handshake, so the token rode in the query
string, where it landed in server logs and proxy history. `POST /ws/ticket` now
exchanges the bearer token for a single-use credential that expires in 30 seconds, and
`/ws` accepts nothing else. The web client fetches a fresh ticket per attempt,
including reconnections, because a spent one is refused by design.

## D20 — The open endpoint is rated

`/public/overview` evaluates all 260 districts without a credential, which turns one
request into a lot of work. A per-process sliding window allows 30 requests a minute
per caller. Per-process is the right weight for one deployment; behind more than one,
this wants a shared cache.

---

## D21 — The climate cache is persistent, because the feed has a daily ceiling

Found by exhausting it: Open-Meteo enforces a **daily** request limit, and once it
is spent every live endpoint returns 503 until it resets at UTC midnight. The cache
already served last-good readings on failure, but it lived only in memory, so a
restart during an outage left the platform with nothing to say. That is the one
thing an early-warning system must not do.

Readings now write through to a `climate_readings` table and are loaded on start.
Tested directly: a provider built over a dead feed but a warm store still answers,
and the same provider without a store raises.

Two operational notes:
- 260 districts is roughly 6 to 12 batched calls per refresh; at a 180-minute cache
  that is comfortable, but repeated restarts with a cold cache are what burn quota.
- Demo scenarios never touch the feed, so `POST /demo/set-conditions` keeps working
  through an outage. That is the safety net for a live demonstration.

---

## Open questions

**Q1 — Pathway thresholds need an epidemiological review.** They are my reading of the
literature, not cited values. All in `domain/pathways/definitions.py`, one readable file.
Tests assert level bands rather than exact scores, so tuning will not break them.

**Q3 — Twi is written but unreviewed.** The citizen forecast is now composed in Twi
rather than translated: `infrastructure/ai/twi_phrasebook.py` holds condition names, level
words, the sentence frame and an action for all 16 conditions, and `TwiRiskNarrator` sits
ahead of machine translation because wording written for a language beats wording pushed
through one. Every response carries a `wording` field, and Twi reports
`curated_unreviewed` until a Twi speaker has been through it. The app shows that to the
reader. **What is still needed from a person:** that review, and then the same for Ga,
Ewe and Dagbani.

Superseded, kept for the record: **Local-language forecasts need a native speaker.** The narration layer carries a
`language` field and the phrasebook is keyed by it, so adding Twi or Dagbani is a data
change. I have not written those entries: inventing health advice in a language I cannot
verify is worse than leaving the seam open. Who on the team can supply them?

**Q2 — Persistence.** Everything is in-memory behind ports, which is right for the demo.
Say the word if a real store is needed before then; the ports make it a swap.
