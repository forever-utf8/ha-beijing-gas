"""Config flow for 北京燃气信息查询."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONF_USER_CODE, DOMAIN
from .gas import GASData

type UserInput = dict[str, str]


def _data_schema(defaults: UserInput | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_USER_CODE, default=defaults.get(CONF_USER_CODE, "")): str,
            vol.Required(CONF_TOKEN, default=defaults.get(CONF_TOKEN, "")): str,
        }
    )


async def _validate_input(hass: HomeAssistant, data: UserInput) -> str:
    user_code = data[CONF_USER_CODE]
    token = data[CONF_TOKEN]
    result = await GASData(async_create_clientsession(hass), token, user_code).async_get_data()
    result[user_code]
    return user_code


class BJGasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for beijing-gas."""

    VERSION = 1

    async def async_step_user(self, user_input: UserInput | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_data_schema())

        user_code = await _validate_input(self.hass, user_input)
        await self.async_set_unique_id(user_code)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"北京燃气 {user_code}",
            data={CONF_TOKEN: user_input[CONF_TOKEN], CONF_USER_CODE: user_code},
        )
