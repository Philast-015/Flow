import pathlib

def merge_flags(extra: list[str], args) -> tuple[list[str], object]:
    mapping = {"-r": "r", "-s": "s", "-d": "d"}
    rest = []
    for item in extra:
        if item in mapping:
            setattr(args, mapping[item], True)
        elif item.startswith("-"):
            print(f"Unknown flag: {item}")
        else:
            rest.append(item)
    return rest, args


ONLINE_THEME = "cyan"
OFFLINE_THEME = "magenta"

THEMES = {
    "blue":     {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[34m"},
    "green":    {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[32m"},
    "red":      {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[31m"},
    "yellow":   {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[33m"},
    "magenta":  {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[35m"},
    "cyan":     {"white": "\033[37m", "grey": "\033[90m", "theme": "\033[36m"},
}

DOWNLOAD_DIR = pathlib.Path.home() / ".flow/downloads"

VERSION = 0.1

Mode = "Online"

THEME = ONLINE_THEME

liked_music = pathlib.Path.home() / ".flow/liked.txt"