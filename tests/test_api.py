"""Tests for the Lifequest API client."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# We need to adjust the import path since we're testing from the repo root
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from custom_components.lifequest.api import LifequestAPI, LifequestAPIError


@pytest.fixture
def api():
    return LifequestAPI(
        base_url="http://localhost:3001",
        email="admin@family.com",
        password="admin123",
    )


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_authenticate_success(self, api):
        """Successful login stores token and expiry."""
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"token": "fake-jwt"})
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False

        with patch.object(api, "_get_session", return_value=mock_session):
            result = await api.authenticate()

        assert result["token"] == "fake-jwt"
        assert api._token == "fake-jwt"
        assert api._token_expiry is not None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self, api):
        """401 response raises LifequestAPIError."""
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.closed = False

        with patch.object(api, "_get_session", return_value=mock_session):
            with pytest.raises(LifequestAPIError, match="Invalid email or password"):
                await api.authenticate()


class TestEnsureAuthenticated:
    @pytest.mark.asyncio
    async def test_returns_existing_valid_token(self, api):
        """If token is still valid, returns it without re-auth."""
        api._token = "valid-token"
        api._token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
            token = await api._ensure_authenticated()

        assert token == "valid-token"
        mock_auth.assert_not_called()

    @pytest.mark.asyncio
    async def test_re_authenticates_when_expired(self, api):
        """If token is expired, re-authenticates."""
        api._token = "old-token"
        api._token_expiry = datetime.now(timezone.utc) - timedelta(seconds=1)

        with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"token": "new-token"}
            api._token = "new-token"
            token = await api._ensure_authenticated()

        mock_auth.assert_called_once()
        assert token == "new-token"


class TestGetPlayers:
    @pytest.mark.asyncio
    async def test_get_players_success(self, api):
        """Fetches player list from API."""
        players_data = [
            {"id": 1, "name": "Child A", "level": 3, "current_points": 120},
            {"id": 2, "name": "Child B", "level": 1, "current_points": 50},
        ]
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=players_data)
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)
        mock_session.closed = False

        api._token = "fake-token"
        api._token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch.object(api, "_get_session", return_value=mock_session):
            result = await api.get_players()

        assert len(result) == 2
        assert result[0]["name"] == "Child A"


class TestCompleteQuest:
    @pytest.mark.asyncio
    async def test_complete_quest_success(self, api):
        """Completes a quest successfully."""
        completion_data = {"message": "Quest completed", "points_awarded": 15}
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=completion_data)
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=mock_resp)
        mock_session.closed = False

        api._token = "fake-token"
        api._token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch.object(api, "_get_session", return_value=mock_session):
            result = await api.complete_quest(quest_id=42)

        assert result["points_awarded"] == 15
