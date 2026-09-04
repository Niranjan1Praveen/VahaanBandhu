# Kinde → Clerk

**Status: architecture complete, activation blocked on credentials.**

Clerk is implemented as the production authentication path. It has **not been
exercised against a live Clerk tenant**, because no Clerk credentials were
available during this unattended run. That is stated plainly rather than
reported as a working integration.

---

## 1. What was wrong with the legacy setup

The legacy app used Kinde, but the deeper problem was not the vendor:

**The role was trusted from the client.** `src/app/api/auth/creation/route.js`
upserted a user after login and redirected to a hardcoded
`http://localhost:3000/input-dealer`. Nothing on the server verified what role a
caller actually held — every request was as authorized as the browser claimed it
was.

That is what this migration fixes. Swapping Kinde for Clerk is the smaller half.

---

## 2. Where authentication now happens

```
Browser
  │  Authorization: Bearer <clerk session token>      (production)
  │  x-dev-user: <seeded id>                          (local development only)
  ▼
FastAPI  get_identity()                server/app/core/security.py
  │  verify token against Clerk JWKS
  │  load the user document from MongoDB
  │  ROLE COMES FROM THE DATABASE — never from the token or a header
  ▼
require_role(UserRole.FARMER)          per-endpoint dependency
```

**Order matters in `get_identity`.** If a bearer token is presented it is
*always* verified and rejected on failure. Development auth applies only when no
bearer token was presented at all — it is never a fallback for a *failed*
verification. A bad token is a 401, never a quiet downgrade.

---

## 3. Endpoint mapping

| Legacy (Kinde) | New |
|---|---|
| `/api/auth/[kindeAuth]` catch-all | Clerk middleware (frontend) |
| `/api/auth/creation` upsert + hardcoded redirect | `POST /api/v1/me/role` |
| `getKindeServerSession()` | `GET /api/v1/me` |
| role read from client | `require_role()` server-side dependency |
| — | `POST /api/v1/auth/dev-login` (development only; **404 outside development**) |

---

## 4. Development authentication

Local UI work, tests and screenshots must not require network access to a Clerk
tenant. So there is a development path — but it is fenced:

```python
@property
def demo_auth_active(self) -> bool:
    return self.dev_auth_enabled and not self.is_production
```

**Two independent conditions.** A single misconfigured environment variable
cannot expose the bypass in production. `POST /api/v1/auth/dev-login` returns
**404** — not 403 — outside development, so the endpoint does not even advertise
its existence.

The UI is unambiguous: a yellow **डेमो मोड** banner naming the user id and role
sits under the header on every page whenever development auth is in use.

Asserted by `server/tests/test_api.py`:

```
test_dev_auth_is_disabled_in_production
test_dev_auth_active_in_development
```

Three seeded users: `dev_farmer_01`, `dev_trucker_01`, `dev_dealer_01`.

---

## 5. Activating Clerk

Everything below is implemented; none of it has been run against a real tenant.

**1. Set credentials** in `.env`:

```
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_JWT_ISSUER=https://<your-subdomain>.clerk.accounts.dev
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

`CLERK_JWT_ISSUER` is required — token verification fetches
`{issuer}/.well-known/jwks.json`, and without it `verify_clerk_token` returns
None and every bearer token is rejected.

**2. Frontend.** `@clerk/nextjs` v7.9.0 is installed. Wrap the root layout in
`<ClerkProvider>`, add `clerkMiddleware()` in `middleware.js`, and have
`SessionProvider` attach `await getToken()` as the bearer instead of
`x-dev-user`. The `apiFetch` helper already takes a `token` option for exactly
this — no call site changes.

**3. Turn off development auth:**

```
DEV_AUTH_ENABLED=false
```

**4. Verify.** `GET /api/v1/health` reports `auth.clerk_configured: true`, and
`/signin` switches from the demo-user list to the Clerk flow automatically —
that page already branches on the health response.

**5. Role onboarding is unchanged.** A newly authenticated Clerk user has
`role: null` and is routed to `/app/role`. The role is written server-side by
`POST /api/v1/me/role`.

---

## 6. What is genuinely untested

| Item | Status |
|---|---|
| JWKS fetch and RS256 verification | **Untested against a live tenant.** Implemented in `verify_clerk_token`. |
| Clerk sign-up / sign-in / sign-out flows | **Untested.** No tenant available. |
| Token refresh and expiry | **Untested.** |
| Clerk webhooks (user deletion, email change) | **Not implemented.** Out of scope for this run. |
| Server-side role enforcement | **Tested** — but via the development auth path, not Clerk. The role lookup and `require_role` logic are identical for both, so what is untested is specifically token verification, not authorization. |

---

## 7. Removing Kinde

Kinde is **not in any active path**. `@kinde-oss/kinde-auth-nextjs` is still in
`package.json` and the two route handlers still exist, both classed `DEPRECATE`
in `LEGACY_MIGRATION_MAP.md`. They were left rather than deleted so the legacy
app stays runnable for reference; removal is a follow-up, not a blocker.

**Verified:** no file under `server/app/` or `client/src/app/app/` imports
anything from `@kinde-oss`.
