"""The 北京燃气信息查询 integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_USER_CODE, DOMAIN, PLATFORMS
from .gas import GASData

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=10)

type BJGasData = dict[str, dict]


async def async_setup(_hass: HomeAssistant, _config: dict) -> bool:
    """Set up beijing-gas."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up beijing-gas from a config entry."""
    token: str = entry.data[CONF_TOKEN]
    user_code: str = entry.data[CONF_USER_CODE]
    coordinator = BJGasDataUpdateCoordinator(hass, token=token, user_code=user_code)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class BJGasDataUpdateCoordinator(DataUpdateCoordinator[BJGasData]):
    """Coordinator to manage fetching data from Beijing Gas APIs."""

    user_code: str

    def __init__(self, hass: HomeAssistant, *, token: str, user_code: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.user_code = user_code
        self._gas = GASData(async_create_clientsession(hass), token, user_code)

    async def _async_update_data(self) -> BJGasData:
        return await self._gas.async_get_data()
