import argparse
import importlib
import sys
import threading
import time
import config
from tui import show_banner, input as tui_input, print as tui_print
from ping import is_connected


def _spinner(stop):
    chars = "|/-\\"
    i = 0
    while not stop():
        sys.stdout.write(f"\r\x1b[36mChecking connection... {chars[i]}\x1b[0m")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()


def _load_commands():
    return importlib.import_module(f"{config.Mode}.commands")


def main():
    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    is_connected()
    stop = True
    t.join()

    parser = argparse.ArgumentParser(description="Flow Music Player")
    parser.add_argument("-r", action="store_true", help="repeat mode")
    parser.add_argument("-s", action="store_true", help="shuffle")
    parser.add_argument("-d", action="store_true", help="download mode")
    parser.add_argument("command", nargs="?", default=None, help="subcommand (play, search, list, ...)")

    args, unknown = parser.parse_known_args()

    commands = _load_commands()

    show_banner()

    if args.command:
        commands.run(args.command, unknown, args)
    elif unknown:
        tui_print(color="white", border="double")(f"Unknown argument: {' '.join(unknown)}")
    else:
        while True:
            try:
                parts = tui_input().strip().split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                extra = parts[1:]
                if cmd in ("exit", "quit", "q"):
                    tui_print(color="grey", border="none")("Goodbye!")
                    break
                cmd_args = argparse.Namespace(**vars(args))
                for flag in ("r", "s", "d"):
                    setattr(cmd_args, flag, False)
                commands.run(cmd, extra, cmd_args)
                if cmd == "switch":
                    mode = config.Mode
                    commands = _load_commands()
                    show_banner()
                    tui_print(color="grey", border="none")(f"Mode changed to {mode}")
            except (EOFError, KeyboardInterrupt):
                tui_print(color="grey", border="none")("\nGoodbye!")
                break


if __name__ == "__main__":
    main()
