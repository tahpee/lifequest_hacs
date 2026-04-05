"""Constants for the Lifequest integration."""

DOMAIN = "lifequest"

# Config entry keys
CONF_BASE_URL = "base_url"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # seconds
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes — re-auth if token expires within this

# API endpoints
AUTH_LOGIN = "/api/auth/login"
USERS_PLAYERS = "/api/users/players"
USERS_PLAYER_DETAIL = "/api/users/players/{player_id}"
QUESTS = "/api/quests"
QUESTS_COMPLETE = "/api/quests/{quest_id}/complete"
POINTS_PROGRESS = "/api/points/progress"
LEVELS = "/api/levels"

# Events
EVENT_QUEST_COMPLETED = "lifequest_quest_completed"
EVENT_PLAYER_LEVELED_UP = "lifequest_player_leveled_up"

# Services
SERVICE_COMPLETE_QUEST = "complete_quest"
SERVICE_REFRESH_DATA = "refresh_data"
