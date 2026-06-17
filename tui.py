import builtins
import config

RESET = "\033[0m"

BORDER_CHARS = {
    "none":   None,
    "single": ("-", "|", "+"),
    "double": ("=", "|", "+"),
    "dashed": ("- ", "!", "+"),
}


def _color_map():
    colors = config.THEMES.get(config.THEME, config.THEMES["cyan"])
    return {
        "white": colors["white"],
        "grey": colors["grey"],
        "theme": colors["theme"],
    }


def print(color: str = "white", border: str = "none"):
    def styled_print(text: str):
        cm = _color_map()
        color_code = cm.get(color.lower(), cm["white"])
        border_style = BORDER_CHARS.get(border.lower())

        if border_style is None:
            print_line = f"{color_code}{text}{RESET}"
            builtins.print(print_line)
        else:
            h_char, v_char, corner_char = border_style
            lines = text.split("\n")
            max_w = max(len(l) for l in lines)
            width = max_w + 2
            top_bottom = corner_char + h_char * width + corner_char
            builtins.print(f"{color_code}{top_bottom}{RESET}")
            for line in lines:
                padded = line.ljust(max_w)
                builtins.print(f"{color_code}{v_char} {padded} {v_char}{RESET}")
            builtins.print(f"{color_code}{top_bottom}{RESET}")

    return styled_print


BANNER = r"""
███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝██║     ██╔═══██╗██║    ██║
█████╗  ██║     ██║   ██║██║ █╗ ██║
██╔══╝  ██║     ██║   ██║██║███╗██║
██║     ███████╗╚██████╔╝╚███╔███╔╝
╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝
"""


def show_banner():
    p = print(color="theme", border="none")
    p(BANNER)
    p = print(color="grey", border="none")
    p(f"         Flow Music Player v{config.VERSION}")
    p = print(color="theme", border="none")
    p(f"         Mode : {config.Mode}")
    builtins.print()


def input(prompt: str = "") -> str:
    cm = _color_map()
    return builtins.input(f"{cm['theme']}{prompt}$ {RESET}")
