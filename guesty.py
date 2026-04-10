"""
Guesty API client.
Uses OAuth 2.0 client_credentials flow to get an access token,
then fetches reservations, listings, and review data.
"""

import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

GUESTY_API_BASE = "https://open-api.guesty.com/v1"
GUESTY_TOKEN_URL = "https://open-api.guesty.com/oauth2/token"

# Persist token to disk so restarts don't trigger a fresh OAuth call
TOKEN_CACHE_FILE = Path("guesty_token_cache.json")


class GuestyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        # Try to restore cached token from disk on startup
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._load_token_cache()

    def _load_token_cache(self):
        """Restore token from disk cache (survives restarts)."""
        try:
            if TOKEN_CACHE_FILE.exists():
                data = json.loads(TOKEN_CACHE_FILE.read_text())
                if data.get("expires_at", 0) > time.time() + 120:
                    self._access_token = data["access_token"]
                    self._token_expires_at = data["expires_at"]
                    logger.info("✅ Guesty token restored from disk cache")
        except Exception as e:
            logger.warning(f"Could not load Guesty token cache: {e}")

    def _save_token_cache(self):
        """Write token to disk so next restart can reuse it."""
        try:
            TOKEN_CACHE_FILE.write_text(json.dumps({
                "access_token": self._access_token,
                "expires_at": self._token_expires_at,
            }))
        except Exception as e:
            logger.warning(f"Could not save Guesty token cache: {e}")

    async def _get_access_token(self) -> str:
        """Fetch (or return cached) OAuth access token. Persists to disk to survive restarts."""
        if self._access_token and time.time() < self._token_expires_at - 120:
            return self._access_token

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                GUESTY_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "scope": "open-api",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600)
            self._save_token_cache()
            logger.info("✅ Guesty access token refreshed and saved to disk")
            return self._access_token

    async def _headers(self) -> dict:
        token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_today_checkouts(self) -> list[dict]:
        """Get all reservations checking out today — need cleaning."""
        today = date.today().isoformat()
        return await self._get_reservations(checkout_date=today, status="checked_out")

    async def get_tomorrow_checkouts(self) -> list[dict]:
        """Get reservations checking out tomorrow — plan ahead."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return await self._get_reservations(checkout_date=tomorrow)

    async def get_today_checkins(self) -> list[dict]:
        """Get reservations checking in today — need to be ready."""
        today = date.today().isoformat()
        return await self._get_reservations(checkin_date=today)

    async def get_reservations_with_bad_reviews(self,
                                                 days_back: int = 30,
                                                 min_rating: float = 3.5) -> list[dict]:
        """
        Get listings that had bad reviews recently (below min_rating).
        These get a warning sent before the cleaner arrives.
        """
        recent_reviews = await self.get_recent_reviews(days_back=days_back)
        bad = [r for r in recent_reviews if r.get("rating", 5) <= min_rating]
        logger.info(f"Found {len(bad)} bad reviews (≤{min_rating}★) in last {days_back} days")
        return bad

    async def get_recent_reviews(self, days_back: int = 30) -> list[dict]:
        """Fetch reviews from the last N days."""
        from_date = (date.today() - timedelta(days=days_back)).isoformat()
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{GUESTY_API_BASE}/reviews",
                    headers=await self._headers(),
                    params={"from": from_date, "limit": 100}
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except Exception as e:
                logger.error(f"❌ Failed to fetch reviews: {e}")
                return []

    async def get_new_5star_reviews(self, hours_back: int = 24) -> list[dict]:
        """Get 5-star reviews posted in the last N hours — celebrate these!"""
        reviews = await self.get_recent_reviews(days_back=2)
        return [r for r in reviews if r.get("rating", 0) >= 5]

    async def get_listing(self, listing_id: str) -> Optional[dict]:
        """Get listing details by ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{GUESTY_API_BASE}/listings/{listing_id}",
                    headers=await self._headers()
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"❌ Failed to fetch listing {listing_id}: {e}")
                return None

    async def get_todays_cleaning_tasks(self) -> list[dict]:
        """
        Fetch today's 'Turnover Cleaning' tasks from the Guesty Tasks API.

        These tasks are manually curated in Guesty — far more accurate than
        raw checkouts, because guests who extend their stay are removed.
        Each task has assigneeId + assigneeFullName already set.

        Filters applied (server-side where supported, client-side as fallback):
        - canStartAfter falls on today (the checkout/handover date)
        - title contains 'turnover' (case-insensitive)
        - status is not completed or canceled
        """
        today_start = f"{date.today().isoformat()}T00:00:00.000Z"
        today_end   = f"{date.today().isoformat()}T23:59:59.999Z"

        params = {
            "limit": 100,
            "skip": 0,
            # Try the most common Guesty date range param names.
            # If these don't filter server-side, we fall back to client-side.
            "canStartAfterFrom": today_start,
            "canStartAfterTo":   today_end,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{GUESTY_API_BASE}/tasks",
                    headers=await self._headers(),
                    params=params
                )
                resp.raise_for_status()
                data = resp.json()
                all_tasks = data.get("results", data if isinstance(data, list) else [])
                logger.info(f"📋 Raw tasks from API: {len(all_tasks)}")

                # Client-side filters as safety net
                today_date = date.today().isoformat()  # "2026-04-10"
                filtered = []
                for t in all_tasks:
                    status = t.get("status", "")
                    if status in ("completed", "canceled"):
                        continue
                    title = t.get("title", "").lower()
                    if "turnover" not in title:
                        continue
                    # Ensure canStartAfter falls on today
                    can_start = t.get("canStartAfter") or t.get("startTime") or ""
                    if can_start and today_date not in can_start[:10]:
                        continue
                    filtered.append(t)

                logger.info(f"📋 Today's turnover cleaning tasks: {len(filtered)}")
                return filtered
            except Exception as e:
                logger.error(f"❌ Failed to fetch tasks: {e}")
                return []

    async def get_all_listings(self) -> list[dict]:
        """Get all active listings."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{GUESTY_API_BASE}/listings",
                    headers=await self._headers(),
                    params={"limit": 100, "active": True}
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
            except Exception as e:
                logger.error(f"❌ Failed to fetch listings: {e}")
                return []

    async def _get_reservations(self,
                                 checkout_date: Optional[str] = None,
                                 checkin_date: Optional[str] = None,
                                 status: Optional[str] = None) -> list[dict]:
        """Internal reservation fetcher with filters."""
        params = {"limit": 100}
        if checkout_date:
            params["checkOut"] = checkout_date
        if checkin_date:
            params["checkIn"] = checkin_date
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{GUESTY_API_BASE}/reservations",
                    headers=await self._headers(),
                    params=params
                )
                resp.raise_for_status()
                data = resp.json()
                reservations = data.get("results", data if isinstance(data, list) else [])
                logger.info(f"📋 Fetched {len(reservations)} reservations")
                return reservations
            except Exception as e:
                logger.error(f"❌ Guesty API error: {e}")
                return []


def prioritize_cleaning_tasks(reservations: list[dict]) -> list[dict]:
    """
    Sort cleaning tasks by priority:
    1. Same-day checkout + same-day checkin (back-to-back) — URGENT
    2. Same-day checkout only — HIGH
    3. Departure cleaning for tomorrow — NORMAL
    """
    today = date.today().isoformat()

    def priority(r: dict) -> int:
        checkout = r.get("checkOut", "")[:10]
        checkin = r.get("checkIn", "")[:10]
        # Back-to-back: checkout today AND checkin today
        if checkout == today and checkin == today:
            return 0  # Most urgent
        elif checkout == today:
            return 1
        else:
            return 2

    return sorted(reservations, key=priority)
