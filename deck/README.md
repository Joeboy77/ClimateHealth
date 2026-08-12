# Pitch deck

`ClimaHealth-Predict.pptx` — 17 slides, 16:9, white background, two colours.
Built by `build_deck.py` so every number lives in one place and can be corrected
in one place.

```bash
cd backend && uv run python ../deck/build_deck.py
```

Editing the .pptx in PowerPoint is fine; a rebuild overwrites it.

## Running order

**Core, about 5 minutes.** Speaker notes are on every slide.

| # | Slide | Time |
|---|---|---|
| 1 | Title | 10s |
| 2 | The problem: 6.7m cases, 11,635 deaths | 35s |
| 3 | The gap: the lag window | 35s |
| 4 | Our solution: three front doors | 30s |
| 5 | The brain: rules, not a guess | 40s |
| 6 | National picture (live screenshot) | 35s |
| 7 | Agency views (EPA on dust) | 25s |
| 8 | The Ɔhwɛfoɔ validation loop | 40s |
| 9 | The app | 20s |
| 10 | Accessibility | 35s |
| 11 | The NHIS renewal queue | 25s |
| 12 | Rewards that are fundable | 30s |
| 13 | Reach: app, USSD, SMS | 25s |
| 14 | Three criticisms, three answers | 40s |
| 15 | Close | 15s |

**Hold back for Q&A:** 16 (sources) and 17 (architecture and known limits).

If you are running over, cut slide 9 first, then 7.

## Screenshots

`screenshots/` is what the slides embed. Web shots were captured from the running
dashboard in light theme at 1440x900. App shots came from the phone; the originals
are kept in `screenshots/originals/`.

| File | Screen |
|---|---|
| `w1-national.png` | National picture, 51/260 districts |
| `w2-renewals.png` | NHIS renewal queue |
| `w3-epa.png` | EPA signed in, dust layer active |
| `m1-home.png` | Home: Ayawaso West, moderate malaria risk |
| `m2-quiz.png` | Quiz question 2, wrong answer with the teaching |
| `m3-finish.png` | Run finished, 4 of 5, +85 XP |
| `m4-report.png` | Report a hazard |
| `m5-twi.png` | The same forecast in Twi |
| `m6-language.png` | Language picker, on the accessibility slide |

## Sources

Every figure on the deck is on slide 16 with its source:

- Malaria burden: WHO, *World Malaria Report 2024* — 6.7m cases, 11,635 deaths in Ghana
- NHIS coverage: National Health Insurance Authority, 2025 — 18.5m active members, ~56%
- NHIS premium: GHS 7.20–48 a year by income band, ~GHS 30–50 informal
- Mobile reach: GSMA Intelligence / DataReportal, *Digital 2025 Ghana* — 38.3m connections, 69.9% internet use
- Climate data: Open-Meteo, live in the product
- Boundaries: geoBoundaries, CC BY 4.0

## Honesty notes

Two things on the deck are seeded rather than live, and the slides say so:

- The six Guardians on the renewal queue are seeded demonstration accounts. The
  caption on that slide states it.
- The EPA dust map is flat because it is the wet season and dust is near zero
  nationally. It proves the layer switches, not that dust is high today. Run
  `POST /demo/set-conditions` to put a northern district into a dry, dusty state
  before presenting if you want that slide to carry more.

Everything else, including the 51/260 figure and the map, is live engine output.
