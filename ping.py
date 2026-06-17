import socket
import urllib.request
import urllib.error
import config


def is_connected(timeout: int = 3, hosts: list[str] | None = None) -> bool:
    if hosts is None:
        hosts = ["1.1.1.1", "8.8.8.8"]

    for host in hosts:
        try:
            urllib.request.urlopen(f"https://{host}", timeout=timeout)
            config.Mode = "Online"
            config.THEME = config.ONLINE_THEME
            return True
        except (urllib.error.URLError, socket.error):
            pass

        try:
            socket.create_connection((host, 80), timeout=timeout).close()
            config.Mode = "Online"
            config.THEME = config.ONLINE_THEME
            return True
        except (OSError, socket.error):
            continue  # try next host

    config.Mode = "Offline"
    config.THEME = config.OFFLINE_THEME
    return False


# if __name__ == "__main__":
#     connected = is_connected()
#     print(f"Status : {config.Mode}")
#     print(f"Returns: {connected}")