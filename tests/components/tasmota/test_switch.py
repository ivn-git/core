"""The tests for the MQTT switch platform."""
import copy
import json

from hatasmota.const import CONF_ONLINE

from homeassistant.components import switch
from homeassistant.components.tasmota.const import DEFAULT_PREFIX
from homeassistant.const import ATTR_ASSUMED_STATE, STATE_OFF, STATE_ON

from .test_common import (
    help_test_availability,
    help_test_availability_discovery_update,
    help_test_availability_when_connection_lost,
    help_test_discovery_device_remove,
    help_test_discovery_removal,
    help_test_discovery_update_unchanged,
    help_test_entity_id_update_discovery_update,
    help_test_entity_id_update_subscriptions,
)

from tests.async_mock import patch
from tests.common import async_fire_mqtt_message
from tests.components.switch import common

DEFAULT_CONFIG = {
    "dn": "My Device",
    "fn": ["Test", "Beer", "Milk", "Four", "Five"],
    "hn": "tasmota_49A3BC",
    "mac": "00000049A3BC",
    "md": "Sonoff 123",
    "ofl": "offline",
    CONF_ONLINE: "online",
    "state": ["OFF", "ON", "TOGGLE", "HOLD"],
    "sw": "2.3.3.4",
    "t": "tasmota_49A3BC",
    "t_f": "%topic%/%prefix%/",
    "t_p": ["cmnd", "stat", "tele"],
    "li": [0, 0, 0, 0, 0, 0, 0, 0],
    "rl": [1, 0, 0, 0, 0, 0, 0, 0],
    "se": [],
    "ver": 1,
}


async def test_controlling_state_via_mqtt(hass, mqtt_mock, setup_tasmota):
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.test")
    assert state.state == "unavailable"
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "online")
    state = hass.states.get("switch.test")
    assert state.state == STATE_OFF
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"ON"}')

    state = hass.states.get("switch.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/STATE", '{"POWER":"OFF"}')

    state = hass.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_sending_mqtt_commands(hass, mqtt_mock, setup_tasmota):
    """Test the sending MQTT commands."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "online")
    state = hass.states.get("switch.test")
    assert state.state == STATE_OFF

    # Turn the switch on and verify MQTT message is sent
    await common.async_turn_on(hass, "switch.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/POWER1", "ON", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Tasmota is not optimistic, the state should still be off
    state = hass.states.get("switch.test")
    assert state.state == STATE_OFF

    # Turn the switch off and verify MQTT message is sent
    await common.async_turn_off(hass, "switch.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "tasmota_49A3BC/cmnd/POWER1", "OFF", 0, False
    )

    state = hass.states.get("switch.test")
    assert state.state == STATE_OFF


async def test_availability_when_connection_lost(
    hass, mqtt_client_mock, mqtt_mock, setup_tasmota
):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
        hass, mqtt_client_mock, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_availability(hass, mqtt_mock, setup_tasmota):
    """Test availability."""
    await help_test_availability(hass, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG)


async def test_availability_discovery_update(hass, mqtt_mock, setup_tasmota):
    """Test availability discovery update."""
    await help_test_availability_discovery_update(
        hass, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_removal_switch(hass, mqtt_mock, caplog, setup_tasmota):
    """Test removal of discovered switch."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["rl"][0] = 0

    await help_test_discovery_removal(
        hass, mqtt_mock, caplog, switch.DOMAIN, config1, config2
    )


async def test_discovery_update_unchanged_switch(
    hass, mqtt_mock, caplog, setup_tasmota
):
    """Test update of discovered switch."""
    with patch(
        "homeassistant.components.tasmota.switch.TasmotaSwitch.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
            hass, mqtt_mock, caplog, switch.DOMAIN, DEFAULT_CONFIG, discovery_update
        )


async def test_discovery_device_remove(hass, mqtt_mock, setup_tasmota):
    """Test device registry remove."""
    await help_test_discovery_device_remove(
        hass, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions(hass, mqtt_mock, setup_tasmota):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    await help_test_entity_id_update_subscriptions(
        hass, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_discovery_update(hass, mqtt_mock, setup_tasmota):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
        hass, mqtt_mock, switch.DOMAIN, DEFAULT_CONFIG
    )
