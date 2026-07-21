import json
import pathlib

CONFIG_FILE = pathlib.Path.home() / ".flow/config.json"


def merge_flags(extra: list[str], args) -> tuple[list[str], object]:
    mapping = {"-bg": "bg", "-s": "shuffle", "-d": "download"}
    rest = []
    i = 0
    while i < len(extra):
        item = extra[i]
        if item == "-r":
            setattr(args, "repeat", True)
            if i + 1 < len(extra) and extra[i + 1].isdigit():
                setattr(args, "repeat_count", int(extra[i + 1]))
                i += 1
            else:
                setattr(args, "repeat_count", -1)
        elif item in mapping:
            setattr(args, mapping[item], True)
        elif item.startswith("-"):
            print(f"Unknown flag: {item}")
        else:
            rest.append(item)
        i += 1
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
_TARGETS = {"primary", "secondary", "tertiary", "display"}
_DISPLAY_MODES = {"none", "bars", "lyrics"}
_BAR_SPACING = {"min", "fit", "max"}

Primary = Cyan
Secondary = Purple
Tertiary = Blue
Muted = Grey
Display = "bars"
BarWidth = 20
BarHeight = 10
BarSpacing = 1

####### Be carefull this will make everything print on screen including links title view and all things ###
DEV_MODE = False
###########################################################################################################


def dev_print(label: str, data: dict | list | str | None = None):
    if not DEV_MODE:
        return
    Y = "\033[1;33m"
    D = "\033[90m"
    RST = "\033[0m"
    sep = f"{D}{'─' * 50}{RST}"
    print(f"\n{Y}┌─ [DEV] {label} ─{RST}")
    print(sep)
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, tuple)):
                print(f"{Y}│{RST} {D}{k}:{RST}")
                for item in v:
                    if isinstance(item, dict):
                        for ik, iv in item.items():
                            print(f"{Y}│{RST}   {D}{ik}:{RST} {iv}")
                    else:
                        print(f"{Y}│{RST}   {item}")
            else:
                print(f"{Y}│{RST} {D}{k}:{RST} {v}")
    elif isinstance(data, (list, tuple)):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                print(f"{Y}│{RST} {D}[{idx}]{RST}")
                for k, v in item.items():
                    print(f"{Y}│{RST}   {D}{k}:{RST} {v}")
            else:
                print(f"{Y}│{RST} {D}[{idx}]{RST} {item}")
    elif data is not None:
        text = str(data)
        while text:
            chunk, text = text[:70], text[70:]
            print(f"{Y}│{RST} {chunk}")
    print(sep)
    print(f"{Y}└─{RST}\n")


def get_bar_spacing():
    import os

    if BarSpacing == "min":
        return 0
    if BarSpacing == "max":
        return 4
    if BarSpacing == "fit":
        try:
            cols = os.get_terminal_size().columns
        except OSError:
            cols = 80
        return max(0, min(4, (cols - BarWidth) // max(BarWidth - 1, 1)))
    return int(BarSpacing)


def _load_config():
    global Primary, Secondary, Tertiary, Display, BarWidth, BarHeight, BarSpacing
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
        if "display" in data and data["display"] in _DISPLAY_MODES:
            Display = data["display"]
        if (
            "bar_width" in data
            and isinstance(data["bar_width"], int)
            and 4 <= data["bar_width"] <= 80
        ):
            BarWidth = data["bar_width"]
        if (
            "bar_height" in data
            and isinstance(data["bar_height"], int)
            and 2 <= data["bar_height"] <= 24
        ):
            BarHeight = data["bar_height"]
        if (
            "bar_spacing" in data
            and isinstance(data["bar_spacing"], int)
            and 0 <= data["bar_spacing"] <= 4
        ):
            BarSpacing = data["bar_spacing"]
    except (json.JSONDecodeError, OSError):
        pass


def _save_config():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "primary": _COLOR_NAMES.get(Primary, "cyan"),
        "secondary": _COLOR_NAMES.get(Secondary, "purple"),
        "tertiary": _COLOR_NAMES.get(Tertiary, "blue"),
        "display": Display,
        "bar_width": BarWidth,
        "bar_height": BarHeight,
        "bar_spacing": BarSpacing,
    }
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


DOWNLOAD_DIR = pathlib.Path.home() / ".flow/downloads"

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _version

    VERSION = _version("flow-twinx")
except PackageNotFoundError:
    VERSION = "0.4.6"

Mode = "Online"

liked_music = pathlib.Path.home() / ".flow/liked.txt"

MAX_RESULTS_RADIO = 35
MAX_SEARCH_RESULTS = 5

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
    import os
    import signal

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
    global Primary, Secondary, Tertiary, Display, BarWidth, BarHeight, BarSpacing
    if extra and extra[0] == "help":
        print(f"{Tertiary}Available targets:{Reset}")
        print(f"  {Primary}primary{Reset}   (aliases: pri)")
        print(f"  {Secondary}secondary{Reset} (aliases: sec)")
        print(f"  {Tertiary}tertiary{Reset}  (aliases: ter)")
        print(f"  {Grey}display{Reset}    (none, bars, lyrics)")
        print(f"  {Grey}barwidth{Reset}   (4-80, current: {BarWidth})")
        print(f"  {Grey}barheight{Reset}  (2-24, current: {BarHeight})")
        print(f"  {Grey}barspacing{Reset} (0-4, min, fit, max — current: {BarSpacing})")
        print(f"\n{Tertiary}Available colors:{Reset}")
        for name, code in _COLORS.items():
            print(f"  {code}{name}{Reset}")
        print(f"\n{Grey}Config file: {CONFIG_FILE}{Reset}")
        return
    if not extra:
        print(f"{Primary}Usage: config <target> <value>{Reset}")
        print(f"       config -h{Reset}")
        return
    if len(extra) < 2:
        print(f"Usage: config <target> <value>{Reset}")
        return
    target = _TARGET_ALIASES.get(extra[0].lower(), extra[0].lower())
    value = extra[1].lower()
    if target == "primary":
        if value not in _COLORS:
            print(f"Unknown color '{value}'. Use 'config -h' to see available colors.")
            return
        Primary = _COLORS[value]
        _save_config()
        print(f"{Primary}Primary color changed to {value}{Reset}")
    elif target == "secondary":
        if value not in _COLORS:
            print(f"Unknown color '{value}'. Use 'config -h' to see available colors.")
            return
        Secondary = _COLORS[value]
        _save_config()
        print(f"{Secondary}Secondary color changed to {value}{Reset}")
    elif target == "tertiary":
        if value not in _COLORS:
            print(f"Unknown color '{value}'. Use 'config -h' to see available colors.")
            return
        Tertiary = _COLORS[value]
        _save_config()
        print(f"{Tertiary}Tertiary color changed to {value}{Reset}")
    elif target == "display":
        if value not in _DISPLAY_MODES:
            print(f"Unknown display mode '{value}'. Options: none, bars, lyrics")
            return
        Display = value
        _save_config()
        print(f"{Tertiary}Display mode changed to {value}{Reset}")
    elif target in ("barwidth", "width"):
        try:
            v = int(extra[1])
        except ValueError:
            print("barwidth must be an integer (4-80)")
            return
        if not (4 <= v <= 80):
            print("barwidth must be between 4 and 80")
            return
        BarWidth = v
        _save_config()
        print(f"{Tertiary}Bar width changed to {v}{Reset}")
    elif target in ("barheight", "height"):
        try:
            v = int(extra[1])
        except ValueError:
            print("barheight must be an integer (2-24)")
            return
        if not (2 <= v <= 24):
            print("barheight must be between 2 and 24")
            return
        BarHeight = v
        _save_config()
        print(f"{Tertiary}Bar height changed to {v}{Reset}")
    elif target in ("barspacing", "spacing"):
        if value in _BAR_SPACING:
            BarSpacing = value
            _save_config()
            print(f"{Tertiary}Bar spacing changed to {value}{Reset}")
        else:
            try:
                v = int(extra[1])
            except ValueError:
                print("barspacing must be 0-4, min, fit, or max")
                return
            if not (0 <= v <= 4):
                print("barspacing must be between 0 and 4")
                return
            BarSpacing = v
            _save_config()
            print(f"{Tertiary}Bar spacing changed to {v}{Reset}")
    else:
        aliases = ", ".join(f"{k}->{v}" for k, v in _TARGET_ALIASES.items())
        print(
            f"Unknown target '{target}'. Use: primary, sec, ter, display ({aliases}){Reset}"
        )


_load_config()
