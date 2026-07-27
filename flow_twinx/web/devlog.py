import logging
import logging.handlers
import pathlib

from ..imports import config

LOGS_DIR = pathlib.Path.home() / ".flow/LOGS"

_handler = None


def _make_handler():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    h = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "flow.log", maxBytes=512_000, backupCount=3, encoding="utf-8"
    )
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    return h


def setup_werkzeug_handler():
    h = _make_handler()
    for name in ("werkzeug", "werkzeug.serving"):
        wlog = logging.getLogger(name)
        wlog.handlers.clear()
        wlog.addHandler(h)
        wlog.setLevel(logging.WARNING)


def _emit(level, msg):
    if not config.DEV_MODE:
        return
    global _handler
    if _handler is None:
        _handler = _make_handler()
    print(msg, flush=True)
    _handler.emit(logging.LogRecord("devlog", level, "", 0, msg, (), None))


def log_error(method, status, route, source="", message=""):
    _emit(logging.ERROR, f"[ERROR] [{source}] {method} {status} {route} - {message}")


def log_success(method, status, route, source="", message=""):
    _emit(logging.INFO, f"[OK] [{source}] {method} {status} {route} - {message}")


def log_info(method, status, route, source="", message=""):
    _emit(logging.INFO, f"[INFO] [{source}] {method} {status} {route} - {message}")


def log_warn(method, status, route, source="", message=""):
    _emit(logging.WARNING, f"[WARN] [{source}] {method} {status} {route} - {message}")
