# 𝄞 Lyrica

> Sing along to any song — in any language you don't speak.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=flat-square)
![Tests](https://img.shields.io/badge/tests-143%20passing-brightgreen?style=flat-square)
![Cost](https://img.shields.io/badge/running%20cost-%240%2Fmonth-success?style=flat-square)
![Render](https://img.shields.io/badge/deployed%20on-Render-46E3B7?style=flat-square)

Paste a song title and artist (or a YouTube link). Get back the original lyrics, a proper romanization, an English-friendly phonetic guide, and an optional English translation — synced to video playback when timing data is available.

```
Original     愛してる
Romanized    Aishiteru
Friendly     Eye-shee-teh-roo  ↳
Translation  I love you
```

---

## Supported languages

19 scripts supported, each checked against real words before shipping — not just assumed to work.

| Script | Language | Method |
|--------|----------|--------|
| Hiragana / Katakana + Kanji | Japanese | cutlet (MeCab morphological analysis) |
| Hangul | Korean | korean-romanizer (Revised Romanization) |
| CJK | Chinese | pypinyin (tone-aware, polyphonic disambiguation) |
| Cyrillic | Russian | PyICU (CLDR BGN standard) |
| Greek | Greek | PyICU + modern voicing correction (αυ/ευ → av/ev) |
| Devanagari | Hindi | indic-transliteration (IAST) |
| Arabic | Arabic | espeak-ng (IPA) |
| Gurmukhi | Punjabi | espeak-ng (IPA) |
| Bengali | Bengali | espeak-ng (IPA) |
| Gujarati | Gujarati | espeak-ng (IPA) |
| Odia | Odia | espeak-ng (IPA) |
| Tamil | Tamil | espeak-ng (IPA) |
| Telugu | Telugu | espeak-ng (IPA) |
| Kannada | Kannada | espeak-ng (IPA) |
| Malayalam | Malayalam | espeak-ng (IPA) |
| Sinhala | Sinhala | espeak-ng (IPA) |
| Armenian | Armenian | espeak-ng (IPA) |
| Georgian | Georgian | espeak-ng (IPA) |
| Ethiopic | Amharic | espeak-ng (IPA) |

**Hebrew, Thai, and Myanmar are intentionally excluded.** espeak-ng's output for all three is demonstrably wrong on common words — confirmed against the raw CLI, not just imprecise. They're detected as scripts (the app knows what language it's looking at), but won't guess at pronunciation.

---

## Build phases

This project was built across 7 phases, each a real decision checkpoint rather than a waterfall stage.

### Phase 1 — Analysis
Feasibility study: which lyrics sources are actually legally usable, which transliteration libraries are reliable enough, what the YouTube API quota math looks like at real usage, and why Spotify's 2026 API changes made it incompatible with a free personal project (requires Premium subscription + 250k MAU for public access).

### Phase 2 — Architecture
Settled on the free-tier pipeline: YouTube Data API v3 for video metadata, LRCLIB for synced lyrics, espeak-ng for IPA fallback, Render for hosting. Deliberately chose deterministic transliteration over LLMs wherever reliable libraries existed — keeps the pipeline free, predictable, and fast.

### Phase 3 — MVP scope
Defined the smallest version that would actually demonstrate the core value: title+artist text input, 7 languages, manual-paste fallback, YouTube embed playback with line-by-line sync. No Spotify, no accounts, no audio upload.

### Phase 4 — Project structure
FastAPI backend with per-language transliteration modules, a shared LRC parser, SQLite cache (disposable by design), and a React frontend. Deliberate separation between the API contract layer and the internal service models.

### Phase 5 — Implementation (6 steps)
Built incrementally, each step verified before the next:
1. Backend skeleton (FastAPI, config, Docker, health check)
2. YouTube Data API + LRCLIB clients (mocked in tests, smoke-tested live)
3. Language detection + transliteration engine (Japanese, Chinese, Korean, Russian, Greek, Hindi)
4. Respelling layer (romanized/IPA → English-friendly phonetics)
5. `/songs/resolve` + `/lyrics/manual` endpoints with SQLite caching
6. React frontend (Tailwind v4, YouTube IFrame embed, synced lyric scroll)

Post-MVP additions: YouTube URL input, search history (localStorage), translation button (Anthropic API), and a language coverage expansion from 7 to 19 scripts after a real bug report (Punjabi song returned unchanged because Gurmukhi wasn't in the script detection table).

### Phase 6 — Tests
143 tests across 9 test files, all passing, running in under 15 seconds. Coverage maps directly to the original spec's checklist: language detection, transliteration (all 19 scripts), respelling, LRC parsing, API failures, invalid URLs, missing lyrics, unsupported languages, malformed lyrics. Database-backed tests use a per-test isolated SQLite file via an autouse fixture.

Three real bugs were caught writing tests — not running them:
- An `assert ... or True` that could never fail (rewritten to actually verify dispatch behavior)
- A monkeypatch that infinitely recursed into its own patched function (fixed by capturing the real value before patching)
- A translation count mismatch that would have silently misaligned translated lines (now raises an error)

### Phase 7 — Deployment
Render Blueprint (`render.yaml`) deploys both services in one step: Docker web service for the backend, static site for the frontend. CI runs the full test suite + frontend build on every push.

One real bug found writing deployment config: the Dockerfile's `CMD` hardcoded port 8000 in exec form, which doesn't expand `$PORT` — Render assigns a dynamic port. Fixed to shell form with `${PORT:-8000}` fallback so `docker compose up` still works locally unchanged.

---

## Architecture decisions

**Spotify was cut.** As of February 2026, Spotify's Web API requires the developer's own Premium subscription just to keep a dev-mode app alive, caps it at 5 users, and requires 250,000 monthly active users for public access. YouTube is genuinely free with no such restrictions.

**History is client-side.** Render's free web services spin down after 15 minutes idle and have no persistent disk (that's a paid add-on). Server-side SQLite history would reset almost every session once deployed. `localStorage` is a better fit for a single-user, no-accounts app anyway.

**Deterministic transliteration wherever possible.** Using language-specific libraries (cutlet, pypinyin, PyICU) rather than LLMs keeps the pipeline free, testable, and deterministic. An LLM layer exists only for translation, which is genuinely a contextual-meaning problem rather than a rules problem.

**Three languages excluded, not just unsupported.** Hebrew, Thai, and Myanmar's espeak-ng output was tested against real words before the decision. Thai leaks raw tone-number digits into what should be IPA (`สวัสดี` → `sa5wmsaɜds`). Myanmar's output barely resembles the input. Both confirmed against the raw `espeak-ng` CLI, not a wrapper bug.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI 0.141.1, Uvicorn |
| Frontend | React 19.2.8, Vite 8.2.0, Tailwind CSS v4.3.3 |
| Routing | react-router-dom 7.18.2 |
| Transliteration | cutlet, pypinyin, korean-romanizer, PyICU, indic-transliteration |
| IPA fallback | phonemizer + espeak-ng (19 languages) |
| Lyrics | LRCLIB (free, open, no auth required) |
| Video | YouTube Data API v3 + IFrame Player API |
| Cache | SQLite (disposable, rebuilds on demand) |
| History | Browser localStorage |
| Translation | Anthropic API — Claude Haiku (optional) |
| Testing | pytest 9.1.1 + pytest-asyncio 1.4.0 |
| Deployment | Render (Docker web service + static site) |
| CI | GitHub Actions |

---

## Getting started

### Windows — install PyICU first

PyPI doesn't ship Windows wheels for PyICU (it compiles against the system ICU library). Install a prebuilt wheel before `pip install -r requirements.txt`:

```powershell
pip install https://github.com/cgohlke/pyicu-build/releases/download/v2.16.2/pyicu-2.16.2-cp312-cp312-win_amd64.whl
```

Use `-win_arm64.whl` on ARM64 Windows.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
cp .env.example .env             # add YOUTUBE_API_KEY
uvicorn app.main:app --reload
```

Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App at `http://localhost:5173`.

### Run tests

```bash
cd backend
pytest tests/ -v
```

### Smoke test (live APIs)

```bash
cd backend
python -m scripts.smoke_test "Bohemian Rhapsody" "Queen"
```

Confirms the YouTube API key works and LRCLIB is reachable. Run this before trusting the mocked test results against real usage.

### Translation (optional)

Add `ANTHROPIC_API_KEY` to `backend/.env` — get one from [console.anthropic.com](https://console.anthropic.com). The translation button appears in the lyrics panel once a song loads. Everything else works without this key set.

---

## Deployment

One-step via Render Blueprint:

1. Push to GitHub (private repo recommended)
2. Render dashboard → New → Blueprint → connect repo
3. Render reads `render.yaml` and creates both services
4. Set `YOUTUBE_API_KEY` in the backend service's environment variables
5. Optionally set `ANTHROPIC_API_KEY` for translation

**Verify URLs after first deploy.** `render.yaml` hardcodes `Lyrica-backend` and `Lyrica-frontend` as service names. If either name is taken and Render assigns a different URL, update `CORS_ORIGINS` (backend) and `VITE_API_BASE_URL` (frontend) to match, then trigger a manual redeploy on the frontend.

**Running cost: $0/month.** YouTube Data API, LRCLIB, espeak-ng, and Render's free tier are all genuinely free. The only possible cost is the Anthropic API for translation — approximately $0.001 per song at Haiku pricing, billed only when the translate button is clicked.

---

## Known limitations

- LRCLIB's coverage varies. Mainstream and well-known tracks usually have synced lyrics; regional or obscure music often doesn't. The manual-paste fallback handles this.
- Pinyin's convention of writing ü as plain "u" after j/q/x/y isn't handled (needs syllable-aware parsing, not character substitution).
- The frontend has not been visually verified in a real browser from the build environment — it was build-verified and prop-traced by hand. Worth an actual look before going live.
- The Docker build for production compiles PyICU from source — first build is slow (3–5 minutes on Render's free infrastructure).

---

## License

MIT — your own code. Dependency licenses vary; notably espeak-ng is GPL (used as an external binary, not compiled against).
