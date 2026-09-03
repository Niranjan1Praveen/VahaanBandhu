"""Authentication and role authorization.

**Server-side role enforcement.** The role is read from the database record for
the authenticated identity, never from a header, body or client claim. The
legacy app trusted a client-supplied role; that is the specific hole this closes.

**Clerk is the production path.** `verify_clerk_token` validates the session
token against Clerk's JWKS.

**Development auth is a separate, clearly-marked path.** It exists so local UI
work, tests and screenshots do not require network access to Clerk. It is
guarded by `settings.demo_auth_active`, which requires BOTH `dev_auth_enabled`
and a non-production environment -- a single misconfigured variable cannot expose
it in production. It is never a fallback for a *failed* Clerk verification;
a bad token is always rejected.
"""

from __future__ import annotations

import logging

from fastapi import Depends, Header, HTTPException, status

from server.app.core.config import get_settings
from server.app.schemas.common import UserRole

log = logging.getLogger(__name__)

DEV_HEADER = "x-dev-user"
DEV_ROLE_HEADER = "x-dev-role"


class Identity:
    """An authenticated caller. `role` always comes from the database."""

    def __init__(self, user_id: str, email: str | None, role: UserRole | None,
                 source: str, onboarded: bool = False) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.source = source  # "clerk" | "dev"
        self.onboarded = onboarded

    def __repr__(self) -> str:  # pragma: no cover
        return f"Identity({self.user_id}, role={self.role}, via={self.source})"


async def verify_clerk_token(token: str) -> dict | None:
    """Validate a Clerk session token. Returns claims, or None if invalid.

    Uses Clerk's JWKS endpoint. A verification failure returns None so the
    caller rejects the request -- it never falls through to development auth.
    """
    s = get_settings()
    if not s.clerk_configured:
        return None
    try:
        import httpx
        from jose import jwt

        issuer = s.clerk_jwt_issuer.rstrip("/")
        if not issuer:
            return None
        async with httpx.AsyncClient(timeout=5.0) as client:
            jwks = (await client.get(f"{issuer}/.well-known/jwks.json")).json()
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks.get("keys", []) if k["kid"] == header.get("kid")), None)
        if key is None:
            return None
        return jwt.decode(token, key, algorithms=["RS256"], issuer=issuer,
                          options={"verify_aud": False})
    except Exception as e:
        log.warning("clerk token verification failed: %s", type(e).__name__)
        return None


async def get_identity(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None, alias=DEV_HEADER),
) -> Identity:
    """Resolve the caller, or raise 401.

    Order matters: a presented bearer token is *always* verified against Clerk
    and rejected on failure. Development auth applies only when no bearer token
    was presented at all.
    """
    from server.app.repositories.user_repo import user_repo
    s = get_settings()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = await verify_clerk_token(token)
        if claims is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token.")
        clerk_id = claims.get("sub")
        user = await user_repo.get_by_clerk_id(clerk_id)
        return Identity(
            user_id=clerk_id,
            email=(user or {}).get("email") or claims.get("email"),
            # Role from the database, never from the token payload.
            role=UserRole(user["role"]) if user and user.get("role") else None,
            source="clerk",
            onboarded=bool(user and user.get("role")),
        )

    if s.demo_auth_active and x_dev_user:
        user = await user_repo.get_by_clerk_id(x_dev_user)
        return Identity(
            user_id=x_dev_user,
            email=(user or {}).get("email"),
            role=UserRole(user["role"]) if user and user.get("role") else None,
            source="dev",
            onboarded=bool(user and user.get("role")),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: UserRole):
    """Dependency enforcing that the caller holds one of `roles`.

    Server-side. A client cannot reach a farmer endpoint by claiming to be a
    farmer; the role is whatever the database says it is.
    """

    async def _dep(identity: Identity = Depends(get_identity)) -> Identity:
        if identity.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role onboarding is not complete.")
        if identity.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires role: {', '.join(r.value for r in roles)}.")
        return identity

    return _dep
