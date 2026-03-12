"""Arduino serial communication controller.

Manages the serial connection to the Arduino, which handles all motor control.
Supports both real serial (pyserial) and mock serial for Mac development.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass

from backend.core.enums import MouthPosition, ServoType, SyncMode
from backend.core.exceptions import SerialError
from backend.hardware.calibration import CalibrationTable

logger = logging.getLogger(__name__)

# Type alias for mouth position callbacks from Arduino realtime reports
MouthPositionCallback = Callable[[MouthPosition], None]


@dataclass
class ArduinoStatus:
    """Current Arduino state."""

    mode: SyncMode
    mouth_position: MouthPosition
    eyes_open: bool


class ArduinoController:
    """Async controller for Arduino serial communication.

    Handles the serial protocol: handshake, configuration, runtime commands.
    All serial I/O is run via asyncio.to_thread since pyserial is synchronous.

    Attributes:
        port: Serial port path.
        baud_rate: Serial baud rate.
        timeout: Read timeout in seconds.
        connect_timeout: Timeout for initial READY handshake.
        use_mock: Use mock serial instead of real hardware.
        connected: Whether the Arduino is connected and configured.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baud_rate: int = 115200,
        timeout: float = 1.0,
        connect_timeout: float = 10.0,
        use_mock: bool = False,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.use_mock = use_mock
        self.connected = False

        self._serial: object | None = None
        self._write_lock = asyncio.Lock()
        self._response_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reader_task: asyncio.Task[None] | None = None
        self._shutdown = False
        self._mouth_position_callback: MouthPositionCallback | None = None

    async def connect(
        self,
        servo_type: ServoType = ServoType.HBRIDGE,
        calibration: CalibrationTable | None = None,
        sync_mode: SyncMode = SyncMode.AMPLITUDE,
    ) -> None:
        """Open serial connection and perform handshake.

        Args:
            servo_type: Type of servo hardware on the Arduino.
            calibration: Calibration table to send. Uses defaults if None.
            sync_mode: Initial sync mode.

        Raises:
            SerialError: If connection or handshake fails.
        """
        if self.connected:
            logger.warning("Already connected, disconnecting first")
            await self.disconnect()

        try:
            if self.use_mock:
                from backend.hardware.mock_serial import MockSerial

                self._serial = MockSerial(self.port, self.baud_rate)
            else:
                import serial

                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                )

            # Start background reader
            self._shutdown = False
            self._reader_task = asyncio.create_task(self._read_loop())

            # Wait for READY
            ready = await self._wait_for_response("READY", timeout=self.connect_timeout)
            if not ready:
                raise SerialError(
                    f"Arduino did not send READY within {self.connect_timeout}s"
                )

            # Send configuration
            await self._send_config(servo_type, calibration, sync_mode)

            self.connected = True
            logger.info(f"Arduino connected on {self.port} (mock={self.use_mock})")

        except SerialError:
            raise
        except Exception as e:
            raise SerialError(f"Failed to connect to Arduino: {e}") from e

    async def disconnect(self) -> None:
        """Close serial connection and clean up."""
        self._shutdown = True
        self.connected = False

        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._serial is not None:
            try:
                await asyncio.to_thread(self._serial.close)  # type: ignore[union-attr]
            except Exception as e:
                logger.error(f"Error closing serial: {e}")
            self._serial = None

        logger.info("Arduino disconnected")

    async def set_mouth_position(self, position: MouthPosition) -> None:
        """Send mouth position by code.

        Args:
            position: One of the 7 mouth positions.
        """
        await self._send_command(f"M{position.value}")

    async def set_mouth_angles(self, upper: int, lower: int) -> None:
        """Send mouth position by direct servo angles.

        Args:
            upper: Upper jaw servo angle in degrees.
            lower: Lower jaw servo angle in degrees.
        """
        await self._send_command(f"J{upper},{lower}")

    async def open_eyes(self) -> None:
        """Command eyes to open."""
        await self._send_command("EO")

    async def close_eyes(self) -> None:
        """Command eyes to close."""
        await self._send_command("EC")

    async def blink_eyes(self) -> None:
        """Command a single blink (firmware handles close+pause+open)."""
        await self._send_command("EB")

    async def notify_audio_start(self) -> None:
        """Signal that audio playback has started.

        Informational hint — the real Arduino ignores this (it reads ADC
        continuously). The mock serial uses it to start generating simulated
        mouth position reports in realtime mode.
        """
        await self._send_command("AUDIO:START")

    async def notify_audio_stop(self) -> None:
        """Signal that audio playback has stopped."""
        await self._send_command("AUDIO:STOP")

    async def set_mode(self, mode: SyncMode) -> None:
        """Switch sync mode on the Arduino.

        Args:
            mode: New sync mode.
        """
        await self._send_command(f"MODE:{mode.value.upper()}")

    async def ping(self) -> bool:
        """Health check.

        Returns:
            True if Arduino responds with PONG.
        """
        try:
            await self._send_command("PING")
            response = await self._wait_for_response("PONG", timeout=2.0)
            return response
        except Exception:
            return False

    async def get_status(self) -> ArduinoStatus | None:
        """Request current Arduino state.

        Returns:
            ArduinoStatus if response received, None on timeout.
        """
        try:
            await self._send_command("STATUS")
            # Wait for STATUS: response
            line = await self._wait_for_line(prefix="STATUS:", timeout=2.0)
            if line is None:
                return None
            return self._parse_status(line)
        except Exception as e:
            logger.error(f"Failed to get Arduino status: {e}")
            return None

    def set_mouth_position_callback(self, callback: MouthPositionCallback | None) -> None:
        """Register a callback for realtime mouth position reports from Arduino.

        The callback is invoked synchronously from the read loop whenever
        the Arduino sends a ``MOUTH:<code>`` line (realtime ADC mode only).

        Args:
            callback: Function accepting a MouthPosition, or None to clear.
        """
        self._mouth_position_callback = callback

    # --- Internal methods ---

    async def _send_config(
        self,
        servo_type: ServoType,
        calibration: CalibrationTable | None,
        sync_mode: SyncMode,
    ) -> None:
        """Send configuration sequence to Arduino."""
        from backend.hardware.calibration import get_default_calibration

        if calibration is None:
            calibration = get_default_calibration()

        # Servo type
        await self._send_command(f"CFG:SERVO:{servo_type.value.upper()}")

        # Calibration data — one line per position
        for pos in MouthPosition:
            upper, lower = calibration.get_angles(pos)
            await self._send_command(f"CFG:CAL:{pos.value}:{upper}:{lower}")

        # Sync mode
        await self._send_command(f"CFG:MODE:{sync_mode.value.upper()}")

        # Done
        await self._send_command("CFG:DONE")

        # Wait for OK
        ok = await self._wait_for_response("OK", timeout=5.0)
        if not ok:
            raise SerialError("Arduino did not acknowledge configuration")

    async def _send_command(self, command: str) -> None:
        """Send a command line to the Arduino.

        Args:
            command: Command string (newline is appended automatically).

        Raises:
            SerialError: If not connected or write fails.
        """
        if self._serial is None:
            raise SerialError("Not connected to Arduino")

        async with self._write_lock:
            try:
                data = f"{command}\n".encode()
                await asyncio.to_thread(self._serial.write, data)  # type: ignore[union-attr]
                logger.debug(f"TX: {command}")
            except Exception as e:
                raise SerialError(f"Failed to send command '{command}': {e}") from e

    async def _read_loop(self) -> None:
        """Background task that reads lines from serial and enqueues them.

        Intercepts ``MOUTH:<code>`` lines from Arduino realtime mode and
        dispatches them to the registered callback instead of the response queue.
        """
        try:
            while not self._shutdown:
                line = await asyncio.to_thread(self._read_line)
                if line:
                    logger.debug(f"RX: {line}")
                    # Intercept realtime mouth position reports
                    if line.startswith("MOUTH:") and self._mouth_position_callback:
                        code = line[6:].strip()
                        try:
                            position = MouthPosition(code)
                            self._mouth_position_callback(position)
                        except ValueError:
                            logger.warning(f"Invalid mouth position code from Arduino: {code}")
                    else:
                        await self._response_queue.put(line)
                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if not self._shutdown:
                logger.error(f"Serial reader error: {e}")

    def _read_line(self) -> str | None:
        """Read a single line from serial (blocking, called via to_thread)."""
        if self._serial is None:
            return None
        try:
            raw = self._serial.readline()  # type: ignore[union-attr]
            if raw:
                return raw.decode("utf-8", errors="replace").strip()
        except Exception:
            if not self._shutdown:
                raise
        return None

    async def _wait_for_response(self, expected: str, timeout: float = 5.0) -> bool:
        """Wait for a specific response string.

        Args:
            expected: The exact string to wait for.
            timeout: Maximum seconds to wait.

        Returns:
            True if the expected response was received.
        """
        try:
            deadline = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < deadline:
                remaining = deadline - asyncio.get_event_loop().time()
                try:
                    line = await asyncio.wait_for(
                        self._response_queue.get(), timeout=min(remaining, 0.5)
                    )
                    if line == expected:
                        return True
                    if line.startswith("ERR:"):
                        logger.warning(f"Arduino error: {line}")
                except TimeoutError:
                    continue
            return False
        except Exception:
            return False

    async def _wait_for_line(self, prefix: str, timeout: float = 5.0) -> str | None:
        """Wait for a line starting with a specific prefix.

        Args:
            prefix: Line prefix to match.
            timeout: Maximum seconds to wait.

        Returns:
            The full line if found, None on timeout.
        """
        try:
            deadline = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < deadline:
                remaining = deadline - asyncio.get_event_loop().time()
                try:
                    line = await asyncio.wait_for(
                        self._response_queue.get(), timeout=min(remaining, 0.5)
                    )
                    if line.startswith(prefix):
                        return line
                except TimeoutError:
                    continue
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_status(line: str) -> ArduinoStatus:
        """Parse a STATUS response line.

        Expected format: STATUS:MODE:<m>,MOUTH:<pos>,EYES:<state>
        """
        try:
            # Strip "STATUS:" prefix
            payload = line[7:]
            parts = {}
            for segment in payload.split(","):
                key, value = segment.split(":", 1)
                parts[key] = value

            mode = SyncMode(parts.get("MODE", "amplitude").lower())
            mouth = MouthPosition(parts.get("MOUTH", "C"))
            eyes_open = parts.get("EYES", "open").lower() == "open"

            return ArduinoStatus(mode=mode, mouth_position=mouth, eyes_open=eyes_open)
        except Exception as e:
            raise SerialError(f"Failed to parse STATUS response '{line}': {e}") from e
