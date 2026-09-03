"""User repository.

Role-specific profile data is **embedded** in the user document rather than kept
in separate collections: it is always read together with the user, is small, and
is never queried independently. That is the case MongoDB embedding is for.
"""

from __future__ import annotations

from datetime import datetime, timezone

from server.app.db.mongodb import USERS, mongo
from server.app.schemas.common import UserRole


class UserRepository:
    @property
    def col(self):
        return mongo.collection(USERS)

    async def get_by_clerk_id(self, clerk_user_id: str | None) -> dict | None:
        if not clerk_user_id:
            return None
        return await self.col.find_one({"clerk_user_id": clerk_user_id}, {"_id": 0})

    async def upsert(self, clerk_user_id: str, *, email: str | None = None,
                     first_name: str | None = None,
                     last_name: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"clerk_user_id": clerk_user_id},
            {
                "$set": {k: v for k, v in {
                    "email": email, "first_name": first_name, "last_name": last_name,
                    "updated_at": now,
                }.items() if v is not None},
                "$setOnInsert": {
                    "clerk_user_id": clerk_user_id, "created_at": now,
                    "role": None, "profile": {},
                },
            },
            upsert=True,
        )
        return await self.get_by_clerk_id(clerk_user_id)

    async def set_role(self, clerk_user_id: str, role: UserRole,
                       profile: dict | None = None) -> dict:
        """Complete role onboarding. The role lives here and only here."""
        await self.col.update_one(
            {"clerk_user_id": clerk_user_id},
            {"$set": {
                "role": role.value,
                "profile": profile or {},
                "onboarded_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        return await self.get_by_clerk_id(clerk_user_id)

    async def update_profile(self, clerk_user_id: str, profile: dict) -> dict:
        sets = {f"profile.{k}": v for k, v in profile.items()}
        sets["updated_at"] = datetime.now(timezone.utc)
        await self.col.update_one({"clerk_user_id": clerk_user_id}, {"$set": sets})
        return await self.get_by_clerk_id(clerk_user_id)

    async def count(self) -> int:
        return await self.col.count_documents({})


user_repo = UserRepository()
