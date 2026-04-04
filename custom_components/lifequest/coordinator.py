"""DataUpdateCoordinator for Lifequest."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LifequestAPI, LifequestAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LifequestCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to poll Lifequest data."""

    def __init__(self, hass: HomeAssistant, api: LifequestAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        """Fetch all player data from Lifequest."""
        try:
            players = await self.api.get_players()
            data = {}
            for player in players:
                player_id = player["id"]
                try:
                    detail = await self.api.get_player_detail(player_id)
                    quests = detail.get("assignedQuests", [])
                    completions = detail.get("completions", [])
                except LifequestAPIError:
                    quests = []
                    completions = []
                    _LOGGER.warning("Failed to fetch detail for player %s", player_id)
                data[player_id] = {
                    "id": player_id,
                    "name": player.get("name", f"Player {player_id}"),
                    "email": player.get("email", ""),
                    "level": player.get("level", 1),
                    "current_points": player.get("current_points", 0),
                    "reward_threshold": player.get("reward_threshold", 250),
                    "avatar_url": player.get("avatar_url"),
                    "active_quests": player.get("active_quests", 0),
                    "quests": quests,
                    "completions": completions,
                }
            return data
        except LifequestAPIError as err:
            raise UpdateFailed(f"Error fetching Lifequest data: {err}") from err
