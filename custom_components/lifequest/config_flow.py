"""Config flow for Lifequest integration."""

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .api import LifequestAPI, LifequestAPIError
from .const import CONF_BASE_URL, DOMAIN


class LifequestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lifequest."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                api = LifequestAPI(
                    user_input[CONF_BASE_URL],
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                try:
                    await api.authenticate()
                    await api.get_players()
                finally:
                    await api.close()

                return self.async_create_entry(
                    title=f"Lifequest ({user_input[CONF_BASE_URL]})",
                    data=user_input,
                )
            except LifequestAPIError as err:
                if err.status == 401:
                    errors["base"] = "invalid_auth"
                elif err.status == 403:
                    errors["base"] = "not_admin"
                else:
                    errors["base"] = "unknown"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_URL): str,
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
