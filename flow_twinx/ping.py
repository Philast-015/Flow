import socket
import urllib.request
from . import config


def is_connected(timeout: int = 2, hosts: list[str] | None = None) -> bool:
    if hosts is None:
        hosts = ["1.1.1.1"]

    socket.setdefaulttimeout(timeout)

    for host in hosts:
        try:
            with urllib.request.urlopen(f"https://{host}", timeout=timeout):
                pass
            config.Mode = "Online"
            config.THEME = config.ONLINE_THEME
            return True
        except Exception:
            pass

        try:
            socket.create_connection((host, 80), timeout=timeout).close()
            config.Mode = "Online"
            config.THEME = config.ONLINE_THEME
            return True
        except Exception:
            continue

    config.Mode = "Offline"
    config.THEME = config.OFFLINE_THEME
    return False