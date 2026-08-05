# CLAUDE.md: ClimaHealth Predict Backend & Engine

This file orients you (Claude Code) to the project and to what we are building together.
Read it fully before writing any code. It defines the product, the architecture, my scope,
the engineering standards, and the exact API surface. When in doubt, this file wins.

---

## 1. Who I am and what I own

I am building the **backend and the prediction engine** for ClimaHealth Predict, plus later
the Next.js web dashboard (separate workstream, not this repo). Teammates own the mobile app,
the Figma design, and documentation. **This repo is the Python backend and engine only.**

My immediate goal: a clean, well-architected, fully tested FastAPI backend that exposes the
API the two front ends will consume, powered by a rules-based prediction engine and a live
climate data feed.

---

## 2. What ClimaHealth Predict is (context)

A climate-health early-warning platform for Ghana. It reads a district's climate conditions
and predicts, **early and before people fall sick**, which health risks are rising, why, the
lag window before cases appear, and who is most affected. It turns a climate signal today into
a ranked, explained health warning for the weeks ahead.

Two front ends consume this backend:
- **Dawuro**, a React Native mobile app for the public (forecast, reporting, gamification).
- **The Agency Command Platform**, a Next.js web dashboard for health agencies.

The backend serves both. It does not render UI.

---

## 3. The core architecture principle

The system has a **brain** and a **mouth**, and they are strictly separate:

- **The brain is a rules engine.** It decides risk from published epidemiological thresholds.
  It is deterministic, reproducible, and explainable. The same inputs always produce the same
  output, and every output can state exactly which conditions caused it. **The brain never
  calls an AI model to decide risk.**
- **The mouth is an AI communication layer.** It takes the engine's structured decision and
  turns it into human, friendly, or local-language text (a citizen forecast, a lesson, an
  officer explanation). It only phrases what the engine already decided. It never decides risk.

This separation is non-negotiable. It is what makes the system defensible and testable. Keep
the engine pure and free of any AI/LLM dependency. The AI layer is an isolated, optional module.

---

## 4. How a prediction flows (the one path to get right)

```
Open-Meteo (live climate data)
        |
        v
  Climate feed  ->  derives features (rain over 7 days, humidity, temp, dust)
        |
        v
  Rules engine  ->  evaluates every disease pathway against the features
        |
        v
  Ranked risks  ->  each: condition, level, score, lag window, vulnerable group, reasons
        |
        v
  FastAPI        ->  serves it to the mobile app and the web dashboard
        |
        +--(optional)--> AI layer turns a risk into friendly / local-language text
```

The prediction (climate -> ranked risk) is **real** and must be correct and reproducible.
The friendly text is a presentation layer on top.

---

## 5. The prediction engine in detail

The engine holds one **pathway** per health condition. A pathway is pure data plus pure logic:

- A **gate**: preconditions that must hold for the pathway to apply at all (for example,
  meningitis only gates on in the dry season and in meningitis-belt districts).
- **Triggers**: individual climate conditions, each with a weight, that raise the risk.
- A **scoring rule**: combine the fired triggers' weights, normalise, apply local context
  multipliers, to produce a score from 0 to 100.
- A **lag window**: how long until cases appear (for example, 2 to 6 weeks).
- A **vulnerable group**: who is most at risk.
- **Reasons**: the human-readable list of which triggers fired and why.

Given a district's features, the engine runs every applicable pathway and returns the results
**ranked by score, highest first**.

### Tier 1 conditions to implement first
- Malaria (rainfall, humidity, stagnant water)
- Cholera (flooding, poor sanitation, unsafe water)
- Meningitis (dust, low humidity, dry season, meningitis-belt gate)
- Diarrhoeal disease (unsafe water, flooding)
- Respiratory / heat illness (dust, air quality, extreme heat)

### The engine must be
- **Pure**: given the same features and district context, always the same output.
- **Explainable**: every risk carries the exact reasons it fired.
- **Data-driven**: pathways are configuration (thresholds, weights, lags), not hard-coded
  branches scattered through the code. Adding a condition means adding a pathway definition,
  not rewriting the engine.
- **Independent**: no web, no database, no AI, no I/O inside the engine. It takes features in
  and returns ranked risks out. This is what makes it trivially testable.

---

## 6. The climate feed

- Source: **Open-Meteo** historical and forecast APIs (free, no key required).
- For each district (identified by coordinates), fetch recent rainfall, temperature, humidity,
  and any available dust/aerosol indicator.
- Derive the features the engine needs (for example, total rainfall over the past 7 days,
  consecutive dry days, humidity average).
- The feed must be **isolated behind an interface** so it can be swapped or mocked. The engine
  and the API must never call Open-Meteo directly; they depend on a feature provider.
- Provide a **demo override**: a way to inject chosen climate values for a district, so a demo
  scenario (heavy rain in Madina) can be triggered deterministically without waiting on live
  weather. This override must go through the same interface, so nothing downstream knows the
  difference.

---

## 7. Access scope (important)

The web dashboard has two access levels, and the backend enforces them:
- **National** users can query any district and see the whole country.
- **District** users are scoped to a single district: they may only query their own district,
  plus a read-only view of the national map.

The backend must know a request's scope and enforce it. A district-scoped request for another
district must be refused. For the demo, two accounts suffice: one national, one Madina district.

---

## 8. The API surface

Build these endpoints. Group the code by area. Response shapes are agreed with the mobile dev
and kept stable; treat them as a contract. All data endpoints are scope-aware (Section 7).

### Access and scope
- `POST /login` -- authenticate, return the user's scope (national, or a district id)
- `GET /me` -- return the current user's scope so the dashboard renders the right view

### Risk and districts
- `GET /districts` -- national: all districts (name, region, coordinates, overall risk level);
  district user: their own district only
- `GET /districts/{id}` -- full detail for one district (climate snapshot + all ranked risks),
  respecting scope
- `GET /risk/{district_id}` -- the ranked risk list: each condition with level, score, lag,
  vulnerable group, reasons, confidence mode
- `GET /forecast/{district_id}` -- citizen-facing daily forecast: top risks in friendly wording
  plus the single action to take today (this is where the AI layer may phrase the text)
- `POST /demo/set-conditions` -- override a district's climate to trigger a demo scenario

### Alerts and agency response
- `GET /alerts` -- active alerts (nationwide or district-scoped)
- `GET /alerts/{id}` -- one alert in full, with explainable reasons and recommended actions
- `GET /incident/{district_id}` -- the incident room: assigned agency actions and their status
- `POST /incident/{district_id}/action` -- update an agency action's status
- `GET /readiness/{district_id}` -- resource readiness: risk vs stock vs reports, and status

### Community reports
- `POST /reports` -- submit a report (type, district, note, optional photo ref, location)
- `GET /reports` -- list reports, filterable by district, scope-aware
- `GET /reports/{id}` -- one report in full

### Gamification (Climate Guardians)
- `GET /guardian/{user_id}` -- a user's profile: points, level, district
- `GET /quiz/daily/{district_id}` -- the daily quiz tied to today's hazard
- `POST /quiz/answer` -- submit an answer, return points and the correct explanation
- `POST /guardian/mission` -- record a completed mission and award points
- `GET /rewards/{user_id}` -- reward ladder status and what the next level unlocks
- `GET /shield/{district_id}` -- a district's shield status and outbreak-averted count

For the demo, some endpoints serve real computed data (risk, forecast, climate) and some serve
seeded data (reports, points, incident actions). Keep the seeded parts clearly separated from
the real engine output in the code, so it is obvious which is which.

---

## 9. Engineering standards (strict)

These are non-negotiable. Hold them on every file you write.

### Clean architecture
- **Layered and decoupled.** Separate clearly: the API layer (FastAPI routers), the service
  layer (use cases), the engine (pure domain logic), and the infrastructure (climate feed,
  any storage). Dependencies point inward: the engine depends on nothing; the API depends on
  services; services depend on the engine and on infrastructure interfaces.
- **Depend on interfaces, not implementations.** The climate feed, any data store, and the AI
  layer sit behind abstractions so they can be mocked and swapped. Use dependency injection.
- **The engine is a pure domain core** with no framework, no I/O, no FastAPI imports.
- **Small, single-responsibility modules.** One clear job per module and per function.
- **Configuration, not magic numbers.** Pathway thresholds, weights, and lag windows live in
  clearly named configuration or definition files, not buried in logic.

### Code style
- **No comments in the code.** The code must be self-explanatory through clear naming and
  structure. If a piece needs a comment to be understood, refactor it until it does not.
  (Docstrings that FastAPI/OpenAPI use to generate API docs are acceptable where they add real
  API value, but keep them minimal. No explanatory inline comments.)
- **Clear, descriptive names** for everything. A reader should understand intent from names.
- **Type hints everywhere.** Full typing on functions and data models.
- **Pydantic models** for all request and response shapes and for internal data structures
  that cross a boundary.
- **Consistent formatting.** Assume ruff and black. Keep imports ordered.
- **No dead code, no TODOs left lying around, no unused dependencies.**

### Testing (required, not optional)
- **Every module ships with tests.** Do not consider a piece done until it is tested.
- **The engine has the deepest tests.** Because it is pure, test it exhaustively: each pathway
  gates correctly, triggers fire correctly, scores compute correctly, ranking is correct,
  reasons are produced. Use table-driven tests with clear cases (for example, Madina rain
  produces malaria high; Wa dust produces meningitis high; malaria falls when it dries out).
- **The climate feed is tested with mocked responses**, never by hitting the live API in tests.
- **The API layer has endpoint tests** (using FastAPI's test client) covering success, scope
  enforcement (a district user refused another district), and error cases.
- Use **pytest**. Keep tests fast, isolated, and deterministic. No test depends on the network.
- Aim for meaningful coverage of behaviour, not a coverage number for its own sake. Every
  branch of the engine's decision logic must be covered.

### Tooling
- Python with **FastAPI**.
- **uv** for dependency and environment management (I use uv).
- **pytest** for tests.
- **ruff** and **black** for lint and format.
- I develop on **Windows** and deploy to a server, so keep everything cross-platform and avoid
  OS-specific paths or assumptions.

---

## 10. The complete scope: everything to build

This is the full job for this repo. I will drive the sequencing myself; treat the list below
as the complete definition of done. Every item ships with tests and follows the standards in
Section 9. Nothing here is optional unless marked so.

### Project foundation
- A clean, layered project structure with clear boundaries (API layer, service layer, pure
  engine, infrastructure). Dependencies point inward.
- uv-managed environment and dependencies; ruff and black configured; pytest configured.
- Pydantic models for every request and response shape and for internal boundary data.
- Dependency injection wiring so the climate feed, the AI layer, and any store are behind
  interfaces and can be mocked and swapped.

### The prediction engine (pure domain core, most heavily tested)
- A pathway abstraction: gate, weighted triggers, scoring rule, lag window, vulnerable group,
  reasons.
- Pathway definitions as configuration (thresholds, weights, lags), not hard-coded branches.
- Implement all Tier 1 pathways: malaria, cholera, meningitis, diarrhoeal disease, and
  respiratory / heat illness.
- The engine takes district features plus district context and returns risks ranked by score,
  each carrying level, score, lag window, vulnerable group, reasons, and a confidence mode.
- The engine is pure: no web, no database, no AI, no I/O. It must be importable and testable
  with zero external dependencies.
- Exhaustive engine tests: gating, trigger firing, score computation, ranking, and reason
  generation, with table-driven cases including at least: Madina rain produces malaria high;
  Wa dust produces meningitis high; malaria falls as conditions dry out.

### The climate feed
- An Open-Meteo client behind a feature-provider interface. The engine and API never call
  Open-Meteo directly; they depend on the interface.
- Feature derivation: rainfall over the past 7 days, consecutive dry days, humidity average,
  temperature, and any available dust indicator, from raw Open-Meteo data.
- A demo override that injects chosen climate values for a district through the same interface,
  so demo scenarios are deterministic and nothing downstream can tell the difference.
- Climate feed tests use mocked responses only; no test hits the live network.

### The AI communication layer (isolated)
- A separate module, behind an interface, that turns a structured engine risk into friendly,
  officer-facing, or local-language text. It never decides risk.
- Used by the forecast endpoint to phrase citizen-facing wording.
- For the demo, support pre-generating and caching this text for the demo districts so nothing
  waits on a live AI call. The engine and API must function fully even if this layer is absent.
- Tests with the AI call mocked; verify the engine decision is passed through faithfully and
  that risk is never altered by this layer.

### Access and scope
- `POST /login` returning a user's scope (national, or a specific district id).
- `GET /me` returning the current user's scope.
- Scope enforcement across every data endpoint: a district user may only access their own
  district; a national user may access any. A cross-district request by a district user is
  refused. Tests must cover this enforcement explicitly.

### The full API surface
Implement every endpoint in Section 8, grouped by area, all scope-aware where applicable:
- Access and scope: `POST /login`, `GET /me`.
- Risk and districts: `GET /districts`, `GET /districts/{id}`, `GET /risk/{district_id}`,
  `GET /forecast/{district_id}`, `POST /demo/set-conditions`.
- Alerts and agency response: `GET /alerts`, `GET /alerts/{id}`, `GET /incident/{district_id}`,
  `POST /incident/{district_id}/action`, `GET /readiness/{district_id}`.
- Community reports: `POST /reports`, `GET /reports`, `GET /reports/{id}`.
- Gamification: `GET /guardian/{user_id}`, `GET /quiz/daily/{district_id}`, `POST /quiz/answer`,
  `POST /guardian/mission`, `GET /rewards/{user_id}`, `GET /shield/{district_id}`.
- Keep clearly separated in code which endpoints serve real engine output (risk, forecast,
  climate) and which serve seeded demo data (reports, points, incident actions).

### Demo districts and data
- Seed the demo districts, including at least Madina (Greater Accra) and Wa (Upper West), each
  with name, region, coordinates, and meningitis-belt flag. Add a few more so the map is
  populated.
- Ensure `POST /demo/set-conditions` can force Madina into a heavy-rain state and Wa into a
  dry-dusty state so the two demo scenarios are reproducible on demand.

### Testing and quality across everything
- Every module ships with tests: unit tests for the engine and feature derivation, mocked
  tests for the climate feed and AI layer, and API tests (FastAPI test client) for every
  endpoint covering success, scope enforcement, and error cases.
- All tests fast, isolated, deterministic, and network-free.
- Meaningful behavioural coverage; every branch of the engine's decision logic covered.
- Clean, self-explanatory code with no comments, full type hints, and consistent formatting.

---

## 11. How to work with me

- Propose the **project structure first** (folders, modules, boundaries) before writing lots of
  code, so we agree the architecture up front.
- Build in **thin, testable increments**. A working, tested slice beats a large untested one.
- I will tell you the order to build things in. When I do not specify, start with the engine
  and the climate feed, since everything depends on them, then the API on top.
- When you make a design decision, state the reasoning briefly in your message to me, not in
  code comments.
- If something here is ambiguous or seems wrong, raise it before building on the assumption.
- Keep the engine pure. If you ever find yourself importing FastAPI or calling an API from
  inside the engine, stop and move it to the right layer.

Build it clean. Build it tested. Keep the brain pure.