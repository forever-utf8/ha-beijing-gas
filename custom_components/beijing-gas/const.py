"""Constants for the 北京燃气信息查询 integration."""

from homeassistant.const import Platform

DOMAIN = "beijing-gas"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_TOKEN = "token"
CONF_USER_CODE = "user_code"
