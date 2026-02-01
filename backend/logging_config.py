"""Centralized logging configuration with WebSocket streaming support."""

import logging
import queue
from typing import Optional

# Queue for streaming logs to WebSocket clients
log_queue: queue.Queue = queue.Queue(maxsize=1000)


class WebSocketHandler(logging.Handler):
    """Custom logging handler that sends logs to a queue for WebSocket streaming."""

    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to queue for WebSocket clients."""
        try:
            log_entry = {
                "timestamp": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Add exception info if present
            if record.exc_info:
                import traceback

                log_entry["exception"] = "".join(traceback.format_exception(*record.exc_info))

            # Put in queue (non-blocking, drop oldest if full)
            try:
                log_queue.put_nowait(log_entry)
            except queue.Full:
                # Drop oldest log and try again
                try:
                    log_queue.get_nowait()
                    log_queue.put_nowait(log_entry)
                except:
                    pass
        except Exception:
            self.handleError(record)


def setup_logging(level: str = "INFO", enable_websocket_streaming: bool = True) -> None:
    """Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_websocket_streaming: Whether to enable WebSocket log streaming
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # WebSocket handler for frontend streaming
    if enable_websocket_streaming:
        ws_handler = WebSocketHandler()
        ws_handler.setLevel(logging.DEBUG)  # Capture all levels, filter on frontend
        root_logger.addHandler(ws_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def set_log_level(level: str) -> None:
    """Change the log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Update console handler level
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, WebSocketHandler):
            handler.setLevel(log_level)

    logging.info(f"Log level changed to {level.upper()}")


def get_recent_logs(count: int = 100) -> list[dict]:
    """Get recent logs from the queue without removing them.

    Args:
        count: Maximum number of logs to return

    Returns:
        List of recent log entries
    """
    logs = []
    temp_queue = queue.Queue()

    # Extract logs
    while not log_queue.empty() and len(logs) < count:
        try:
            log = log_queue.get_nowait()
            logs.append(log)
            temp_queue.put(log)
        except queue.Empty:
            break

    # Put them back
    while not temp_queue.empty():
        try:
            log_queue.put_nowait(temp_queue.get_nowait())
        except queue.Full:
            break

    return logs
