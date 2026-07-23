import errno
import fcntl
import os
import re
import signal
import sys
import termios
import threading
import time

import vlc

from .. import visualizer
from ..imports import config

P = config.Primary
S = config.Secondary
T = config.Tertiary


def _truncate_title(title):
    title = re.sub(r"[^A-Za-z0-9\s]", "", title)
    words = title.split()
    return " ".join(words[:4]) + "..." if len(words) > 4 else title


M = config.Muted
E = config.Red
R = config.Reset

m = lambda t: print(f"{M}{t}{R}")
e = lambda t: print(f"{E}{t}{R}")
i = lambda t: print(f"{P if config.Mode == 'Online' else S}{t}{R}")
t = lambda t: print(f"{T}{t}{R}")

_paused = False
_player = None
_original_term = None


def _sigusr1_toggle(sig, frame):
    global _paused
    _paused = not _paused
    if _player:
        _player.pause()


def _setup_pause_input():
    global _original_term
    fd = sys.stdin.fileno()
    try:
        _original_term = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[0] &= ~termios.IXON
        new[6][termios.VSUSP] = 0
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
    except termios.error, OSError:
        _original_term = None
        return
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    signal.signal(signal.SIGUSR1, _sigusr1_toggle)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    thread = threading.Thread(target=_input_reader, daemon=True)
    thread.start()


def _input_reader():
    fd = sys.stdin.fileno()
    try:
        while True:
            try:
                ch = os.read(fd, 1)
            except OSError as ex:
                if ex.errno == errno.EAGAIN:
                    time.sleep(0.05)
                    continue
                break
            if ch == b"\x10":
                os.kill(os.getpid(), signal.SIGUSR1)
    except OSError:
        pass


def _restore_pause_input():
    global _original_term
    if _original_term is not None:
        try:
            fd = sys.stdin.fileno()
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
            termios.tcsetattr(fd, termios.TCSADRAIN, _original_term)
        except termios.error, OSError:
            pass
        _original_term = None


def _flags_str(args):
    if not args:
        return ""
    parts = []
    if getattr(args, "repeat", False):
        count = getattr(args, "repeat_count", 0)
        parts.append(f"[Repeat:{'∞' if count < 0 else count}]")
    if getattr(args, "shuffle", False):
        parts.append("[Shuffle:On]")
    return "  ".join(parts)


def _display_loop(player, duration=0):
    global _paused
    display = config.Display
    if display == "none":
        return

    if display == "bars":
        visualizer.start()

    start = time.time()
    paused_printed = False
    try:
        while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
            if _paused:
                if not paused_printed:
                    sys.stdout.write(f"\r  {T}[Paused]{R}  ")
                    sys.stdout.flush()
                    paused_printed = True
                try:
                    time.sleep(0.1)
                except OSError:
                    pass
                continue
            if paused_printed:
                paused_printed = False
            if display == "bars":
                bar_str = visualizer.render(color=S, reset=R)
                sys.stdout.write(f"\r{bar_str}")
                sys.stdout.flush()
            try:
                time.sleep(0.08)
            except OSError:
                pass
    finally:
        if display == "bars":
            visualizer.stop()
        sys.stdout.write("\r" + " " * 60 + "\r\n")
        sys.stdout.flush()


def play_file(filepath, title, args=None):
    global _player, _paused
    _paused = False
    instance = vlc.Instance("--no-video --quiet")
    _player = instance.media_player_new()
    media = instance.media_new(str(filepath))
    _player.set_media(media)
    _player.play()
    _setup_pause_input()

    duration = 0
    for _ in range(50):
        duration = _player.get_length() / 1000
        if duration > 0:
            break
        time.sleep(0.1)
    if duration <= 0:
        duration = 0
    dur_min, dur_sec = divmod(int(duration), 60)
    flags = _flags_str(args)
    i(f"\nPlaying : {_truncate_title(title)}")
    m(
        f"    [{dur_min}:{dur_sec:02d}]  {flags}"
        if flags
        else f"    [{dur_min}:{dur_sec:02d}]"
    )

    try:
        _display_loop(_player, duration=duration)
    except KeyboardInterrupt:
        _player.stop()
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise
    finally:
        _restore_pause_input()
