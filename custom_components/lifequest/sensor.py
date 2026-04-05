"""Sensor platform for Lifequest."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LifequestCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lifequest sensor entities."""
    coordinator: LifequestCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data is None:
        return

    entities: list[SensorEntity] = []
    for player_id, player_data in coordinator.data.items():
        name = player_data["name"]
        slug = name.lower().replace(" ", "_")
        entities.extend(
            [
                LifequestPointsSensor(coordinator, player_id, slug),
                LifequestLevelSensor(coordinator, player_id, slug),
                LifequestQuestsAvailableSensor(coordinator, player_id, slug),
                LifequestCompletionsTodaySensor(coordinator, player_id, slug),
            ]
        )

    async_add_entities(entities)


class LifequestBaseSensor(CoordinatorEntity[LifequestCoordinator], SensorEntity):
    """Base class for Lifequest sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LifequestCoordinator,
        player_id: int,
        slug: str,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._player_id = player_id
        self._sensor_key = sensor_key
        self._attr_unique_id = f"lifequest_{slug}_{sensor_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"player_{player_id}")},
            name=coordinator.data[player_id]["name"],
            manufacturer="Lifequest",
        )

    def _get_player(self) -> dict | None:
        """Get current player data from coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._player_id)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self._get_player() is not None


class LifequestPointsSensor(LifequestBaseSensor):
    """Sensor for player's current points."""

    _attr_name = "Points"
    _attr_icon = "mdi:star"
    _attr_native_unit_of_measurement = "pts"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, player_id, slug) -> None:
        super().__init__(coordinator, player_id, slug, "points")

    @property
    def native_value(self) -> int | None:
        player = self._get_player()
        if player is None:
            return None
        return player["current_points"]

    @property
    def extra_state_attributes(self) -> dict:
        player = self._get_player()
        if player is None:
            return {}
        threshold = player["reward_threshold"]
        points = player["current_points"]
        return {
            "threshold": threshold,
            "points_to_reward": max(0, threshold - points),
            "level": player["level"],
            "progress_pct": round((points / threshold * 100), 1) if threshold else 0,
        }


class LifequestLevelSensor(LifequestBaseSensor):
    """Sensor for player's current level."""

    _attr_name = "Level"
    _attr_icon = "mdi:trophy"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, player_id, slug) -> None:
        super().__init__(coordinator, player_id, slug, "level")

    @property
    def native_value(self) -> int | None:
        player = self._get_player()
        if player is None:
            return None
        return player["level"]

    @property
    def extra_state_attributes(self) -> dict:
        player = self._get_player()
        if player is None:
            return {}
        return {
            "player_id": self._player_id,
            "level_name": player.get("level_name", ""),
        }


class LifequestQuestsAvailableSensor(LifequestBaseSensor):
    """Sensor for player's available quest count."""

    _attr_name = "Quests Available"
    _attr_icon = "mdi:checkbox-marked-circle-outline"

    def __init__(self, coordinator, player_id, slug) -> None:
        super().__init__(coordinator, player_id, slug, "quests_available")

    @property
    def native_value(self) -> int | None:
        player = self._get_player()
        if player is None:
            return None
        return len(player.get("quests", []))

    @property
    def extra_state_attributes(self) -> dict:
        player = self._get_player()
        if player is None:
            return {}
        quests = player.get("quests", [])
        return {
            "quests": [
                {
                    "id": q.get("id"),
                    "title": q.get("title", ""),
                    "points": q.get("points", 0),
                    "frequency": q.get("frequency", ""),
                    "repeatable": q.get("repeatable", False),
                    "description": q.get("description", ""),
                    "completed_today": q.get("completed_today", 0),
                }
                for q in quests
            ]
        }


class LifequestCompletionsTodaySensor(LifequestBaseSensor):
    """Sensor for player's completions today."""

    _attr_name = "Completions Today"
    _attr_icon = "mdi:check-circle"

    def __init__(self, coordinator, player_id, slug) -> None:
        super().__init__(coordinator, player_id, slug, "completions_today")

    @property
    def native_value(self) -> int | None:
        player = self._get_player()
        if player is None:
            return None
        completions = player.get("completions", [])
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            1 for c in completions if c.get("completed_at", "").startswith(today)
        )

    @property
    def extra_state_attributes(self) -> dict:
        player = self._get_player()
        if player is None:
            return {}
        completions = player.get("completions", [])
        today = datetime.now().strftime("%Y-%m-%d")
        today_completions = [
            c for c in completions if c.get("completed_at", "").startswith(today)
        ]
        return {
            "completions": [
                {
                    "quest_id": c.get("quest_id"),
                    "quest_title": c.get("quest_title", ""),
                    "points_awarded": c.get("points_awarded", 0),
                    "completed_at": c.get("completed_at", ""),
                }
                for c in today_completions
            ]
        }
