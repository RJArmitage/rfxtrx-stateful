from __future__ import annotations
import logging
from .abs_tilting_cover import (
    AbstractTiltingCover,
    BLIND_POS_CLOSED
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPENING
)
from .const import (
    CONF_CLOSE_SECONDS,
    CONF_COLOUR_ICON,
    CONF_OPEN_SECONDS,
    CONF_CUSTOM_ICON,
    CONF_COLOUR_ICON,
    CONF_PARTIAL_CLOSED,
    CONF_SIGNAL_REPETITIONS,
    CONF_SIGNAL_REPETITIONS_DELAY_MS,
    DEF_CLOSE_SECONDS,
    DEF_COLOUR_ICON,
    DEF_OPEN_SECONDS,
    DEF_CUSTOM_ICON,
    DEF_COLOUR_ICON,
    DEF_PARTIAL_CLOSED,
    DEF_SIGNAL_REPETITIONS_DELAY_MS
)

_LOGGER = logging.getLogger(__name__)

DEVICE_TYPE = "Vogue Vertical"

CMD_VOGUE_CLOSE_CW = 0x00
CMD_VOGUE_CLOSE_CCW = 0x01
CMD_VOGUE_45_DEGREES = 0x02
CMD_VOGUE_90_DEGREES = 0x03
CMD_VOGUE_135_DEGREES = 0x04

ICON_PATH = "/local/rfxtrx/vertical"

# Event 0919130400A1DB010000


class LouvoliteVogueBlind(AbstractTiltingCover):
    """Representation of a RFXtrx cover."""

    def __init__(self, device, device_id, entity_info, event=None):
        device.type_string = DEVICE_TYPE

        openSecs = entity_info.get(CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
        closeSecs = entity_info.get(CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)

        super().__init__(device, device_id,
                         entity_info[CONF_SIGNAL_REPETITIONS],
                         entity_info.get(
                             CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS),
                         event,
                         2,  #  2 steps to mid point
                         True,  # Supports mid point
                         False,  # Does not support lift
                         False,  # Do not lift on open
                         False,  # Does not require sync on mid point
                         min(openSecs, closeSecs),  # Open time
                         max(openSecs, closeSecs),  # Close time
                         max(openSecs, closeSecs),  # Sync time ms
                         2000  # Ms for each step
                         )
        self._customIcon = entity_info.get(CONF_CUSTOM_ICON, DEF_CUSTOM_ICON)
        self._colourIcon = entity_info.get(CONF_COLOUR_ICON, DEF_COLOUR_ICON)
        self._partialClosed = entity_info.get(
            CONF_PARTIAL_CLOSED, DEF_PARTIAL_CLOSED)

        _LOGGER.info("Create Louvolite Vogue tilting blind " + str(device_id))

    @property
    def entity_picture(self):
        """Return the icon property."""
        if self._customIcon:
            if self.is_opening or self.is_closing:
                icon = "move.svg"
                closed = self._lastClosed
            else:
                tilt = self._steps_to_tilt(self._tilt_step)
                if tilt <= 15:
                    icon = "00.svg"
                    closed = True
                elif tilt <= 40:
                    icon = "25.svg"
                    closed = self._partialClosed
                elif tilt <= 60:
                    icon = "50.svg"
                    closed = False
                elif tilt <= 85:
                    icon = "75.svg"
                    closed = self._partialClosed
                else:
                    icon = "99.svg"
                    closed = True
            if self._colourIcon and not(closed):
                icon = ICON_PATH + "/active/" + icon
            else:
                icon = ICON_PATH + "/inactive/" + icon
            self._lastClosed = closed
            _LOGGER.debug("Returned icon attribute = " + icon)
        else:
            icon = None
        return icon

    async def _async_tilt_blind_to_step(self, steps, target):
        """Callback to tilt the blind to some position"""
        _LOGGER.info("LOUVOLITE TILTING BLIND")
        if target == 0:
            movement = STATE_CLOSING
            command = CMD_VOGUE_CLOSE_CCW
        elif target == 1:
            movement = STATE_OPENING
            command = CMD_VOGUE_45_DEGREES
        elif target == 2:
            movement = STATE_OPENING
            command = CMD_VOGUE_90_DEGREES
        elif target == 3:
            movement = STATE_OPENING
            command = CMD_VOGUE_135_DEGREES
        else:
            movement = STATE_CLOSING
            command = CMD_VOGUE_CLOSE_CW

        delay = self._blindOpenSecs if steps <= 2 else self._blindCloseSecs

        if self._motion_allowed():
            await self._set_state(movement, BLIND_POS_CLOSED, self._tilt_step)
            await self._async_send_command(command)
            await self._wait_and_set_state(delay, movement, STATE_CLOSED, BLIND_POS_CLOSED, target)

        return target

    async def _async_do_close_blind(self):
        """Callback to close the blind"""
        _LOGGER.info("LOUVOLITE CLOSING BLIND")
        if self._motion_allowed():
            await self._set_state(STATE_CLOSING, BLIND_POS_CLOSED, self._tilt_step)
            await self._async_send_command(CMD_VOGUE_CLOSE_CCW)
        return self._blindCloseSecs

    async def _async_do_open_blind(self):
        """Callback to open the blind"""
        _LOGGER.info("LOUVOLITE OPENING BLIND")
        if self._motion_allowed():
            await self._set_state(STATE_OPENING, BLIND_POS_CLOSED, self._tilt_step)
            await self._async_send_command(CMD_VOGUE_90_DEGREES)
        return self._blindOpenSecs

    async def _async_do_tilt_blind_to_mid(self):
        """Callback to tilt the blind to mid"""
        _LOGGER.info("LOUVOLITE TILTING BLIND TO MID")
        if self._motion_allowed():
            await self._set_state(STATE_OPENING, BLIND_POS_CLOSED, self._tilt_step)
            await self._async_send_command(CMD_VOGUE_90_DEGREES)
        return self._blindOpenSecs
