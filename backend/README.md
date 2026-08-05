# ClimaHealth Predict — Backend & Engine

Climate-health early-warning API for Ghana. A deterministic rules engine turns a district's
climate conditions into ranked, explained health risks for the weeks ahead.

## Run it

```bash
uv sync
uv run uvicorn climahealth.api.main:app --reload
```

Interactive API docs: <http://127.0.0.1:8000/docs>

## Test it

```bash
uv run pytest          # 449 tests, no network, under 5 seconds
uv run ruff check .
uv run black --check .
```

No test touches the network — an autouse fixture blocks sockets across the whole suite.

## Demo accounts

| Username           | Password             | Scope           |
| ------------------ | -------------------- | --------------- |
| `national.officer` | `national-demo-2026` | All districts   |
| `madina.officer`   | `madina-demo-2026`   | Madina only     |

## The two demo scenarios

```bash
TOKEN=$(curl -s localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"national.officer","password":"national-demo-2026"}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# Madina: heavy rain -> malaria severe
curl -s localhost:8000/demo/set-conditions -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"district_id":"madina","scenario":"heavy_rain"}'
curl -s localhost:8000/forecast/madina -H "Authorization: Bearer $TOKEN"

# Wa: dry and dusty -> meningitis severe (works in any month)
curl -s localhost:8000/demo/set-conditions -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"district_id":"wa","scenario":"dry_and_dusty"}'
curl -s localhost:8000/risk/wa -H "Authorization: Bearer $TOKEN"

# Back to live Open-Meteo data
curl -s -X DELETE localhost:8000/demo/set-conditions/madina -H "Authorization: Bearer $TOKEN"
```

A demo scenario overrides the season as well as the climate, so `dry_and_dusty` produces
meningitis in July even though the real meningitis gate is closed in the wet season.

## Architecture

```
climahealth/
  domain/            the engine — pure, no I/O, no framework, no AI
  services/          use cases and ports (interfaces)
  infrastructure/    Open-Meteo, narrator, translation, stores, events, seed data
  api/               FastAPI routers, schemas, DI wiring, WebSocket
```

**The brain and the mouth are separate.** The engine decides risk from published
epidemiological thresholds and can always say exactly which conditions caused its answer.
The narration layer only phrases what the engine already decided; it never changes a level,
a score, or a reason. Two tests enforce this: one AST-scans the domain for forbidden
imports, another checks that no layer points outward.

**Adding a disease** means adding one `PathwayDefinition` in
`domain/pathways/definitions.py` — a gate, weighted triggers, a lag window, a vulnerable
group. No engine code changes.

## Configuration

Configuration is read from a `.env` file in this directory, or from real environment
variables (which win over the file). Every value has a working default, so the API runs
with no `.env` at all.

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # generate a token secret
```

| Variable                            | Default                | Effect                                |
| ----------------------------------- | ---------------------- | ------------------------------------- |
| `CLIMAHEALTH_TOKEN_SECRET`          | a development secret   | JWT signing key; min 32 bytes         |
| `CLIMAHEALTH_TOKEN_LIFETIME_HOURS`  | `12`                   | How long an access token stays valid  |
| `CLIMAHEALTH_CORS_ORIGINS`          | `localhost:3000,:8081` | Comma-separated allowed origins       |
| `CLIMAHEALTH_GHANA_NLP_API_KEY`     | unset                  | Enables Twi/Ga/Ewe/Dagbani forecasts  |
| `CLIMAHEALTH_CLIMATE_CACHE_MINUTES` | `30`                   | Per-district Open-Meteo cache window  |

**Set `CLIMAHEALTH_TOKEN_SECRET` before deploying.** The default is a known public string,
and the app logs a warning at startup while it is in use. Invalid configuration (a short
secret, a zero token lifetime) fails at startup rather than at the first request.

`.env` is gitignored; `.env.example` is the documented template and is committed.

## Local languages

`GET /forecast/{district_id}?language=tw` returns Twi (also `gaa`, `ee`, `dag`) via the
free [GhanaNLP Khaya API](https://translation.ghananlp.org/). Without an API key the
endpoint still works and returns English.

If a translation call fails or is rate-limited, the response falls back to English **and
reports `language: "en"`** — a client is never told text is Twi when it is not.

## Real versus seeded

Real, computed by the engine on every request:
`/risk`, `/forecast`, `/districts`, `/alerts`, `/readiness` (demand side), `/quiz/daily`
(follows the district's actual leading hazard).

Seeded demo data, all under `infrastructure/seed/`:
incident actions, resource stock levels, community reports, guardian profiles, quiz bank,
outbreak-averted counts.

## WebSocket

`ws://localhost:8000/ws?token=<jwt>` broadcasts domain events — a report submitted, an
incident action updated, a district's conditions overridden. Clients re-fetch over REST;
the socket does not stream risk scores, because they change on a scale of days.

Events are scope-filtered at connect: a Madina officer's socket never receives Wa events.
