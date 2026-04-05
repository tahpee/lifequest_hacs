"""Lifequest API client."""

from datetime import datetime, timedelta, timezone
import aiohttp

from .const import (
    AUTH_LOGIN,
    LEVELS,
    REWARDS_PENDING,
    REWARDS_DELIVER,
    USERS_PLAYERS,
    USERS_PLAYER_DETAIL,
    QUESTS,
    QUESTS_COMPLETE,
    POINTS_PROGRESS,
    TOKEN_EXPIRY_BUFFER,
)


class LifequestAPIError(Exception):
    """Base exception for Lifequest API errors."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class LifequestAPI:
    """Async client for the Lifequest REST API."""

    def __init__(self, base_url: str, email: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._token: str | None = None
        self._token_expiry: datetime | None = None
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _ensure_authenticated(self) -> str:
        """Return a valid JWT token, re-authenticating if needed."""
        if self._token and self._token_expiry:
            now = datetime.now(timezone.utc)
            if now < self._token_expiry - timedelta(seconds=TOKEN_EXPIRY_BUFFER):
                return self._token
        await self.authenticate()
        return self._token

    async def authenticate(self) -> dict:
        """Authenticate with the Lifequest server."""
        session = await self._get_session()
        url = f"{self._base_url}{AUTH_LOGIN}"
        async with session.post(
            url, json={"email": self._email, "password": self._password}
        ) as resp:
            if resp.status == 401:
                raise LifequestAPIError("Invalid email or password", 401)
            if resp.status != 200:
                raise LifequestAPIError(
                    f"Authentication failed: HTTP {resp.status}", resp.status
                )
            data = await resp.json()
            self._token = data["token"]
            self._token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
            return data

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        """Make an authenticated API request."""
        token = await self._ensure_authenticated()
        session = await self._get_session()
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self._token}"
                async with session.request(
                    method, url, headers=headers, **kwargs
                ) as retry_resp:
                    if retry_resp.status != 200:
                        body = await retry_resp.text()
                        raise LifequestAPIError(f"API error: {body}", retry_resp.status)
                    return await retry_resp.json()
            if resp.status != 200:
                body = await resp.text()
                raise LifequestAPIError(f"API error: {body}", resp.status)
            return await resp.json()

    async def get_players(self) -> list[dict]:
        """Fetch all players (admin endpoint)."""
        return await self._request("GET", USERS_PLAYERS)

    async def get_player_detail(self, player_id: int) -> dict:
        """Fetch detail for a single player."""
        path = USERS_PLAYER_DETAIL.format(player_id=player_id)
        return await self._request("GET", path)

    async def get_player_quests(self, player_id: int) -> list[dict]:
        """Fetch assigned quests for a player."""
        return await self._request("GET", QUESTS, params={"player_id": str(player_id)})

    async def complete_quest(self, quest_id: int, player_id: int | None = None) -> dict:
        """Complete a quest."""
        path = QUESTS_COMPLETE.format(quest_id=quest_id)
        json_data = {"player_id": player_id} if player_id else None
        return await self._request("POST", path, json=json_data)

    async def get_points_progress(self, player_id: int) -> dict:
        """Fetch points progress for a player."""
        return await self._request(
            "GET", POINTS_PROGRESS, params={"player_id": str(player_id)}
        )

    async def get_levels(self) -> list[dict]:
        """Fetch all level names."""
        return await self._request("GET", LEVELS)

    async def get_pending_rewards(self) -> list[dict]:
        """Fetch all pending (undelivered) rewards."""
        return await self._request("GET", REWARDS_PENDING)

    async def deliver_reward(self, cycle_id: int) -> dict:
        """Mark a reward as delivered."""
        path = REWARDS_DELIVER.format(cycle_id=cycle_id)
        return await self._request("PUT", path)
