# ClimaHealth Predict — Proposal vs Build

Audit of what exists against `ClimaHealth_Predict_Full_Proposal (1).docx`, judged two ways:
as a **software engineer** preparing for a next round, and as a **judge holding the proposal**
while watching the demo.

Section references are to the proposal.

**Verdict:** the engine and the Agency Command Platform are strong and largely real. But the
proposal sells a **four-part system** — predict, coordinate, educate, reward — and only the
first two exist. Roughly **half the document has no running code**, including both features
the proposal itself ranks as its most original (§19.2, §19.3).

---

## P0 — Promises a judge can check and will find unmet

### 1. Dawuro does not exist
§9–§12 and §17 commit to the public application: daily forecast, Community Watch reporting,
Climate Guardians, quiz duel, mission flow, points record, simulated insurance redemption,
one Anansi mini-game. The backend serves `/guardian`, `/quiz/daily`, `/quiz/answer`,
`/guardian/mission`, `/rewards`, `/shield` — all tested — and **nothing consumes any of it.**

This is not a missing screen. §11 and §12 are the movement and the business model. §19.4
("Converting Engagement Into Real Healthcare") and §15 (who pays) both rest on it.

**Fix:** build Dawuro, even thin. Three screens beat zero: forecast, report, guardian.

### 2. Community reports do not reach the engine
§6.2 calls verified reports "a first-class data layer". §10: "Every verified report feeds
directly into the Signal-to-Syndrome Engine." §22 closes the whole document on it — "a
schoolgirl's photograph of stagnant water can trigger a coordinated national response."

**Reports currently only increment a counter on the readiness screen.** They do not alter a
single risk score. Verified by grep: zero references to any report store in the engine or
risk path.

**Fix:** add a `community_signal` input to `DistrictContext` derived from verified reports
(stagnant-water reports raise the stagnant-water index; flooding reports raise flood
exposure). This is the demo's emotional climax and it is currently theatre.

### 3. No report verification pipeline
§10 specifies location tagging, photo upload, **corroboration from multiple reports**,
**verification by health officers or trusted volunteers**, and **priority scoring**.
§14 specifies points for *verified* reports only, and a per-user **accuracy score** that
decays with false reports.

Built: location, a photo *reference* field. Missing: actual upload, corroboration,
verification workflow, priority scoring, accuracy score. Anyone can submit anything and it
counts immediately.

### 4. The confidence model contradicts §6.3
Proposal promises three named modes — **model**, **threshold**, **baseline** (the last
"marked indicative only"). We ship `live` / `partial` / `demo`, which describes *data
provenance*, not which engine tier produced the answer.

§19.6 lists "A System That States Its Own Confidence" as a headline innovation, so the
naming being wrong is a **scored claim**, not a detail.

**Fix:** `ConfidenceMode` becomes `MODEL | THRESHOLD | BASELINE`; keep `provenance`
(`live | demo`) as the separate field it already is.

### 5. The Tier A machine-learning layer is not even architected
§6.4, verbatim: "the Tier A machine-learning layer architected and demonstrated on available
and synthetic data." There is **no model, no port for one, no synthetic demonstration**.

The proposal is honest that real case data is unavailable — good. But it commits to
*architecting and demonstrating* the layer. A judge who reads §6.1's three-tier table and
then finds only Tier B will mark the difference.

**Fix:** a `RiskModel` port behind the engine, one trained-on-synthetic estimator, and the
tier surfaced per district. Small, and it converts a gap into the proposal's own claim.

### 6. Lag windows contradict the proposal's own Matrix
The engine stores whole weeks. §3 gives days for the fast conditions:

| Condition | Proposal §3 | Built | Match |
| --- | --- | --- | --- |
| Cholera | 2–10 days | 1–3 weeks | no |
| Diarrhoeal | 3–14 days | 1–3 weeks | no |
| Leptospirosis | 5–14 days | 1–3 weeks | no |
| Typhoid | 1–3 weeks | 1–4 weeks | no |
| Malaria | 2–6 weeks | 3–8 weeks | no |
| Meningitis | 1–4 weeks | 2–6 weeks | no |
| Dengue | 2–6 weeks | 1–4 weeks | no |

**Every fast pathway is wrong, and cholera — the one with a real 2024 outbreak behind it —
is overstated by up to a week.** For a tool whose entire value is *timing*, this is the most
damaging inconsistency in the build.

**Fix:** `LagWindow` in days, not weeks; reconcile all 13 against §3.

### 7. Role-based agency views do not differ
§8 tabulates what each of nine agencies sees. §17 requires "role-based views for at least
three agencies". We model agency identity and permissions correctly — but **every agency
sees an identical dashboard.** Zero agency-conditional rendering on the national or alerts
pages.

An EPA officer should land on air quality, dust and fire hotspots. NADMO on flood and heat.
GMet on forecast-to-outcome feedback. Right now they all land on the same map.

### 8. District distinctions and Outbreak Averted are absent from the map
§11.2 is the proposal's **second-ranked innovation** (§19.2). §17 requires "district
distinctions" on the map. Backend holds `outbreaks_averted`; there is no distinction
concept, no district competition, no UI.

### 9. Conditions the proposal names are missing
Tier 1 and 2 gaps, by the proposal's own staging (§5):

- **Child undernutrition** — in the executive summary, §3.5, *and* §7.2's district table
  (Bawku). Absent.
- **Maternal heat outcomes** — miscarriage, stillbirth, preterm birth. §3.2, Tier 2. Absent,
  despite §1 citing the 12–15% per-degree miscarriage figure as headline evidence.
- **Air-pollution cardiorespiratory** — §3.4 is an entire climate driver (stroke, IHD, lower
  respiratory infection) with **no pathway at all**. §1 calls air pollution Ghana's *second
  leading risk factor for death*.
- **Asthma / COPD as distinct rows** — §3.3 separates them; we lump both into
  `respiratory_heat_illness`, which *also* overlaps our own `heat_stroke`.

Meanwhile we added **Lassa fever** and **trachoma**, which appear nowhere in the proposal.
Not wrong, but a judge may ask why unlisted conditions were built while the proposal's own
Tier 2 was skipped.

### 10. One data source out of eleven
§6.2 names Open-Meteo, NASA POWER, CHIRPS, OpenAQ, FIRMS, Copernicus/GloFAS, MODIS/FEWS NET,
WorldPop, WHO GHO, and DHIS2 as the primary long-term integration. **Only Open-Meteo is
wired.** Consequences:

- No **OpenAQ** → §3.4 air pollution cannot be assessed at all
- No **FIRMS** → §3.7 bushfire smoke cannot be assessed
- No **flood extent** → flooding drives six conditions in §3.1 and is inferred from rainfall alone
- No **drought/NDVI** → §3.5 undernutrition has no signal
- No **WorldPop** → housing density, named in §4's contextual weighting, is unavailable

### 11. No SMS / USSD / WhatsApp / voice simulation
§17 requires "a simulation of message and menu-code alerts". §9 and §13 make multi-channel
delivery central to the inclusion argument. Nothing exists.

### 12. Named demo districts are missing scenarios
§7.2 and §18 build the demo on **Ada East** (the real October 2024 cholera origin) and
**Tamale Metro** (harmattan). Both exist among the 260 districts, but only Madina and Wa have
scenario presets. The proposal's chosen evidence districts cannot be demonstrated on cue.

---

## P1 — Engineering gaps for a next round

### 13. The web has zero automated tests
746 backend tests. **0 frontend tests, no runner configured.** For "we are going to the next
round", this is the single largest engineering weakness. Every UI regression is caught by me
looking at a screenshot.

**Fix:** Vitest + Testing Library for the risk/climate/agency logic modules and the
permission-dependent rendering; Playwright for sign-in → district → status-change.

### 14. Nothing persists
Every store is in-memory. A restart loses all reports, action statuses, guardian points and
the entire append-only transition log. The log is the accountability record §8 and §19.5 sell
— an accountability record that evaporates is not one.

**Fix:** SQLite behind the existing ports. They were built for this.

### 15. Not deployed
Neither stack is reachable. Nothing is showable, and Dawuro cannot be built against it.

### 16. Access token in the WebSocket URL
Lands in browser history and server logs. Needs a 30-second single-use ticket exchange.

### 17. No CI
No automated run of 746 tests, ruff, black, typecheck, design audit on change.

### 18. Points and reports are farmable
`POST /reports` and `POST /quiz/answer` have no rate limiting. §14 promises defences against
manufactured reports; the accuracy score that backs it does not exist.

### 19. Contextual weighting is largely inert
§4 layer 3 names drainage/sanitation, housing density, immunization coverage, meningitis
belt, coastal proximity, clinic capacity, historical case patterns. **Only the meningitis
belt works.** Sanitation, water and stagnant-water are honestly `null`; the rest were never
modelled. Coastal proximity is derivable from the geometry we already hold and would unlock
§3.6 — cheap win.

### 20. No public overview page
A judge opening the URL hits a login wall. There is no page explaining the platform, the
engine, or the Matrix without credentials.

---

## P2 — Corrections and removals

### 21. The risk score reads as a probability but is not one
§4 and §7.3 present risk as "78 percent". Our 0–100 is a **normalised fired-trigger weight**
— not a probability, not a calibrated confidence. Presenting it beside the word "percent"
would misrepresent it.

**Fix:** label it "risk score / 100" everywhere, keep confidence separate, and say plainly in
the UI what the number is. Honesty here is a feature, per §6.3's own argument.

### 22. Proposal vocabulary is absent from the product
The proposal brands the engine the **Signal-to-Syndrome Engine** and the knowledge base the
**Climate-Health Intelligence Matrix**. The UI uses neither phrase. Cheap alignment, and the
Matrix deserves its own browsable screen: it shows 13 pathways of depth even when only 4 are
firing, which is exactly the "this is a system, not a demo" signal judges look for.

### 23. Remove or justify the overlapping pathways
- `respiratory_heat_illness` double-counts heat with `heat_stroke` and merges §3.3's separate
  asthma and COPD rows. Split into **airway exacerbation** (dust/PM driven) and keep heat
  illness separate.
- `trachoma`'s 8–24 week lag makes it a poor fit for an *early-warning* product, and it is
  not in the proposal. Keep only with a stated rationale.

### 24. Thresholds remain unreviewed, now across 13 conditions
Still my reading of the literature, not cited values. This is the only gap where being wrong
has clinical meaning, and it has grown. It needs a named clinical reviewer before any round
that includes health professionals.

### 25. Accessibility is claimed far beyond what is built
§13 is one of the strongest sections and §19.7 scores it. The dashboard has designed focus
states, labelled controls, `prefers-reduced-motion` and `prefers-contrast`. It does **not**
have a screen-reader-verified flow, large-text mode, or simplified symbol mode. Most of §13
targets Dawuro — but nothing should contradict it, and the claims need something behind them.

---

## Recommended order

1. **Lag windows in days, reconciled to §3** — cheapest fix, largest credibility gain
2. **Confidence modes renamed to model/threshold/baseline**
3. **Reports feed the engine** — makes the closing demo story real
4. **Dawuro, three screens** — forecast, report, guardian
5. **Frontend tests + CI**
6. **Air-pollution pathway + OpenAQ** — unlocks a whole climate driver
7. **Role-based agency landing views**
8. **District distinctions and Outbreak Averted on the map**
9. **SQLite persistence**
10. **Tier A model architected on synthetic data**
11. **Undernutrition and maternal-heat pathways**
12. **Ada East and Tamale scenarios**

Items 1–3 are corrections to things that are currently *wrong*, not additions. They should
go first regardless of what else is chosen.
