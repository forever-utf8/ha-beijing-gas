"""Sensor entities for 北京燃气信息查询."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BJGasDataUpdateCoordinator
from .const import DOMAIN

type UserData = dict


@dataclass(frozen=True, kw_only=True, slots=True)
class BJGasSensorEntityDescription(SensorEntityDescription):
    """Describe a bj_gas sensor entity."""

    value_key: str
    extra_attributes: tuple[str, ...] = ()


SENSOR_DESCRIPTIONS: tuple[BJGasSensorEntityDescription, ...] = (
    BJGasSensorEntityDescription(
        key="balance",
        translation_key="balance",
        icon="hass:cash-100",
        native_unit_of_measurement="元",
        value_key="balance",
        extra_attributes=("last_update",),
    ),
    BJGasSensorEntityDescription(
        key="current_level",
        translation_key="current_level",
        icon="hass:stairs",
        value_key="current_level",
    ),
    BJGasSensorEntityDescription(
        key="current_price",
        translation_key="current_price",
        icon="hass:cash-100",
        native_unit_of_measurement="元/m³",
        value_key="current_price",
    ),
    BJGasSensorEntityDescription(
        key="current_level_remain",
        translation_key="current_level_remain",
        device_class=SensorDeviceClass.GAS,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_key="current_level_remain",
    ),
    BJGasSensorEntityDescription(
        key="year_consume",
        translation_key="year_consume",
        device_class=SensorDeviceClass.GAS,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL,
        value_key="year_consume",
    ),
    BJGasSensorEntityDescription(
        key="month_reg_qty",
        translation_key="month_reg_qty",
        device_class=SensorDeviceClass.GAS,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL,
        value_key="month_reg_qty",
    ),
    BJGasSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_key="battery_voltage",
    ),
    BJGasSensorEntityDescription(
        key="mtr_status",
        translation_key="mtr_status",
        value_key="mtr_status",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: BJGasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    user_code = coordinator.user_code
    user_data = coordinator.data[user_code]

    entities: list[SensorEntity] = [BJGasSensor(coordinator, user_code, description) for description in SENSOR_DESCRIPTIONS]
    entities += [BJGasMonthlyHistorySensor(coordinator, user_code, index) for index, _ in enumerate(user_data["monthly_bills"], start=1)]
    entities += [BJGasDailyHistorySensor(coordinator, user_code, index) for index, _ in enumerate(user_data["daily_bills"], start=1)]
    async_add_entities(entities)


class BJGasBaseSensor(CoordinatorEntity[BJGasDataUpdateCoordinator], SensorEntity):
    """Base entity for bj_gas sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BJGasDataUpdateCoordinator, user_code: str) -> None:
        super().__init__(coordinator)
        self._user_code = user_code

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._user_code)},
            name=f"北京燃气 {self._user_code}",
            manufacturer="北京燃气",
            model="智能物联网燃气表",
        )

    @property
    def _user_data(self) -> UserData:
        return self.coordinator.data[self._user_code]


class BJGasSensor(BJGasBaseSensor):
    """Regular summary sensor for bj_gas."""

    entity_description: BJGasSensorEntityDescription

    def __init__(
        self,
        coordinator: BJGasDataUpdateCoordinator,
        user_code: str,
        description: BJGasSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, user_code)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{user_code}_{description.key}"

    @property
    def native_value(self):
        return self._user_data[self.entity_description.value_key]

    @property
    def extra_state_attributes(self) -> dict | None:
        if not self.entity_description.extra_attributes:
            return None
        return {key: self._user_data[key] for key in self.entity_description.extra_attributes}


class BJGasMonthlyHistorySensor(BJGasBaseSensor):
    """Monthly history sensor."""

    _attr_device_class = SensorDeviceClass.GAS
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(self, coordinator: BJGasDataUpdateCoordinator, user_code: str, index: int) -> None:
        super().__init__(coordinator, user_code)
        self._index = index
        self._attr_unique_id = f"{DOMAIN}_{user_code}_monthly_{index}"
        self._attr_translation_key = f"monthly_{index}"

    @property
    def _monthly_bill(self) -> dict:
        return self._user_data["monthly_bills"][self._index - 1]

    @property
    def native_value(self):
        return self._monthly_bill["regQty"]

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "month": self._monthly_bill["mon"],
            "consume_bill": self._monthly_bill["amt"],
        }


class BJGasDailyHistorySensor(BJGasBaseSensor):
    """Daily history sensor."""

    _attr_device_class = SensorDeviceClass.GAS
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(self, coordinator: BJGasDataUpdateCoordinator, user_code: str, index: int) -> None:
        super().__init__(coordinator, user_code)
        self._index = index
        self._attr_unique_id = f"{DOMAIN}_{user_code}_daily_{index}"
        self._attr_translation_key = f"daily_{index}"

    @property
    def _daily_bill(self) -> dict:
        return self._user_data["daily_bills"][self._index - 1]

    @property
    def native_value(self):
        return self._daily_bill["regQty"]

    @property
    def extra_state_attributes(self) -> dict:
        return {"day": self._daily_bill["day"]}
