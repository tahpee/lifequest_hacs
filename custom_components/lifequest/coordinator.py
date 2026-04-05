"""DataUpdateCoordinator for Lifequest."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LifequestAPI, LifequestAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, EVENT_REWARD_PENDING

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
        self._known_reward_cycle_ids: set[int] = set()

    async def _async_update_data(self) -> dict:
        """Fetch all player data from Lifequest."""
        try:
            players = await self.api.get_players()

            # Fetch level names
            try:
                levels_list = await self.api.get_levels()
                level_names = {l["level"]: l["name"] for l in levels_list}
            except LifequestAPIError:
                level_names = {}
                _LOGGER.warning("Failed to fetch level names")

            # Fetch pending rewards
            try:
                pending_rewards = await self.api.get_pending_rewards()
            except LifequestAPIError:
                pending_rewards = []
                _LOGGER.warning("Failed to fetch pending rewards")

            # Detect new rewards and fire events
            current_cycle_ids = {r["id"] for r in pending_rewards}
            new_cycle_ids = current_cycle_ids - self._known_reward_cycle_ids
            for reward in pending_rewards:
                if reward["id"] in new_cycle_ids:
                    self.hass.bus.async_fire(
                        EVENT_REWARD_PENDING,
                        {
                            "cycle_id": reward["id"],
                            "player_id": reward["player_id"],
                            "player_name": reward.get("player_name", "Unknown"),
                            "level_name": reward.get("level_name", ""),
                            "level": reward.get("player_level", 0),
                        },
                    )
            self._known_reward_cycle_ids = current_cycle_ids

            data = {}
            for player in players:
                player_id = player["id"]
                player_level = player.get("level", 1)
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
                    "level": player_level,
                    "level_name": level_names.get(
                        player_level, f"Level {player_level}"
                    ),
                    "current_points": player.get("current_points", 0),
                    "reward_threshold": player.get("reward_threshold", 250),
                    "avatar_url": player.get("avatar_url"),
                    "active_quests": player.get("active_quests", 0),
                    "quests": quests,
                    "completions": completions,
                }

            # Store pending rewards at the top level of data
            data["_pending_rewards"] = pending_rewards
            return data
        except LifequestAPIError as err:
            raise UpdateFailed(f"Error fetching Lifequest data: {err}") from err
