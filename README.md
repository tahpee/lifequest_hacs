# Lifequest Home Assistant Integration

A HACS custom integration that connects Home Assistant to a Lifequest server.

## Features

- Sensor entities per player: points, level, available quests, completions today
- Custom Lovelace card for interactive quest dashboard
- Service calls for completing quests from HA automations
- Events for quest completions and level-ups

## Installation

1. Add this repository to HACS as a custom repository
2. Install the "Lifequest" integration
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration → "Lifequest"
5. Enter your Lifequest server URL, admin email, and admin password

## Configuration

The integration is configured via the UI config flow. No YAML configuration needed.

## Sensors

For each player, the following sensors are created:

| Sensor | State | Key Attributes |
|--------|-------|----------------|
| `sensor.lifequest_{name}_points` | Current points | `threshold`, `level`, `progress_pct` |
| `sensor.lifequest_{name}_level` | Current level | `level_name` |
| `sensor.lifequest_{name}_quests_available` | Quest count | `quests` (full list) |
| `sensor.lifequest_{name}_completions_today` | Today's completions | `completions` |

## Services

| Service | Parameters | Description |
|---------|-----------|-------------|
| `lifequest.complete_quest` | `player_id`, `quest_id` | Complete a quest |
| `lifequest.refresh_data` | none | Force data refresh |

## Lovelace Card

```yaml
type: custom:lifequest-card
```
