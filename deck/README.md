# Pitch deck

`ClimaHealth-Predict.pptx` — 13 slides, 16:9, white background. Built by
`build_deck.py` so the numbers live in one place.

Rebuild after any edit to the script:

```bash
cd backend && uv run python ../deck/build_deck.py
```

Editing the .pptx directly in PowerPoint is fine; just know a rebuild overwrites it.

## Screenshots

`screenshots/` holds what the slides embed. Web shots were captured from the running
dashboard in light theme at 1440x900.

Still needed, as phone screenshots (portrait, ideally 1170x2532 or similar):

| File | Screen |
|---|---|
| `m1-home.png` | Home: today's warning with the conditions strip underneath |
| `m2-quiz.png`  | A quiz question mid-run, showing points and the streak flame |
| `m3-report.png`| Report screen scrolled to "What you have reported", showing a progress bar |

Drop them in with those exact names and rebuild. Until then those three appear as
labelled grey placeholders, so nothing is silently missing.

## Running order, 5 minutes

1. Title, 15s
2. The gap: the lag window, 40s
3. The brain: rules not guesses, 45s
4. National picture, 40s
5. Agency views, 30s
6. The Ɔhwɛfoɔ loop, 45s
7. Mobile, 15s — cut this first if you are over
8. NHIS rewards, 40s
9. Reach: app, USSD, SMS, 30s
10. Three criticisms answered, 45s
11. Close, 15s

Slides 12-13 are backup for Q&A. Speaker notes are on every slide.
