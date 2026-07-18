import json
import pathlib

CONFIG_FILE = pathlib.Path.home() / ".flow/config.json"


def merge_flags(extra: list[str], args) -> tuple[list[str], object]:
    mapping = {"-bg": "bg"}
    rest = []
    for item in extra:
        if item in mapping:
            setattr(args, mapping[item], True)
        elif item.startswith("-"):
            print(f"Unknown flag: {item}")
        else:
            rest.append(item)
    return rest, args


Red = "\033[0;31m"
Green = "\033[0;32m"
Brown = "\033[0;33m"
Blue = "\033[0;34m"
Purple = "\033[0;35m"
Cyan = "\033[0;36m"
Grey = "\033[90m"
YELLOW = "\033[1;33m"
White = "\033[1;37m"
MAROON = "\033[38;5;124m"
OLIVE = "\033[38;5;100m"
DARK_KHAKI = "\033[38;5;136m"
GOLD = "\033[38;5;220m"
TAN = "\033[38;5;215m"
SALMON = "\033[38;5;209m"
CORAL = "\033[38;5;203m"
HOT_PINK = "\033[38;5;205m"
VIOLET = "\033[38;5;141m"
DEEP_PURPLE = "\033[38;5;129m"
TEAL = "\033[38;5;30m"
SKY_BLUE = "\033[38;5;117m"
STEEL_BLUE = "\033[38;5;67m"
NAVY = "\033[38;5;18m"
INDIGO = "\033[38;5;54m"
ORANGE = "\033[38;5;202m"
PINK = "\033[38;5;205m"
LIME = "\033[38;5;154m"
Reset = "\033[0m"

_COLORS = {
    k.lower().replace("_", ""): v
    for k, v in vars().items()
    if isinstance(v, str) and v.startswith("\033") and k != "Reset"
}

_COLOR_NAMES = {v: k for k, v in _COLORS.items()}

_TARGET_ALIASES = {"pri": "primary", "sec": "secondary", "ter": "tertiary"}
_TARGETS = {"primary", "secondary", "tertiary"}

Primary = Cyan
Secondary = Purple
Tertiary = Blue
Muted = Grey


def _load_config():
    global Primary, Secondary, Tertiary
    if not CONFIG_FILE.exists():
        return
    try:
        data = json.loads(CONFIG_FILE.read_text())
        if "primary" in data and data["primary"] in _COLORS:
            Primary = _COLORS[data["primary"]]
        if "secondary" in data and data["secondary"] in _COLORS:
            Secondary = _COLORS[data["secondary"]]
        if "tertiary" in data and data["tertiary"] in _COLORS:
            Tertiary = _COLORS[data["tertiary"]]
    except (json.JSONDecodeError, OSError):
        pass


def _save_config():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "primary": _COLOR_NAMES.get(Primary, "cyan"),
        "secondary": _COLOR_NAMES.get(Secondary, "purple"),
        "tertiary": _COLOR_NAMES.get(Tertiary, "blue"),
    }
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


DOWNLOAD_DIR = pathlib.Path.home() / ".flow/downloads"

VERSION = 0.3

Mode = "Online"

liked_music = pathlib.Path.home() / ".flow/liked.txt"

MAX_RESULTS_RADIO = 35

PID_FILE = pathlib.Path.home() / ".flow/vlc.pid"


def save_pid(pid: int):
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def clear_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def kill_stored():
    import os, signal
    pid = read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    clear_pid()
    return True


def cmd_config(extra: list[str], args=None):
    global Primary, Secondary, Tertiary
    if extra and extra[0] == "help":
        print(f"{Tertiary}Available targets:{Reset}")
        print(f"  {Primary}primary{Reset}   (aliases: pri)")
        print(f"  {Secondary}secondary{Reset} (aliases: sec)")
        print(f"  {Tertiary}tertiary{Reset}  (aliases: ter)")
        print(f"\n{Tertiary}Available colors:{Reset}")
        for name, code in _COLORS.items():
            print(f"  {code}{name}{Reset}")
        print(f"\n{Grey}Config file: {CONFIG_FILE}{Reset}")
        return
    if not extra:
        print(f"{Primary}Usage: config <primary|secondary|tertiary> <color>{Reset}")
        print(f"       config -h{Reset}")
        return
    if len(extra) < 2:
        print(f"Usage: config <primary|secondary|tertiary> <color>{Reset}")
        return
    target = _TARGET_ALIASES.get(extra[0].lower(), extra[0].lower())
    color_name = extra[1].lower()
    if color_name not in _COLORS:
        print(
            f"Unknown color '{color_name}'. Use 'config -h' to see available colors.{Reset}"
        )
        return
    if target == "primary":
        Primary = _COLORS[color_name]
        _save_config()
        print(f"{Primary}Primary color changed to {color_name}{Reset}")
    elif target == "secondary":
        Secondary = _COLORS[color_name]
        _save_config()
        print(f"{Secondary}Secondary color changed to {color_name}{Reset}")
    elif target == "tertiary":
        Tertiary = _COLORS[color_name]
        _save_config()
        print(f"{Tertiary}Tertiary color changed to {color_name}{Reset}")
    else:
        aliases = ", ".join(f"{k}->{v}" for k, v in _TARGET_ALIASES.items())
        print(f"Unknown target '{target}'. Use: primary, sec, ter ({aliases}){Reset}")


_load_config()
