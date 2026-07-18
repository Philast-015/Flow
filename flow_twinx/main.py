import argparse
import importlib
import sys
import threading
import time
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    __package__ = "flow_twinx"
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from . import shortcuts
from .imports import config, is_connected, show_banner, tui_input

P = config.Primary
S = config.Secondary
M = config.Muted
R = config.Reset

SHELL_AUTO_BG = {"radio", "savan"}


def _spinner(stop):
    chars = "|/-\\"
    i = 0
    while not stop():
        sys.stdout.write(f"\r{P}Checking connection... {chars[i]}{R}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()


def _load_commands():
    return importlib.import_module(f".{config.Mode}.commands", package=__package__)


def _check_vlc():
    try:
        import vlc
    except ImportError:
        print(
            f"{config.Red}VLC is not installed. Flow requires VLC to play audio.{config.Reset}\n"
            f"{config.Muted}Install it with:{config.Reset}\n"
            f"  {config.Tertiary}sudo apt install vlc{config.Reset}"
            f"  {config.Muted}  # Debian/Ubuntu{config.Reset}\n"
            f"  {config.Tertiary}sudo dnf install vlc{config.Reset}"
            f"  {config.Muted}  # Fedora{config.Reset}\n"
            f"  {config.Tertiary}sudo pacman -S vlc{config.Reset}"
            f"  {config.Muted}  # Arch Linux{config.Reset}\n"
            f"  {config.Tertiary}brew install vlc{config.Reset}"
            f"  {config.Muted}  # macOS{config.Reset}"
        )
        sys.exit(1)


def main():
    _check_vlc()

    parser = argparse.ArgumentParser(description="Flow Music Player")
    parser.add_argument("--play", nargs="+", help="play a song")
    parser.add_argument("--rd", nargs="+", help="play radio mix")
    parser.add_argument("--stop", action="store_true", help="stop background VLC")
    parser.add_argument(
        "command", nargs="?", default=None, help="subcommand (play, search, list, ...)"
    )

    args, unknown = parser.parse_known_args()

    shortcuts.load()

    if getattr(args, "stop", False):
        if config.kill_stored():
            print(f"{P}Stopped VLC{R}")
        else:
            print(f"{M}No background VLC running{R}")
        sys.exit(0)

    if getattr(args, "play", None) is not None:
        args.command = "play"
        unknown = args.play + unknown
    elif getattr(args, "rd", None) is not None:
        args.command = "radio"
        unknown = args.rd + unknown

    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    try:
        if is_connected():
            config.Mode = "Online"
        else:
            config.Mode = "Offline"
    finally:
        stop = True
        t.join()

    commands = _load_commands()

    if args.command:
        resolved = []
        for item in unknown:
            if item.startswith("-"):
                alias = item[1:]
                resolved_cmd = shortcuts.resolve(alias)
                if resolved_cmd != alias:
                    if args.command is None:
                        args.command = resolved_cmd
                    continue
            resolved.append(item)
        unknown = resolved

        if args.command in SHELL_AUTO_BG:
            args.bg = True

        show_banner()
        try:
            commands.run(args.command, unknown, args)
        except KeyboardInterrupt:
            pass
    else:
        show_banner()
        if unknown:
            print(f"{M}Unknown command: {' '.join(unknown)}{R}")
        while True:
            try:
                parts = tui_input().strip().split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                extra = parts[1:]
                cmd = shortcuts.resolve(cmd)
                if cmd in ("exit", "quit", "q"):
                    print(f"{M}Goodbye!{R}")
                    break
                cmd_args = argparse.Namespace(**vars(args))
                for flag in ("bg", "repeat", "shuffle"):
                    setattr(cmd_args, flag, False)
                cmd_args.repeat_count = 0
                try:
                    commands.run(cmd, extra, cmd_args)
                except KeyboardInterrupt:
                    pass
                if getattr(cmd_args, "bg", False):
                    break
                if cmd == "switch":
                    commands = _load_commands()
                    show_banner()
            except (EOFError, KeyboardInterrupt):
                print(f"{M}\nGoodbye!{R}")
                break


if __name__ == "__main__":
    main()
