"""Mock serial port for Mac development.

Simulates Arduino responses for the serial protocol so the full system
can be developed and tested without hardware.

In REALTIME mode, a background thread generates periodic ``MOUTH:<code>``
reports to simulate Arduino ADC processing, so the frontend shows mouth
movement during audio playback even on Mac.
"""

import logging
import random
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

# Mouth position codes in order of increasing openness
_MOUTH_CODES = ["C", "T", "S", "N", "M", "L", "W"]


class MockSerial:
    """Mock serial port that simulates Arduino responses.

    Provides the same interface as pyserial's Serial class (write, readline, close)
    so it can be used as a drop-in replacement.

    In REALTIME mode, generates simulated mouth position reports at ~25Hz
    to mimic the Arduino's ADC-driven servo updates.
    """

    def __init__(self, port: str = "/dev/mock", baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self.is_open = True

        self._read_buffer: deque[bytes] = deque()
        self._lock = threading.Lock()
        self._config_lines_received = 0
        self._config_started = False
        self._sync_mode = "AMPLITUDE"
        self._realtime_thread: threading.Thread | None = None
        self._realtime_active = False

        # Enqueue READY on "boot"
        self._enqueue_response("READY")
        logger.info(f"MockSerial opened on {port} at {baudrate} baud")

    def write(self, data: bytes) -> int:
        """Process a command and enqueue appropriate response.

        Args:
            data: Raw bytes to "send" to the Arduino.

        Returns:
            Number of bytes written.
        """
        if not self.is_open:
            raise OSError("MockSerial port is closed")

        command = data.decode("utf-8", errors="replace").strip()
        logger.debug(f"MockSerial TX: {command}")
        self._handle_command(command)
        return len(data)

    def readline(self) -> bytes:
        """Read the next line from the mock response buffer.

        Returns:
            A line of bytes (with newline), or empty bytes if buffer is empty.
        """
        if not self.is_open:
            raise OSError("MockSerial port is closed")

        with self._lock:
            if self._read_buffer:
                return self._read_buffer.popleft()
        return b""

    def close(self) -> None:
        """Close the mock serial port."""
        self._stop_realtime()
        self.is_open = False
        logger.debug("MockSerial closed")

    def _handle_command(self, command: str) -> None:
        """Route a command and enqueue the appropriate response."""
        if command.startswith("CFG:"):
            self._handle_config(command)
        elif command == "PING":
            self._enqueue_response("PONG")
        elif command == "STATUS":
            self._enqueue_response(
                f"STATUS:MODE:{self._sync_mode},MOUTH:C,EYES:open"
            )
        elif command.startswith("M") and len(command) <= 3:
            # Mouth position command (MC, MT, MS, etc.)
            logger.debug(f"MockSerial: mouth → {command[1:]}")
        elif command.startswith("J"):
            logger.debug(f"MockSerial: jaw angles → {command[1:]}")
        elif command in ("EO", "EC", "EB"):
            logger.debug(f"MockSerial: eyes → {command}")
        elif command.startswith("MODE:"):
            new_mode = command[5:]
            logger.debug(f"MockSerial: mode → {new_mode}")
            self._sync_mode = new_mode
            self._enqueue_response("OK")
            if new_mode != "REALTIME":
                self._stop_realtime()
        elif command == "AUDIO:START":
            logger.debug("MockSerial: audio started")
            if self._sync_mode == "REALTIME":
                self._start_realtime()
        elif command == "AUDIO:STOP":
            logger.debug("MockSerial: audio stopped")
            self._stop_realtime()
        else:
            logger.debug(f"MockSerial: unrecognized command '{command}'")

    def _handle_config(self, command: str) -> None:
        """Handle CFG: commands during configuration phase."""
        if command == "CFG:DONE":
            self._enqueue_response("OK")
            self._config_started = False
            logger.debug("MockSerial: config complete")
        else:
            # CFG:SERVO:..., CFG:CAL:..., CFG:MODE:...
            if command.startswith("CFG:MODE:"):
                self._sync_mode = command[9:]
            self._config_started = True
            logger.debug(f"MockSerial: config → {command}")

    def _start_realtime(self) -> None:
        """Start background thread that simulates ADC mouth position reports."""
        if self._realtime_active:
            return
        self._realtime_active = True
        self._realtime_thread = threading.Thread(
            target=self._realtime_loop, daemon=True, name="mock-realtime"
        )
        self._realtime_thread.start()
        logger.debug("MockSerial: realtime simulation started")

    def _stop_realtime(self) -> None:
        """Stop the realtime simulation thread."""
        if not self._realtime_active:
            return
        self._realtime_active = False
        if self._realtime_thread is not None:
            self._realtime_thread.join(timeout=1.0)
            self._realtime_thread = None
        logger.debug("MockSerial: realtime simulation stopped")

    def _realtime_loop(self) -> None:
        """Simulate Arduino ADC processing at ~25Hz.

        Generates semi-random mouth position changes to mimic real audio
        amplitude driving the servos. Positions drift up and down smoothly
        rather than jumping randomly.
        """
        current_idx = 0  # Index into _MOUTH_CODES
        while self._realtime_active and self.is_open:
            # Random walk: drift 0-2 positions in either direction
            delta = random.choice([-1, -1, 0, 0, 1, 1, 2])
            current_idx = max(0, min(len(_MOUTH_CODES) - 1, current_idx + delta))
            code = _MOUTH_CODES[current_idx]
            self._enqueue_response(f"MOUTH:{code}")
            time.sleep(0.04)  # ~25Hz

        # Close mouth when simulation stops
        self._enqueue_response("MOUTH:C")

    def _enqueue_response(self, response: str) -> None:
        """Add a response line to the read buffer."""
        with self._lock:
            self._read_buffer.append(f"{response}\n".encode())
