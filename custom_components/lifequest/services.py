"""Service definitions for Lifequest integration."""

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import LifequestAPI, LifequestAPIError
from .const import (
    DOMAIN,
    EVENT_QUEST_COMPLETED,
    SERVICE_COMPLETE_QUEST,
    SERVICE_REFRESH_DATA,
    SERVICE_DELIVER_REWARD,
)
from .coordinator import LifequestCoordinator


SERVICE_SCHEMA_COMPLETE_QUEST = vol.Schema(
    {
        vol.Required("player_id"): cv.positive_int,
        vol.Required("quest_id"): cv.positive_int,
    }
)

SERVICE_SCHEMA_DELIVER_REWARD = vol.Schema(
    {
        vol.Required("cycle_id"): cv.positive_int,
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register Lifequest services."""

    async def handle_complete_quest(call: ServiceCall) -> None:
        """Handle the complete_quest service call."""
        player_id = call.data["player_id"]
        quest_id = call.data["quest_id"]

        entries = hass.data.get(DOMAIN, {})
        if not entries:
            raise HomeAssistantError("Lifequest integration not configured")

        coordinator: LifequestCoordinator = next(iter(entries.values()))
        api: LifequestAPI = coordinator.api

        player_name = "Unknown"
        if coordinator.data and player_id in coordinator.data:
            player_name = coordinator.data[player_id]["name"]

        quest_title = "Unknown"
        if coordinator.data and player_id in coordinator.data:
            for q in coordinator.data[player_id].get("quests", []):
                if q.get("id") == quest_id:
                    quest_title = q.get("title", "Unknown")
                    break

        try:
            result = await api.complete_quest(quest_id, player_id=player_id)
        except LifequestAPIError as err:
            raise HomeAssistantError(f"Failed to complete quest: {err}") from err

        points_awarded = result.get("points_awarded", 0)

        hass.bus.async_fire(
            EVENT_QUEST_COMPLETED,
            {
                "player_id": player_id,
                "player_name": player_name,
                "quest_id": quest_id,
                "quest_title": quest_title,
                "points_awarded": points_awarded,
            },
        )

        await coordinator.async_request_refresh()

    async def handle_refresh_data(call: ServiceCall) -> None:
        """Handle the refresh_data service call."""
        entries = hass.data.get(DOMAIN, {})
        if not entries:
            raise HomeAssistantError("Lifequest integration not configured")

        coordinator: LifequestCoordinator = next(iter(entries.values()))
        await coordinator.async_request_refresh()

    async def handle_deliver_reward(call: ServiceCall) -> None:
        """Handle the deliver_reward service call."""
        cycle_id = call.data["cycle_id"]

        entries = hass.data.get(DOMAIN, {})
        if not entries:
            raise HomeAssistantError("Lifequest integration not configured")

        coordinator: LifequestCoordinator = next(iter(entries.values()))
        api: LifequestAPI = coordinator.api

        try:
            await api.deliver_reward(cycle_id)
        except LifequestAPIError as err:
            raise HomeAssistantError(f"Failed to deliver reward: {err}") from err

        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_QUEST,
        handle_complete_quest,
        schema=SERVICE_SCHEMA_COMPLETE_QUEST,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_DATA,
        handle_refresh_data,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELIVER_REWARD,
        handle_deliver_reward,
        schema=SERVICE_SCHEMA_DELIVER_REWARD,
    )
