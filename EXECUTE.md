Prerequisites (one-time)

# Postgres must be up — it is on your machine right now
pg_isready                 # expect: accepting connections
Backend — terminal 1

cd ~/Desktop/projects/ClimateHealth/backend

# with uv (your normal path)
uv run uvicorn climahealth.api.main:app --reload --port 8000

# or with the venv that already exists, if uv isn't on PATH
source .venv/bin/activate
uvicorn climahealth.api.main:app --reload --port 8000
Check: http://127.0.0.1:8000/health → {"status":"ok"} · docs at http://127.0.0.1:8000/docs

Web — terminal 2

cd ~/Desktop/projects/ClimateHealth/web
npm run dev          # http://localhost:3000
For the demo, run the production build instead — it's much faster in the browser:


npm run build && npm start
Use port 3000 exactly. CORS allows localhost:3000 and 127.0.0.1:3000 only; any other port fails every request with "Could not reach the prediction service".

Logins
Who	Username	Password	Sees
National coordinator (GHS)	national.officer	national-demo-2026	All 260 districts
District officer (GHS, Madina)	madina.officer	madina-demo-2026	Madina only
EPA responder	epa.officer	epa-demo-2026	National, air-quality lens
NADMO responder (Madina)	nadmo.officer	nadmo-demo-2026	Madina, flood lens
Use national.officer for the full picture, nadmo.officer to see that a responder can only move their own agency's actions.