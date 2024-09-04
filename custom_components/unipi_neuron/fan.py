"""Platform for fan integration."""
import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.fan import (
    FanEntity,
    SUPPORT_SET_SPEED,
    PLATFORM_SCHEMA,
    ATTR_PERCENTAGE
)


from homeassistant.const import (
    CONF_DEVICE,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_NAME,
    CONF_PORT,
    CONF_MODE
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from homeassistant.components.fan import FanEntityFeature

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE): vol.Any("ao"),
        vol.Required(CONF_PORT): cv.matches_regex(r"^[1-3]_[0-1][0-9]|[1-8]"),
        vol.Required(CONF_MODE): vol.Any("on_off", "pwm"),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_SCHEMA]),
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Unipi Fans."""
    _LOGGER.info("Setup platform Unipi Neuron fan on %s", config)
    unipi_device_name = config[CONF_DEVICE_ID]
    fans = []
    for fan in config[CONF_DEVICES]:
        fans.append(
            UnipiFan(
                hass.data[DOMAIN][unipi_device_name],
                fan[CONF_NAME],
                fan[CONF_PORT],
                fan[CONF_DEVICE],
                fan[CONF_MODE],
            )
        )

    async_add_entities(fans)
    return

class UnipiFan(FanEntity):
    """Representation of a Unipi Fan."""

    def __init__(self, unipi_hub, name, port, device, mode):
        """Initialize the Unipi Fan."""
        self._unipi_hub = unipi_hub
        self._name = name
        self._port = port
        self._device = device
        self._mode = mode
        self._percentage = 0
        self._preset_mode = "auto"

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED 

    @property
    def name(self):
        """Return the display name of this fan."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the fan."""
        return self._percentage > 0

    @property
    def percentage(self):
        """Return the relative speed."""
        return self._percentage

    async def async_set_percentage(self, percentage: int):
        """Set the speed of the fan."""
        self._percentage = percentage
        dict_to_send = {"frequency": 100, "value": self.get_ao_value_from_percentage(self._percentage)}
        await self._unipi_hub.evok_send(self._device, self._port, dict_to_send)

    def get_ao_value_from_percentage(self, percentage):
        percentage = min(percentage, 100)
        percentage = max(0, percentage)
        return 10 - percentage / 10

    async def async_turn_on(self, **kwargs):
        """Instruct the fan to turn on."""

        self._percentage = kwargs.get(ATTR_PERCENTAGE, 100)
        # self._preset_mode = kwargs.get(ATTR_PRESET_MODE, "auto")
        # self._oscillating = kwargs.get(ATTR_OSCILLATING, False)
        # self._direction = kwargs.get(ATTR_DIRECTION, "forward")
        dict_to_send = {"frequency": 100, "value": self.get_ao_value_from_percentage(self._percentage)}
        await self._unipi_hub.evok_send(self._device, self._port, dict_to_send)

    async def async_turn_off(self, **kwargs):
        """Instruct the fan to turn off."""
        self._percentage = 0
        dict_to_send = {"frequency": 100, "value": self.get_ao_value_from_percentage(self._percentage)}
        await self._unipi_hub.evok_send(self._device, self._port, dict_to_send)
