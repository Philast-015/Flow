import datetime
import logging
import pathlib
import re
import threading

from ..imports import config

LOGS_DIR = pathlib.Path.home() / ".flow/LOGS"

_level_map = {
    "ERROR": config.Red,
    "SUCCESS": config.Green,
    "INFO": config.Cyan,
    "WARN": config.YELLOW,
}

_color_names = {
    "ERROR": "ERROR",
    "SUCCESS": "SUCCESS",
    "INFO": "INFO",
    "WARN": "WARN",
}

_source_colors = {
    "flask": config.Purple,
    "yt_dlp": config.ORANGE,
    "api": config.TEAL,
}

_http_method_colors = {
    "GET": config.Cyan,
    "POST": config.TAN,
    "FETCH": config.VIOLET,
}

_status_colors = {
    200: config.Green,
    201: config.Green,
    204: config.Green,
    301: config.SKY_BLUE,
    302: config.SKY_BLUE,
    304: config.SKY_BLUE,
    400: config.YELLOW,
    401: config.SALMON,
    403: config.ORANGE,
    404: config.Red,
    500: config.Red,
}

_lock = threading.Lock()
_log_file = None
_log_file_date = None

_werkzeug_re = re.compile(r'"(\w+) (\S+) HTTP/\S+" (\d+)')


def _ensure_log_file():
    global _log_file, _log_file_date
    now = datetime.datetime.now()
    date_str = now.strftime("%d-%H:%M")
    if _log_file_date != date_str:
        if _log_file:
            try:
                _log_file.close()
            except Exception:
                pass
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"{date_str}.log"
        _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        _log_file_date = date_str
    return _log_file


def _strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _log(level, method, status, route, source="", message=""):
    if not config.DEV_MODE:
        return

    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")

    level_color = _level_map.get(level, config.Grey)
    method_color = _http_method_colors.get(method, config.Grey)
    status_color = _status_colors.get(status, config.Grey)
    src_color = _source_colors.get(source, config.Grey)
    src_tag = f" {src_color}[{source}]{config.Reset}" if source else ""

    terminal_line = (
        f"{config.Grey}{time_str}{config.Reset} "
        f"{level_color}[{level}]{config.Reset}"
        f"{src_tag} "
        f"{method_color}{method}{config.Reset} "
        f"{status_color}{status}{config.Reset} "
        f"{config.Grey}{route}{config.Reset}"
    )
    if message:
        terminal_line += f" {config.Grey}-{config.Reset} {message}"

    file_line = f"{time_str} [{_color_names.get(level, level)}]"
    if source:
        file_line += f"[{source}] "
    file_line += f"{method} {status} {route}"
    if message:
        file_line += f" - {_strip_ansi(message)}"

    with _lock:
        try:
            print(terminal_line, flush=True)
        except Exception:
            pass
        try:
            f = _ensure_log_file()
            f.write(file_line + "\n")
            f.flush()
        except Exception:
            pass


class DevLogHandler(logging.Handler):
    def emit(self, record):
        if not config.DEV_MODE:
            return
        try:
            msg = record.getMessage()
            m = _werkzeug_re.search(msg)
            if m:
                method, route, status = m.group(1), m.group(2), int(m.group(3))
                if status >= 500:
                    _log("ERROR", method, status, route, "flask")
                elif status >= 400:
                    _log("WARN", method, status, route, "flask")
                else:
                    _log("INFO", method, status, route, "flask")
            elif record.levelno >= logging.WARNING:
                _log("WARN", "--", "--", record.name, "flask", msg)
            else:
                _log("INFO", "--", "--", record.name, "flask", msg)
        except Exception:
            pass


def setup_werkzeug_handler():
    for name in ("werkzeug", "werkzeug.serving"):
        wlog = logging.getLogger(name)
        wlog.handlers.clear()
        wlog.addHandler(DevLogHandler())
        wlog.setLevel(logging.WARNING)


def log_error(method, status, route, source="", message=""):
    _log("ERROR", method, status, route, source, message)


def log_success(method, status, route, source="", message=""):
    _log("SUCCESS", method, status, route, source, message)


def log_info(method, status, route, source="", message=""):
    _log("INFO", method, status, route, source, message)


def log_warn(method, status, route, source="", message=""):
    _log("WARN", method, status, route, source, message)


def log_detail(data, source="", label=""):
    if not config.DEV_MODE:
        return
    if not data:
        return

    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M:%S")
    src_color = _source_colors.get(source, config.Grey)
    src_tag = f" {src_color}[{source}]{config.Reset}" if source else ""
    D = config.Grey
    RST = config.Reset
    BOX = config.GOLD

    hdr = f"{label}" if label else "details"
    line1 = f"{D}{time_str}{RST}{src_tag} {BOX}┌─ {hdr} ─{RST}"
    sep = f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {D}{'─' * 46}{RST}"

    file_lines = [f"{time_str} {hdr}"]

    lines = [line1, sep]

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, tuple)):
                lines.append(f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {D}{k}:{RST}")
                file_lines.append(f"  {k}:")
                for item in v:
                    if isinstance(item, dict):
                        for ik, iv in item.items():
                            lines.append(
                                f"{D}{time_str}{RST}{src_tag} {BOX}│{RST}   {D}{ik}:{RST} {iv}"
                            )
                            file_lines.append(f"    {ik}: {iv}")
                    else:
                        lines.append(
                            f"{D}{time_str}{RST}{src_tag} {BOX}│{RST}   {item}"
                        )
                        file_lines.append(f"    {item}")
            else:
                lines.append(
                    f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {D}{k}:{RST} {v}"
                )
                file_lines.append(f"  {k}: {v}")
    elif isinstance(data, (list, tuple)):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {D}[{idx}]{RST}")
                file_lines.append(f"  [{idx}]")
                for k, v in item.items():
                    lines.append(
                        f"{D}{time_str}{RST}{src_tag} {BOX}│{RST}   {D}{k}:{RST} {v}"
                    )
                    file_lines.append(f"    {k}: {v}")
            else:
                lines.append(
                    f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {D}[{idx}]{RST} {item}"
                )
                file_lines.append(f"  [{idx}] {item}")
    else:
        text = str(data)
        while text:
            chunk, text = text[:60], text[60:]
            lines.append(f"{D}{time_str}{RST}{src_tag} {BOX}│{RST} {chunk}")
            file_lines.append(f"  {chunk}")

    end = f"{D}{time_str}{RST}{src_tag} {BOX}└{'─' * 48}{RST}"
    lines.append(end)

    with _lock:
        for l in lines:
            try:
                print(l, flush=True)
            except Exception:
                pass
        try:
            f = _ensure_log_file()
            for fl in file_lines:
                f.write(fl + "\n")
            f.flush()
        except Exception:
            pass
