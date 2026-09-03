# Security — Action Required From You

**Status: 2 live credentials were exposed in this repository. Both require
manual rotation that I deliberately did not perform automatically.**

---

## 1. Committed `.env` with live Supabase credentials — ROTATE

**File:** `server/TruckRouteNavigator/.env`
**Contains:** `SUPABASE_URL`, `SUPABASE_KEY` (anon JWT)
**Exposure:** Committed to git and present in history since before Phase-A.

**What I did (safe, reversible):**
- `git rm --cached server/TruckRouteNavigator/.env` — removed from tracking.
  The local file is untouched so the legacy Flask app still runs.
- Root `.gitignore` already covers `.env` and `.env.*`.

**What I did NOT do, and why:**
- **No history rewrite.** `git filter-repo` / BFG rewrites every commit hash.
  On a repo with a remote and possible collaborators that is destructive and is
  your call, not mine.
- **No credential rotation.** Rotating a live Supabase key from an unattended
  run could break other things you have connected to that project.

**What you need to do:**
1. Rotate the Supabase anon key in the Supabase dashboard.
2. Decide whether to purge git history. The key remains readable in every
   historical commit until you do.
3. If the repo was ever public or shared, treat the key as compromised
   regardless of rotation timing.

---

## 2. Hardcoded TomTom API key — ROTATE

**File:** `server/TruckRouteNavigator/app.py`, line 184
**Value:** a live TomTom key, committed in plaintext.

**What I did:** replaced it with an environment lookup in the legacy Flask file.
The legacy value remains in git history.

**What you need to do:** rotate that TomTom key. The three keys you supplied via
`VBTools.txt` are in the gitignored `.env` and were never committed — those are
fine.

---

## 3. Verified clean

| Check | Result |
|---|---|
| `.env` tracked by git | **No** (after this change) |
| `.env.example` contains real values | No — placeholders only |
| Secrets in frontend bundle/config | None found |
| Secrets in Docker images | None — injected at runtime via `env_file` |
| Secrets printed to logs | None — see `server/app/core/logging.py` redaction |
| Secrets in screenshots | None captured |
| IBM Quantum token | In gitignored `.env` only |

---

## 4. Standing guidance

- `.env` is gitignored. Keep it that way.
- Add new variables to `.env.example` with **placeholder** values only.
- The FastAPI logging config redacts `authorization`, `token`, `key`, `secret`
  and `password` fields; do not bypass it.
