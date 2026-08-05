# Dawuro — the public mobile application

Working doc for the React Native app. Companions: `WORKING_DOC.md` (backend, complete),
`WEB_WORKING_DOC.md` (agency console, complete).

**The bar:** a judge picks up the phone and assumes a product design team shipped this.
Not a hackathon build, not a template, and nothing that reads as generated.

**Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done and reviewed

---

## 1. What Dawuro is

Dawuro is the gong-gong: the town crier's bell that warned Ghanaian communities for
generations. The proposal's own framing is the design brief — *"People already check the
weather every day. Dawuro gives Ghana a health-weather habit: one glance, one action,
every day."*

So this is **not a small version of the agency console**. The console is an operations
instrument for officers on a desk. Dawuro is a daily habit on a phone, in a hand, often
outdoors, often on a cheap device, often by someone who is not reading English.

An ordinary person opens it and gets three things, in this order:

1. **Am I at risk today?** — one level, one condition, one glance.
2. **Why, and how long do I have?** — plain language, no jargon, no score out of 100.
3. **What do I do about it today?** — exactly one action, doable today, free.

Anything that does not serve that sequence goes below the fold or does not ship.

### The five things it does (proposal §9–§12)

| Area | What the citizen does | Proposal |
| --- | --- | --- |
| **Today** | Reads the daily district health forecast and the one action | §9 |
| **Report** | Sends a photo of a blocked drain or stagnant water | §10 Community Watch |
| **Learn** | Gets a one-minute lesson *because* it rained, then a quiz | §11.1 |
| **Guardian** | Earns points, climbs the ladder, redeems health cover | §11.3, §12 |
| **District** | Sees their district's shield, distinction and neighbours | §11.2 |

---

## 2. Why this is not the console, visually

Both products read the same engine, so a severe risk must look severe in both. Everything
else should differ, because the reader and the setting differ.

| | Agency console | Dawuro |
| --- | --- | --- |
| Read in | An office, on a large screen | A hand, outdoors, in sunlight |
| Session | Twenty minutes, comparing districts | Eight seconds, once a day |
| Density | High. Tables, ranked lists, small type | Low. One idea per screen, large type |
| Surface | Cool graphite and teal, dark by default | Warm clay and ink, light by default |
| Tone | "Cholera 81.6, severe, 2–10 days" | "Cholera risk is high. Boil your water today." |
| Numbers | Scores, coverage ratios, hours | Almost none. Words and a dial |

**Shared, non-negotiable:** the four risk colours and their meanings. A citizen who sees
red and an officer who sees red are looking at the same fact.

### Visual direction

Warm, plain and confident. The reference points are a good weather app and a well-made
public-health poster, not a SaaS dashboard and not a game.

- **Canvas:** warm off-white clay, not grey, not pure white. Reads well in sunlight.
- **The opening palette:** a deep forest field (`#0A3B35`) with a cream mark and warm
  ochre rings. Green and ochre on warm cream is a Ghanaian palette arrived at through
  material rather than through flags and kente prints, which is what "make it African"
  produces when nobody is thinking.
- **Two typefaces.** Fraunces carries the verdict: a warm, slightly old-style serif with
  the authority of a public notice. Inter carries everything else, because a warning has
  to stay legible at small sizes on a cheap screen and a serif does not.
- **One hero per screen.** On Today that is the risk dial and the action card. Nothing
  competes with it.
- **Type does the work.** A large, quiet display face for the verdict; everything else
  small and calm. No card grids of equal weight.
- **Ghanaian without costume.** Warmth, a clay palette and the Dawuro bell mark. No kente
  wallpaper, no adinkra scattered as decoration, no flag gradients. Those are what a
  generator produces when asked to make something "African".

---

## 3. Non-negotiable quality rules

Carried over from the console and adapted for a phone. The banned list is the important
half: these are the tells that a machine made it.

### Banned

| Banned | Instead |
| --- | --- |
| Emoji as interface | One icon set, consistent weight |
| Purple/violet gradients, gradient text | Flat, considered colour with semantic meaning |
| Glassmorphism, neon glow, heavy blur | Solid surfaces, hairline borders, honest elevation |
| Everything rounded-3xl with a drop shadow | A radius and elevation scale used deliberately |
| Default React Native styling left visible | Every control designed, including the ones we didn't build |
| Bounce/spring on things that are not physical | Springs for gestures, curves for state |
| Animating everything in on mount | Motion only where it carries meaning (§6) |
| "Welcome back 👋", "Dashboard", "My Stats" | "Today in Madina", "Your Guardian card" |
| Confetti and trophy animations for everything | Recognition sized to what was actually achieved |
| Lorem-grade filler ("Stay safe out there!") | Copy a health worker would say out loud |
| A score out of 100 shown to a citizen | A level, a word, and a time window |
| Stock illustrations of doctors and cities | Data, type and the district's own shape |

### Required

- **One action per screen.** If a screen has two primary buttons, it is two screens.
- **Thumb-reachable.** Every primary action sits in the bottom third. Nothing critical
  in the top corners.
- **Real states everywhere**: loading (skeleton in the final layout), empty (says what
  would appear and how to get it), error (says what failed, offers retry), offline
  (says what is cached and when it was fetched).
- **Offline is normal, not an error.** Last-good forecast is shown with its timestamp.
  A report written offline is queued and sent later, and the app says so.
- **Colour is never the only carrier.** Every risk level pairs colour + word + icon.
- **British English**, matching the backend strings ("diarrhoea", "prioritise").
- **Tabular numerals** anywhere a number changes in place (points, countdowns).

---

## 4. Accessibility is a feature here, not a checklist

Proposal §13 is unusually strong on this and it is a genuine differentiator: *"The measure
of an inclusive system is not that it can be used by most people. It is that it cannot be
prevented from reaching anyone."* Judges will test it. We build it in from the first
screen, because retrofitting accessibility is how it ends up fake.

| Requirement | How | Proposal |
| --- | --- | --- |
| Screen reader end to end | Every control labelled; reading order set deliberately; the risk dial announces "Cholera risk, high, cases expected in two to ten days" | §13.1 |
| Nothing conveyed by sound alone | Every alert is text + colour + icon + vibration | §13.2 |
| Distinct vibration patterns | Severe, high and routine each feel different, so an urgent warning is identifiable without looking | §13.2, §13.3 |
| Braille display support | Standard accessibility APIs only, no custom text rendering that bypasses them | §13.3 |
| Large text | Respects OS font scaling to 200% without breaking layout. No fixed-height text containers | §13.4 |
| Simplified mode | Symbols and short spoken sentences, no technical language | §13.4 |
| Big targets | 48dp minimum, generously spaced, no fine or rapid movement required | §13.4 |
| Local languages | English, Twi, Ga, Ewe, Dagbani — written and spoken | §13.5 |
| Audio delivery | The forecast and each lesson can be listened to rather than read | §13.1 |

**Test we hold ourselves to:** the daily forecast and a full report submission are both
completable with the screen curtain on, using VoiceOver/TalkBack only.

---

## 5. Architecture

Layered the same way as the backend, dependencies pointing inward, so the parts that hold
the product's logic can be tested without a simulator.

```
app/                 Expo Router routes. Screens only: layout, state wiring, no logic.
src/
  design/            Tokens, typography, motion constants. The single source of style.
  components/        Presentational. Take props, hold no network state.
  features/          One folder per area: forecast, report, learn, guardian, district.
                     Each owns its hooks, its view models and its copy.
  lib/
    api/             Generated types from the live OpenAPI + a typed client. No hand-written shapes.
    identity/        Guardian identity, district choice, secure storage.
    offline/         Queue for reports, cache for the last-good forecast.
    a11y/            Announcements, vibration patterns, font-scale helpers.
    i18n/            Message catalogue per language.
```

**Rules**

- `app/` never calls the API directly; it uses a feature hook.
- `components/` never imports from `features/`. Dependencies point one way.
- Types come from `npm run types:api` against the running backend, exactly as the web
  does. The contract cannot drift silently.
- No business rules in the app. The engine decides risk; the phone renders the decision.
  If we find ourselves computing a risk level on the phone, it belongs in the backend.

### Stack and why

| Choice | Why |
| --- | --- |
| **Expo SDK 54** + Expo Router | File-based routing matches the team's Next.js mental model; EAS gives a real installable build for the demo without Xcode wrangling. SDK 54 (React Native 0.81, React 19.1) is pinned deliberately rather than tracking latest — see D7 |
| **TypeScript strict** + `noUncheckedIndexedAccess` | Same settings as the web, same discipline |
| **Reanimated 4.1** + Gesture Handler | Animations on the UI thread via `react-native-worklets`. Anything less drops frames on the cheap Android devices this app is for |
| **TanStack Query** | Same as web: caching, retry, and offline semantics we would otherwise hand-roll |
| **expo-haptics** | Vibration patterns are an accessibility requirement, not a flourish |
| **expo-speech** | Audio delivery of the forecast (§13.1) without a paid TTS service |
| **react-native-svg** | The district shape, the risk dial, the shield. No raster assets |
| **MMKV** | Fast synchronous storage for the offline queue and last-good forecast |
| **expo-image** | Real caching and fast decode for report photos |

Deliberately **not** used: a component kit (Paper, NativeBase, Tamagui). Their default look
is exactly the "AI trace" we are avoiding, and fighting a kit's opinions costs more than
building fifteen controls. We build the controls; the design system is ours.

---

## 6. Motion: the rules before the animations

The user asked for strong animation, so it is worth being precise about what separates
considered motion from the kind that reads as generated.

**The rule:** motion explains a change that already happened, or gives feedback for a
gesture. It never decorates, never announces the app's arrival, and never delays a person
who is trying to read a warning.

| Rule | Consequence |
| --- | --- |
| Everything under 300ms unless it follows a finger | A warning app that makes you wait is a bad warning app |
| Springs for gestures, curves for state | A sheet follows the thumb with physics; a colour change eases |
| Motion is interruptible | A user can always swipe away mid-animation |
| Nothing loops forever | Except one thing: the severe-risk pulse, which is a warning |
| Respect Reduce Motion | Every transition has a cross-fade fallback, not "no feedback" |
| Never animate in a list on scroll | Stagger on first mount only; after that, instant |

### The opening

The gong is struck and the sound travels: the mark lands with a spring, three rings leave
it in sequence, and the dark field lifts to reveal the day's forecast underneath.

The rule that shapes it: **this is a warning application, so the opening may never make
somebody wait to read a warning.** It runs *while* the forecast is being fetched, not
before it, and it is capped at about 1.6 seconds. If the data arrives first the opening
still finishes its beat, because a splash cut off mid-motion looks broken. If the data is
slow the opening ends anyway and the screen behind shows its own loading state. Under
Reduce Motion it is a still mark and a cross-fade.

The native splash uses the same field colour, so there is no white flash between the two.

### The animations that earn their place

1. **Risk dial** — on load the arc sweeps from zero to the level and settles with a spring;
   the colour interpolates through the scale rather than cutting. It is the one hero
   moment, and it is showing a real value arriving.
2. **Level-change shift** — when the level changes between days, the old word slides out
   and the new one in, with the canvas tint crossfading. This is the state change the
   whole app exists to communicate.
3. **Severe pulse** — a slow, low-amplitude pulse on the dial ring at severe only.
   Deliberately not a flash: it must be noticeable in peripheral vision without being
   alarming to look at, and it stops when acknowledged.
4. **Action card lift** — the day's action lifts under the thumb on press with a spring,
   with a haptic tick at the top of the travel.
5. **Report sheet** — a gesture-driven bottom sheet that tracks the finger, with rubber
   banding at the limits and a decay to snap points.
6. **Shutter and upload** — the photo scales into the report card and a determinate ring
   tracks the upload. Progress is real, never a fake timer.
7. **Points counter** — rolls up with tabular figures when points are awarded; the ladder
   segment fills to the new position. No confetti.
8. **Quiz answer** — correct and incorrect are distinguished by shape and haptic as well
   as colour, then the explanation slides in beneath. No buzzer, no celebration.
9. **Shield fill** — the district shield fills as community activity rises. Slow, and only
   animates when the value actually changed since last view.
10. **Screen transitions** — shared element on district shape from list into detail;
    otherwise a short, flat push. No zoom-blur, no parallax.

**Haptics, mapped:** severe = two heavy taps, high = one heavy, moderate = one light,
success = light tick, failure = warning pattern. Consistent across the app so a person
learns the language of it.

---

## 7. Screens

### Today (`/`) — the habit
The whole product in one screen. District name and date, the risk dial, the verdict in a
sentence, the single action, and a "why this" disclosure that opens the plain-language
reasons. Below the fold: the other conditions raised today, and the lesson if one was
triggered. Pull to refresh shows when the forecast was last fetched.

### Report (`/report`) — Community Watch
Type of hazard as large icon targets, photo, automatic location with a manual correction,
one optional note. Submits offline-first with a visible queue. After submitting, it says
what happens next: a health officer verifies it, and it becomes a signal in the engine.
That sentence is the whole point of Community Watch and most apps forget to say it.

### Learn (`/learn`) — weather-triggered
Not a library. One lesson, chosen because of today's hazard, about a minute long, ending
in a practical task. Then the daily quiz: three questions tied to the live hazard, with
the explanation shown after each answer. Audio playback for every lesson.

### Guardian (`/guardian`) — the card
Points, level, and what the next level unlocks in health terms, not in badges. The
Guardian ladder with the health dividend spelled out (§12.1). Missions available now.
Redemption flow for insurance renewal, simulated for the demo and clearly labelled as such.

### District (`/district`) — belonging
The district's own shape, its shield strength, its distinction, the Outbreak Averted count,
and how it stands against neighbours. This is where community pride lives (§11.2).

---

## 8. What the backend already gives us, and what is missing

**Ready now** (all typed, tested and live):

`POST /login` · `GET /me` · `GET /districts` · `GET /forecast/{district}` ·
`GET /risk/{district}` · `POST /reports` · `GET /reports` · `GET /quiz/daily/{district}` ·
`POST /quiz/answer` · `GET /guardian/{user}` · `GET /rewards/{user}` ·
`POST /guardian/mission` · `GET /shield/{district}` · `GET /prevention/{district}` ·
`GET /public/overview` · `GET /matrix`

**Missing, and needed before the matching screen can be real.** Each is backend work:

| Gap | Needed for | Notes |
| --- | --- | --- |
| ~~Citizen sign-up~~ | Done | `POST /citizens`, no password, no code. Age band decides tier, supervision and reward eligibility |
| Lessons, weather-triggered | Learn | §11.1. The engine already knows the hazard; a lesson needs to be selectable by condition and season |
| Mission catalogue | Guardian | `POST /guardian/mission` exists but nothing lists the missions available now |
| ~~Photo upload~~ | Done | `POST /reports/photo` takes the image as the raw request body, addressed by content hash, signed-in callers only |
| Language on the forecast | Today, Learn | `GET /forecast` accepts `language`, but only English and partial Twi phrasing exist |
| Quiz duel | Learn | §11.3, and listed in the §17 prototype scope |
| Anansi mini-game | Children's tier | §11.4, listed in §17 scope |

**Recommended order:** citizen identity first (everything depends on it), then photo
upload, then missions, then lessons. Quiz duel and Anansi last: they are scoped in §17 but
they are the two that can be cut without breaking the demo story.

---

## 9. Build order

Thin, working slices. Each one ships with its states and its accessibility, or it is not
done.

- [x] **M0.5 — The opening and the typefaces.** Native splash matched to the field colour
      so the handover is invisible, the Dawuro bell mark drawn as geometry, three rings
      leaving it in sequence, and the field lifting to reveal the forecast. Fraunces for
      the verdict, Inter for everything else.
- [x] **M0 — Foundation.** Expo SDK 57, TypeScript strict with `noUncheckedIndexedAccess`,
      Expo Router with typed routes, design tokens, type scale, motion constants, risk
      presentation with the vibration language, generated API types, and the Today screen
      rendering a real engine forecast with the dial animating to it.
- [x] **M1 — Today.** The forecast screen end to end: risk dial, verdict, action, reasons,
      offline last-good, pull to refresh, full screen-reader pass.
- [x] **M2 — Identity.** `POST /citizens` takes a name, district, age band and language,
      with no password and no verification code. `GET /citizens/age-bands` and
      `GET /public/districts` are open so sign-up renders before anybody has an account.
      The four-step join screen persists the returned token to the keychain, so a Guardian
      joins once and afterwards simply opens the app. Today reads their district and their
      language; a phone with no session goes to sign-up instead.
- [x] **M3 — Report.** Community Watch end to end: six hazard types as large targets,
      camera or gallery, optional exact location, a note, and the "what happens next"
      screen. Photographs upload separately and are content-addressed. A report written
      without a connection is held on the phone, the person is told so plainly, and it
      sends itself the next time the app opens online.
- [x] **M4 — Learn.** Weather-triggered lesson and the daily quiz with explanations.
- [x] **M5 — Guardian.** Points, ladder, health dividend, missions, simulated redemption.
- [x] **M6 — District.** Shield strength and status, the Outbreak Averted count with what
      it actually means, the agencies' on-time record including anything overdue, and
      every condition the engine evaluated rather than only the leading one.
- [~] **M7 — Language pass.** The citizen forecast is composed in Twi, not translated:
      condition names, level words, the sentence frame and all 16 actions. The API
      declares where the words came from, and the app tells the reader the Twi has not
      been reviewed. The forecast and the lesson can be read aloud, prominently for a
      Voice-First Guardian. **Remaining:** review by a Twi speaker, then Ga, Ewe and
      Dagbani, and simplified
      mode, screen-curtain test on Today and Report.
- [ ] **M8 — Demo build.** EAS build installed on a real device, both proposal scenarios
      rehearsed on it.

---

## 10. Decisions

**D18 — Audio never speaks a language the phone cannot pronounce.** `Listen` checks the
system voice list for the language the text is actually in. If there is no voice, it says
"This phone cannot read Twi aloud yet" and stays quiet, rather than reading Twi with an
English voice. Noise delivered confidently is worse than silence, because the listener
cannot tell it is wrong. The control is full width and sits directly under the verdict for
a Voice-First Guardian, and is a quiet pill for everybody else: the tier is named for
this, and the rest of us mostly read.

Nothing auto-plays. A warning that starts talking by itself on a shared phone is a
different kind of failure.

**D17 — Offline data and credentials are stored differently on purpose.** On a device
both use native storage: the token in the keychain, the queue and the last forecast in
MMKV. On web the token stays in memory and is forgotten on reload, while the queue and
forecast use localStorage. A queued report is the user's own data and a forecast is public
information; a bearer token sitting in browser storage is a credential somewhere it need
not be. The split also means the offline behaviour can be exercised in the preview.

**D16 — The action card shows the engine's own reasons, unedited.** Tapping it reveals
the exact trigger sentences with their readings and thresholds: "Heavy rainfall in the
past week creates mosquito breeding sites (7-day rainfall 120 mm, at or above the 50 mm
threshold)". Nothing is rewritten for the phone. This is the difference between a warning
somebody trusts and one they scroll past, and it is the same text the agency dashboard
shows, so a citizen and an officer are never told different stories.

**D15 — Points are never shown alone.** The Guardian card puts every level next to what
it unlocks, because a number with no meaning attached is a vanity metric. Proposal
section 12: the reward that matters is health insurance registration, since recognition
does not pay for a clinic visit.

**D14 — Joining is becoming a Guardian, in one step.** Registration now enrols the
Guardian record as well as the citizen identity. Found by testing: without it the first
quiz answer returned 404, because points had nowhere to go. Proposal section 11 says
everyone who joins becomes a Climate Guardian of their district, so there is no second
sign-up.

**D13 — The age band changes the words, not just the wrapper.** Every Tier 1 condition is
written four times, once per tier, and a test asserts all twenty exist. A nine-year-old
reads an Anansi story about a bucket of old rain; a teenager reads why the mosquito's
ten-day cycle explains the three-week gap; an adult reads what to clear this week; an
elder reads three short sentences in larger type. Same district, same hazard, same day.

Conditions without written content say so plainly and give the action, rather than
handing a child an adult's paragraph.

**D12 — A report is held, never lost.** The people most exposed to climate risk have the
least reliable connectivity, so a failed send is queued rather than surfaced as an error,
and the screen says exactly that: it is saved here, it will send by itself, you do not
need to write it again. Photographs are kept by their local file URI rather than copied,
because the phone already holds the bytes. Eight attempts, then the entry is dropped: a
report nobody can send will never be verified and is only taking up room.

Durability is MMKV on a device. In the web preview the queue lives in memory and does not
survive a reload — the preview is a development convenience, and the queue only has to be
durable on a phone. **Not yet verified on a real device**, only in the preview.

**D11 — A photograph is its own request, and its own step.** `POST /reports/photo` takes
the image as the whole request body with its type in the Content-Type header. One image
per request needs no field names and keeps a multipart parser out of the server, which
also meant no new dependency. Uploading before the report means a weak connection retries
the bytes rather than the whole submission, and a report can still be filed without a
photo. Files are addressed by the hash of their contents, so a resend after a dropped
connection costs one file rather than two.

**D10 — What we store is always a district, never a region.** The engine forecasts at
district level, so a region alone would not produce a warning. Region exists in the
sign-up only to narrow 260 districts to a dozen, and the screen says which one it is
asking for at each step rather than blurring the two together.

Three routes into the same answer, fastest first: let the phone say where it is, or pick
region then district. Location is matched against district *centres*, because the backend
does not hold boundaries, so it can land on a neighbour — Madina's coordinates match
Adenta at 4.3 km. The match is therefore always shown with its distance and can be
changed, never applied silently.

**D9 — The session lives in the keychain, and joining happens once.** A person opens
Dawuro each morning to read a warning. Asking them to sign in first would be absurd, so
the token is kept on the device: `expo-secure-store` on a phone, and in memory only in the
web preview, which is a development convenience and should not quietly persist credentials
in a browser.

**D8 — The age band is a safeguarding field, not a demographic one.** It is the only
question at sign-up that changes the product: it sets the tier (Anansi, Risk Scout,
Community Champion, Voice-First), whether missions must be supervised, and whether health
rewards may be offered at all. Proposal section 12.3 is explicit that under-18s are
already exempt from insurance premiums, so offering a child free insurance would mean
nothing, and offering health rewards to a minor in exchange for fieldwork would be wrong.
The rule lives in `services/citizens.py` with tests, not in the screen.

We ask for a band rather than a date of birth because a band is all the platform needs,
and asking a child for their birthday to run a public-health app is more than we can
justify holding.

**D1 — Expo, not bare React Native.** The demo needs an installable build on a real
Android phone with minimum ceremony, and EAS gives that. Bare RN buys native-module
freedom we do not need.

**D2 — No component library.** A kit's default look is the exact thing the brief rules
out, and every screen here is bespoke anyway. We build the controls.

**D3 — Warm palette, distinct from the console.** Same risk semantics, different world.
A citizen app that looks like an operations console has misjudged its reader.

**D4 — No score out of 100 shown to citizens.** The console shows 81.6 because an officer
ranks districts. A citizen needs a level, a window and an action. The number would invite
false precision about a person's own risk.

**D5 — Offline is a first-class state.** The people most exposed to climate risk have the
least reliable connectivity. Last-good forecast with its timestamp, and a report queue that
survives being closed.

**D7 — Pinned to Expo SDK 54, not latest.** Every package is pinned to SDK 54's own
manifest (`bundledNativeModules.json`) rather than to whatever npm resolves, so the tree
is exactly what Expo tests together. A side effect worth having: SDK 54 ships TypeScript
5.9, so `openapi-typescript` installs as a normal devDependency instead of being run
through `npx` to dodge a peer conflict. `npm run types:api` now works in-tree.

**D6 — Accessibility built in from M1.** Retrofitted accessibility is always shallow, and
§13 is one of the strongest parts of the proposal. It ships with each screen.

---

## 11. The demo, in order

Set the two scenarios first (they bypass the climate feed, so they work even if
Open-Meteo's daily quota is spent):

```bash
T=$(curl -s -X POST localhost:8000/login -H 'content-type: application/json' \
  -d '{"username":"national.officer","password":"national-demo-2026"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -s -X POST localhost:8000/demo/set-conditions -H "Authorization: Bearer $T" \
  -H 'content-type: application/json' -d '{"district_id":"madina","scenario":"heavy_rain"}'
curl -s -X POST localhost:8000/demo/set-conditions -H "Authorization: Bearer $T" \
  -H 'content-type: application/json' -d '{"district_id":"wa","scenario":"dry_and_dusty"}'
```

That gives Madina malaria 83 severe and Wa meningitis 91 severe.

Then, on the phone:

1. **Open the app.** The gong sounds three times and the field irises open onto the
   forecast. Tap to skip it if you would rather not wait.
2. **Join** as a 6 to 12 year old in Madina. Four questions, no password, no code.
3. **Today** shows severe malaria, the reason, and the one action for today.
4. **Learn** shows *Where the mosquito hides*, the Anansi version, and asks
   "Where do mosquitoes lay their eggs?"
5. **Sign out and rejoin as 60 and above**, same district. The same hazard is now
   *After the rain, check the water*, in larger type, asking what protects you while you
   sleep. This is the point worth pausing on: the age band changed the words, not the
   wrapper.
6. **Report** standing water. Turn the phone to flight mode first: the report is held,
   and the screen says so. Turn signal back on and reopen the app; it sends itself.
7. **Guardian card** shows the points that report will earn and what each level unlocks.

---

## 12. Running it against a phone

`npm start` on its own is not enough, because the two halves have to be able to see each
other.

```bash
# Backend: bind every interface, or a phone on the same Wi-Fi reaches nothing
cd backend && uv run uvicorn climahealth.api.main:app --host 0.0.0.0 --port 8000

# Mobile
cd mobile && npm start
```

The app infers the API host from the Expo dev server's own address, so no constant needs
editing. Two settings make it work: uvicorn must bind `0.0.0.0` rather than its default
`127.0.0.1`, and `CLIMAHEALTH_ALLOW_LOCAL_NETWORK_ORIGINS=true` admits private-network
origins on the development ports. That switch is off by default and must never be on in
production.

---

## 13. Known issues

**S1 — Three console messages in the web preview only.** `react-native-svg`'s web shim
emits an invalid `transform-origin` property; `react-native-web` deprecates the `shadow*`
props that are correct on iOS; and Chrome blocks `navigator.vibrate` until the page has
been tapped. None exist on iOS or Android, and the screen renders correctly on all three.
The web preview is a convenience for fast iteration, not a target.

**S2 — The dial's colour steps rather than interpolates.** The working doc's motion
section asked for the colour to interpolate through the risk scale. `react-native-svg`
only animates geometry reliably across platforms, and a dial whose colour disagrees with
the word beside it is worse than one that changes in a single step. The sweep and the
severe pulse are animated; the colour is set per level. Revisit if it matters.

**S3 — resolved.** Today now reads the registered Guardian's own district and language.

---

## 14. Open questions

**Q1 — Citizen authentication: settled.** No verification code. A one-time code costs
money to send and turns the first thirty seconds of a public-health application into a
chore, which is exactly the friction that stops the people most at risk from ever
arriving. The account holds no money and reaches no data beyond the citizen's own
district, which the public overview already publishes, so the cost of a wrong name is
close to nothing. Phone number is optional and only so a warning can reach a phone that
cannot open the app.

**Q2 — Which languages ship real content.** Twi is written into the SMS layer already.
Ga, Ewe and Dagbani need a native speaker; inventing health advice in a language nobody on
the team can verify would be worse than shipping English only. Who can supply them?

**Q3 — The insurance redemption is simulated.** §12 is the strongest idea in the proposal
and no part of it can be real for a hackathon. The screen must be clearly labelled as a
simulation, in a way that reads as honesty rather than as a disclaimer we were forced to add.

**Q4 — Anansi tier scope.** §11.4 is a whole product. For the prototype, one mini-game is
listed in §17. Worth confirming that is all we attempt.
