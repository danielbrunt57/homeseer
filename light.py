"""
Support for HomeSeer light-type devices.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.homeseer/
"""
import logging

from homeassistant.components.light import (ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light)
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homeseer']


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up HomeSeer light-type devices."""
    from pyhs3 import HASS_LIGHTS

    light_devices = []
    homeseer = hass.data[DOMAIN]

    for device in homeseer.devices:
        if device.device_type_string in HASS_LIGHTS:
            dev = HSLight(device, homeseer)
            light_devices.append(dev)
            _LOGGER.info('Added HomeSeer light-type device: {}'.format(dev.name))

    async_add_entities(light_devices)


class HSLight(Light):
    """Representation of a HomeSeer light-type device."""
    def __init__(self, device, connection):
        self._device = device
        self._connection = connection

    @property
    def available(self):
        """Return whether the device is available."""
        from pyhs3 import STATE_LISTENING
        return self._connection.api.state == STATE_LISTENING

    @property
    def device_state_attributes(self):
        attr = {
            'Device Ref': self._device.ref
        }
        return attr

    @property
    def name(self):
        """Return the name of the device."""
        return self._device.name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._convert_to_hass_level(self._device.value)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._device.value > 0

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        percent = int(brightness/255 * 100)
        await self._device.dim(percent)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._device.off()

    def _convert_to_hass_level(self, value):
        """Determine state of HS light device as a percentage, then return that percentage of 255."""
        brightness = int((value / self._device.on_value) * 255)
        if brightness > 255:
            return 255
        else:
            return brightness

    async def async_added_to_hass(self):
        """Register value update callback."""
        self._device.register_update_callback(self.async_schedule_update_ha_state)