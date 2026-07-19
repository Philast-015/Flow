import builtins

from . import config

BANNER = r"""
███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝██║     ██╔═══██╗██║    ██║
█████╗  ██║     ██║   ██║██║ █╗ ██║
██╔══╝  ██║     ██║   ██║██║███╗██║
██║     ███████╗╚██████╔╝╚███╔███╔╝
╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝
"""


def show_banner():
    c = config.Primary if config.Mode == "Online" else config.Secondary
    builtins.print(f"{c}{BANNER}{config.Reset}")
    builtins.print(
        f"{config.Muted}         Flow Music Player v{config.VERSION}{config.Reset}"
    )
    builtins.print(f"{c}         Mode : {config.Mode}{config.Reset}")
    if config.DEV_MODE:
        print(f"     {config.Red}       [Dev Mode]{config.Reset}")
    builtins.print()


def input(prompt: str = "") -> str:
    if config.Mode == "Online":
        return builtins.input(f"{config.Primary}{prompt}$ {config.Reset}")
    elif config.Mode == "Offline":
        return builtins.input(f"{config.Secondary}{prompt}$ {config.Reset}")
    return builtins.input(prompt)
