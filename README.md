# Song Pronunciation App

Helps English speakers sing along to non-English songs by showing original
lyrics, a proper romanization, and an English-friendly phonetic respelling —
side by side, synced to playback where timing data is available.

**Status:** backend skeleton only. Song lookup, lyrics, transliteration, and
the frontend land in the steps that follow.

## Design decisions worth knowing before you read the code

- **No Spotify integration.** As of Feb 2026, Spotify's Web API requires the
  developer's own account to have an active Premium subscription just to keep
  a development-mode app running, caps dev apps at 5 users, and requires
  250k+ monthly active users to unlock public access. None of that fits a
  free personal project, so YouTube (genuinely free, no such cap) is the only
  audio source.
- **Lyrics come from LRCLIB**, a free, open (MIT), no-auth-required database
  of plain and synced lyrics — not from Genius (their API doesn't return
  lyric text at all) or from scraping any streaming platform.
- **Transliteration is deterministic wherever a good library exists**
  (Japanese, Korean, Chinese, Cyrillic/Greek, Hindi), with `espeak-ng` as a
  free, offline fallback for everything else, including Arabic and Hebrew.
  An LLM polish layer is an optional, off-by-default add-on — never a
  requirement for the app to work or stay free.

**Hebrew is not supported yet.** espeak-ng's Hebrew voice gives correct
output for simple words (שלום → shalom) but produces genuinely wrong
output for common words involving certain vowel-letter clusters (אוהב,
בוקר) — confirmed against the raw `espeak-ng` CLI directly, not a bug in
this app's code. Rather than present unreliable pronunciation as if it
were trustworthy, Hebrew lines raise `UnsupportedLanguageError` until
there's a better option — most likely the optional LLM layer, since this
is exactly the kind of context-dependent vowel ambiguity a language model
can reason about better than a rule-based phonemizer.

**Docker build note:** the backend image now compiles PyICU against the
system ICU library and installs espeak-ng, so the image is bigger and the
build is slower than Step 1's. I can't run `docker build` from inside my
own sandbox to test this end-to-end (no Docker daemon there) — the local
`uvicorn` path is fully verified, the Docker path is verified by
reasoning about what each package needs, not by an actual build. Flag it
if it breaks.

**API (Step 5):**
- `POST /songs/resolve` — `{title, artist}` → video info (YouTube), lyrics
  (LRCLIB), and every line transliterated + respelled. YouTube and LRCLIB
  run concurrently; either can fail without breaking the other — you can
  get lyrics with no video, or a video with no lyrics (`lyrics_found:
  false` is the signal to show the manual-paste UI). A line in an
  unsupported language (Hebrew, currently) comes back with
  `supported: false` rather than failing the whole request. Successful
  lookups are cached in SQLite for 30 days, keyed by normalized
  title+artist; transient errors (quota, network) are never cached, so a
  bad moment doesn't get stuck there for a month.
- `POST /lyrics/manual` — `{lyrics}` → the same per-line processing,
  for when LRCLIB doesn't have the song.

One structural note: the originally-planned `models/db.py` (SQLAlchemy
models + session) didn't end up existing — the cache is a single
key→JSON-blob table, plain `sqlite3` in `services/cache.py` handles it
without needing an ORM layer on top.

**Frontend (Step 6):** React 19 + Vite 8 + Tailwind v4 — all newer major
versions than I'd have guessed from memory, checked against the real npm
registry before locking `package.json` rather than assumed (Tailwind v4
in particular configures very differently from v3: CSS-first `@theme`
tokens, not a JS config file).

Design concept: the exact format this app produces — original text,
romanization, gloss, stacked per line — is a real linguistic convention
called interlinear glossing, which became the anchor instead of generic
"music app" styling. The look is a songbook with pencil pronunciation
notes in the margin: deep ink-indigo background, warm gold and dusty sage
accents (deliberately not the cream+terracotta or near-black+neon combos
that AI-generated design defaults to), Fraunces for display type, Work
Sans for UI, Noto Sans for the original-script lyrics text (chosen for
real multi-script Unicode coverage, not as a default), and — the one
signature move — the English-friendly pronunciation renders in a
handwritten face (Caveat), slightly rotated, like an actual margin note.

**Honest limitation on testing:** I can build the frontend
(`npm run build`) and confirm the custom design tokens and fonts land
correctly in the compiled output, and I traced every prop name between
components and every field name against the backend's response models by
hand to catch mismatches a build won't. What I can't do from this
sandbox is render it in an actual browser — no visual check of the
design, no confirming the YouTube player embeds and syncs correctly in
practice. Worth genuinely looking at before trusting the design choices
land the way they're described here.

**Running the frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Opens on `http://localhost:5173`, already pointed at the backend's
default `http://localhost:8000` via CORS (Step 1's `cors_origins`
default matches Vite's default port, so this works with no config
changes on either side).

## Added after the MVP: YouTube link input + history

**Paste a YouTube link instead of typing title/artist.** New backend
endpoint `POST /songs/from-url`: parses the video ID out of the URL
(handles youtu.be, youtube.com/watch, /embed/, /shorts/, music.youtube.com),
fetches real metadata via `videos.list` (1 quota unit, vs. 100 for a
search — `services/youtube_client.get_video_by_id`), then guesses a
title/artist from the video title (`services/title_guess.py`) to feed
the same LRCLIB lookup the text-input path uses. The guess is inherently
best-effort — YouTube has no structured artist field — so it's never
silently trusted: it's shown to you, and if lyrics aren't found, the
search form auto-switches back to title+artist mode pre-filled with the
guess so fixing it is a two-second edit, not a dead end.

**History.** Every search (cache hit or fresh) is logged to a new
`search_history` SQLite table (same file as the cache), recorded
defensively — a history-write failure can never break an otherwise-
successful lookup. New `GET /history` endpoint, new `/history` page in
the frontend (added real client-side routing via `react-router-dom` for
this — the app now has more than one page). Clicking a history entry
re-runs that search.

**A note on `react-router-dom`:** `npm install` flagged a high-severity
advisory (GHSA-qwww-vcr4-c8h2) affecting react-router 7.12.0–8.2.0. Read
the actual advisory rather than just reacting to the flag: it explicitly
states it only affects apps using the *unstable RSC (React Server
Components) APIs* — a server-rendering mode this app doesn't use at all
(this is a plain Vite client-side SPA using the classic
`BrowserRouter`/`Routes`/`Route` API). The installed version, 7.18.2, is
also exactly the patched boundary for the 7.x line per the advisory's
own precise ranges, independent of the RSC point. Not upgraded to v8 —
no risk reduction for this app's actual usage, and a major-version
migration isn't worth doing for that.

## Phase 6 — test suite

126 tests, `backend/tests/`, running in under 4 seconds:

```bash
cd backend
pip install -r requirements-dev.txt   # adds pytest + pytest-asyncio on top of the app deps
pytest tests/ -v
```

Every test is either pure logic (no mocking needed — language detection,
transliteration, respelling, LRC/URL parsing, title guessing) or mocked
at the external-service boundary (`youtube_client`/`lrclib_client` —
this sandbox has no network access to the real APIs, same limitation as
`scripts/smoke_test.py`). `/lyrics/manual` is tested through the real
pipeline with no mocking at all, since it never touches an external
service. Database-backed tests (cache, history) get a fresh isolated
SQLite file per test via an autouse fixture in `conftest.py` — they
never touch the real `cache.db`.

Coverage maps directly to the original spec's list:
- **Language detection** — `test_language_detect.py`
- **Transliteration** — `test_transliteration.py` (all 7 supported
  languages, plus the Hebrew rejection)
- **Pronunciation generation** — `test_respelling.py`
- **Lyrics parsing** — `test_lrc_parser.py`, `test_lyrics_processor.py`
- **API failures** — `test_clients.py` (quota, network, config errors),
  `test_api.py` (partial-failure behavior through the real endpoints)
- **Invalid URLs** — `test_url_input.py`, `TestSongsFromUrl` in `test_api.py`
- **Missing lyrics** — `TestSongsResolve::test_lyrics_not_found_*`
- **Unsupported languages** — Hebrew rejection tests across three
  layers (router, lyrics_processor, and the full API)
- **Malformed lyrics** — `test_lyrics_processor.py` (stray control
  characters, malformed LRC, extremely long lines)

Three real bugs were caught *writing* these tests, not just running
already-correct code:
- A dispatch test in `test_respelling.py` originally had
  `assert ... or True` — an assertion that can never fail, which is
  worse than no test at all. Rewritten to actually verify which function
  gets called, using mocks.
- A TTL-expiry test infinitely recursed: the mock replacing `time.time()`
  called `time.time()` internally, which was itself the patched version
  by the time it ran. Fixed by capturing the real timestamp before
  patching.
- A history-page label ("pasted manually") turned out to claim something
  the data didn't actually support — caught while writing the frontend,
  not the test suite, but worth restating here since it's the same
  category of mistake: a plausible-sounding claim that isn't backed by
  what was actually verified.

## Phase 7 — deployment (Render, $0/month)

**A real architecture change happened here, not just config.** Thinking
through what actually survives a Render free-tier restart surfaced that
persistent disks are a $0.25/GB/month paid add-on — free web services
have no persistent disk at all, and spin down after 15 minutes idle.
Render's free Postgres isn't a fix either (1 GB, expires after 30 days).
Server-side SQLite history would have reset almost every session once
actually deployed — invisible in local dev, where the backend process
just stays running, but a real problem the moment this leaves your
machine. **History moved to the browser's own `localStorage`**
(`frontend/src/lib/history.js`) — it has no accounts anyway and runs
from one browser, so client-side storage is a better architectural fit,
not just a workaround. The cache stays server-side SQLite: it was always
designed to be disposable, and losing it just means an occasional extra
API call, not a broken feature.

### What's deployed where

- **Backend** → Render Web Service, Docker runtime, free plan
- **Frontend** → Render Static Site, free plan
- Both defined in `render.yaml` at the repo root — one Blueprint, one deploy

### Steps

1. **Push to GitHub** (Render's Blueprint deploy needs a real git repo):
   ```bash
   cd song-pronunciation-app
   git init
   git add .
   git commit -m "Initial commit"
   ```
   Set your own `user.name`/`user.email` first if you haven't (`git
   config user.name "..."` / `git config user.email "..."`), then create
   a GitHub repo and push:
   ```bash
   git remote add origin <your-repo-url>
   git branch -M main
   git push -u origin main
   ```

2. **Deploy the Blueprint.** In the Render dashboard: New → Blueprint →
   connect the GitHub repo → Render reads `render.yaml` and shows both
   services it's about to create → Deploy Blueprint.

3. **Set the one secret.** `YOUTUBE_API_KEY` is marked `sync: false` in
   the Blueprint on purpose — it's never written into the repo. Render
   will prompt for it during setup, or set it afterward: backend service
   → Environment → add `YOUTUBE_API_KEY`.

4. **Verify the URLs match.** `render.yaml` hardcodes
   `songbook-backend`/`songbook-frontend` into each other's config
   (frontend's `VITE_API_BASE_URL`, backend's `CORS_ORIGINS`) rather than
   using Render's cross-service reference syntax (`fromService`) — that
   mechanism exists and is documented, but wasn't tested end-to-end here
   (no Render account access from the sandbox this was built in), and a
   plain hardcoded URL felt like the safer bet than syntax I couldn't
   verify actually resolves the way I expect. If either service name is
   already taken globally on Render, it'll assign a different one —
   check both actual URLs after first deploy and update `CORS_ORIGINS`
   (backend env vars) and `VITE_API_BASE_URL` (frontend env vars) to
   match if they differ from the hardcoded guess, then redeploy.

### What I could verify vs. what I couldn't

Same honesty as the rest of this project: I fixed a real, verifiable bug
in the Dockerfile (`CMD` hardcoded port 8000 in exec form, which doesn't
expand `$PORT` — Render assigns a dynamic port and routes to whatever
the container actually listens on; fixed to shell form with a
`${PORT:-8000}` fallback so local `docker compose up` still works
unchanged). But I don't have Render account access from this sandbox, so
the Blueprint itself — service names resolving correctly, the free-tier
Docker build actually succeeding on Render's infrastructure, cross-service
env var behavior — is my best-effort reading of Render's current
documented Blueprint spec, not something I've watched deploy
successfully. Worth confirming for real before trusting it fully,
especially the first deploy.

### Costs

Everything above is free at this project's scale: Render web service +
static site (free plan), YouTube Data API (free quota), LRCLIB (free,
open). The only way this stops being $0 is turning on the optional LLM
polish layer mentioned back in Phase 1 — which, unbuilt as of this
checkpoint, isn't a cost yet either.

### Known production quirks worth expecting

- **Cold starts.** The free backend spins down after 15 minutes idle;
  the first request after that takes a moment to wake it back up. Same
  tradeoff flagged all the way back in the architecture phase.
- **Cache resets periodically**, by design — see above. Slightly more
  frequent YouTube/LRCLIB calls, not a broken feature.
- **CI runs on every push** (`.github/workflows/ci.yml`) — backend test
  suite plus frontend build, using the same system dependencies
  (`libicu-dev`, `espeak-ng`) the Dockerfile needs. Like the Blueprint,
  written correctly to the best of my knowledge of GitHub Actions syntax
  but not something I've watched execute on a real runner — the first
  push is the first real test of it too.

## Post-deployment fix: language coverage was much narrower than it looked

A real bug report (Punjabi song, screenshot showed original/romanized/
friendly all identical) traced back to a bigger gap than just Punjabi:
`language_detect.py` only recognized 8 scripts, and **anything else
silently fell through to the "already English, don't touch it" path** —
so unrecognized scripts came back completely unchanged, which looks
exactly like a broken feature rather than an unsupported one. Same root
cause was making the manual-paste fallback look like it "did nothing"
for the same set of languages.

The fix generalizes rather than patches Punjabi specifically:
`espeak-ng` turned out to have **132 voices already installed** in this
project (confirmed via `espeak-ng --voices`), and only one (Arabic) was
ever wired up. `transliteration/arabic.py` became
`transliteration/espeak_fallback.py` — a generic module parameterized by
language instead of hardcoded to one — and `language_detect.py` grew 14
new Unicode script ranges (Punjabi, Bengali, Gujarati, Odia, Tamil,
Telugu, Kannada, Malayalam, Sinhala, Thai, Myanmar, Armenian, Georgian,
Amharic).

**Not all 14 made the cut.** Each was checked against real words before
being trusted, the same way Hebrew was checked and excluded originally.
Thai and Myanmar both failed that check — confirmed against the raw
`espeak-ng` CLI directly, not a wrapper bug: Thai leaks raw tone-number
digits into what should be IPA (`สวัสดี` → `sa5wmsaɜds`), and Myanmar's
output barely resembles the input at all (`မင်္ဂလာပါ` → `mŋ ɡltspe`).
Both stay in the same "detected but not romanized" bucket as Hebrew —
the app knows what script it is, but won't guess at how it sounds. 11 of
the 14 passed and are now live: Punjabi, Bengali, Gujarati, Odia, Tamil,
Telugu, Kannada, Malayalam, Sinhala, Armenian, Georgian, Amharic.

The respelling layer (`from_ipa.py`) also needed real extension, not
just more table entries — aspiration and nasalization are both
*modifier* characters in IPA (they alter the preceding sound rather than
standing alone), which the existing capitalize/duplicate modifier
pattern didn't cover. Generalized into an `_APPEND_TO_PREVIOUS` mechanism:
aspirated consonants respell as "kh"/"jh"/etc. (the conventional English
spelling for these already, as in "Dharma"), nasalized vowels get a
trailing "n". Building this surfaced a genuine Unicode bug along the
way: a hand-typed test string used a pre-composed character (`ũ` as one
codepoint) where espeak-ng's real output uses the decomposed form (`u` +
a separate combining tilde) — same visual character, different
underlying bytes, and the character-by-character scan only handled one
of them. Fixed by normalizing input to NFD form at the start of
`respell()`, not by special-casing the test string, so it's correct
regardless of which form any future input arrives in.

**On "why do songs still say lyrics weren't found" — this part isn't
fully fixable.** LRCLIB is a community-contributed database; its
coverage is naturally stronger for mainstream/Western pop than for
regional or less-mainstream music, and that's a property of the data
source, not a bug in this app. What this fix does ensure is that the
manual-paste workaround now actually works correctly across 19 total
supported languages (up from 8) instead of silently no-op'ing for
anything outside the original set.

14 new tests cover all of this — the Punjabi bug specifically, several
of the newly-added languages, both exclusions (Thai, Myanmar), and the
aspiration/nasalization respelling logic. 132 tests total.

## Translation feature

New `POST /lyrics/translate` — the actual meaning in English, the fourth
tier of what's traditionally called interlinear glossing (original text
/ transliteration / gloss, which is the exact format this app already
used as its design anchor — translation is just the missing tier).
`services/translation.py` calls the Anthropic API server-side (this must
never happen from the browser — exposing an API key in frontend code
means anyone can pull it from the network tab and spend money on it;
the special no-key-needed calling convention some contexts offer only
works inside Claude.ai's own sandbox, not a real standalone deployed
app like this one). Uses Haiku-tier pricing, the cheapest model, since
this is a short, well-defined text task with no need for a larger model.

Optional and explicitly user-triggered, not automatic: this is the one
part of the whole pipeline with a real per-use cost, matching the
"optional, off by default" design from the original architecture phase.
A "Translate" button in the lyrics panel triggers it on demand.

Two things worth knowing about the implementation:
- **Blank lines (instrumental gaps) are handled deterministically**, not
  by trusting the model to follow a "return empty for blank input"
  instruction — they're filtered out before the API call and reinserted
  afterward, so alignment between lines and their translations can't
  drift regardless of what the model does.
- **A translation count mismatch raises an error rather than guessing**
  — pairing the wrong translation with the wrong line would be worse
  than showing no translation at all, so the response is validated
  (exact line count, valid JSON) before anything reaches the user.

Add `ANTHROPIC_API_KEY` to `backend/.env` (from console.anthropic.com)
to enable it locally — everything else in the app works with this unset.
11 new tests cover the service (alignment, blank-line handling, code
fence stripping, all the error paths) and the endpoint. 143 tests total.

**Respelling (Step 4) is uneven by design, not by accident.** Japanese
Hepburn romaji and Korean Revised Romanization were already built to be
readable by English speakers, so they need only small fixes (Korean's
"eo" vowel). Chinese pinyin's q/x/c/z initials and ICU's classical Greek
convention (αυ/ευ → "au"/"eu" instead of modern "af/ev") actively
mislead if left alone, so those get real correction, verified against
real dictionary words during the build (see `from_romanized.py` and
`from_ipa.py` for the specifics and the reasoning behind each rule).
One known gap: pinyin's convention of writing ü as plain "u" after
j/q/x/y isn't handled — it needs syllable-aware parsing, not character
substitution, so it's a documented limitation for now rather than a
half-fix.

## Backend — running it locally

Requires Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then check:
- http://localhost:8000/health → `{"status": "ok", "env": "development"}`
- http://localhost:8000/docs → interactive Swagger UI

### Windows: PyICU needs a prebuilt wheel

`pip install -r requirements.txt` will fail on `pyicu` with a
`pkg-config` / `ICU_VERSION` error — PyPI doesn't publish Windows wheels
for it, only source, and building it from source on Windows needs a C++
toolchain plus the ICU library itself, which is genuinely painful to set
up. Fix: install a prebuilt wheel first, then re-run the normal install
(it'll pick up wherever it left off):
```powershell
pip install https://github.com/cgohlke/pyicu-build/releases/download/v2.16.2/pyicu-2.16.2-cp312-cp312-win_amd64.whl
pip install -r requirements.txt
```
Use `-win_arm64.whl` instead of `-win_amd64.whl` on ARM64 Windows. If a
future `requirements.txt` bumps the pyicu version, grab the matching
wheel from [cgohlke/pyicu-build releases](https://github.com/cgohlke/pyicu-build/releases)
instead of this exact link. This isn't needed on Linux/macOS or inside
Docker — `apt-get install libicu-dev` (already in the Dockerfile) makes
it a non-issue there, which is why this was missed originally: the whole
project was built and tested in a Linux sandbox.

### YouTube API key

Song lookup needs one. Google Cloud Console → enable "YouTube Data API v3"
→ Credentials → Create API Key → paste it into `YOUTUBE_API_KEY` in `.env`.
It's free (10,000 quota units/day; each lookup here costs 100).

### Trying the lookup for real

```bash
python -m scripts.smoke_test "Bohemian Rhapsody" "Queen"
```

Prints what YouTube and LRCLIB actually return for that title/artist —
useful for confirming your API key works, separate from the Phase 6 test
suite (which runs against mocked responses, not the live APIs).

## Backend — running it with Docker

```bash
docker compose up --build
```

Same endpoints, same port.

## Git

No repo initialized yet on purpose — run `git init` and set your own
`user.name`/`user.email` before your first commit, so authorship is
correct from the start this time.

## Roadmap

- [x] Step 1 — backend skeleton (FastAPI, config, health check, Docker)
- [x] Step 2 — song lookup + lyrics retrieval (YouTube Data API, LRCLIB)
- [x] Step 3 — language detection + transliteration engine (Japanese, Chinese, Korean, Russian, Greek, Hindi, Arabic; Hebrew intentionally not supported yet — see below)
- [x] Step 4 — respelling (romanized/IPA → English-friendly)
- [x] Step 5 — `/songs/resolve` and `/lyrics/manual` endpoints + caching
- [x] Step 6 — React frontend
- [x] Phase 6 — test suite
- [x] Phase 7 — deployment
