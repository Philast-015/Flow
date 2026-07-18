import os
import signal
import sys
import termios
import threading
import time

from .. import shortcuts
from ..imports import config, merge_flags
from . import player, savan, youtube

P = config.Primary
S = config.Secondary
T = config.Tertiary
M = config.Muted
E = config.Red
G = config.Grey
R = config.Reset

m = lambda t: print(f"{M}{t}{R}")
e = lambda t: print(f"{E}{t}{R}")
i = lambda t: print(f"{P if config.Mode == 'Online' else S}{t}{R}")

_last_results = []
_last_played = None

_radio_quit = False
_radio_skip = False
_radio_tracks = []


def _radio_sigint(sig, frame):
    global _radio_skip
    _radio_skip = True


def _radio_sigquit(sig, frame):
    global _radio_quit
    _radio_quit = True


def _fork_bg(label):
    config.kill_stored()
    pid = os.fork()
    if pid > 0:
        config.save_pid(pid)
        i(f"{label} in background (PID: {pid})")
        return False
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    return True


COMMANDS = {
    "play": "Play a song from YouTube",
    "search": "Search YouTube for tracks",
    "savan": "Play a song from JioSaavn (alias: svn)",
    "savan-s": "Search JioSaavn for tracks (alias: svn-s)",
    "radio": "Generate a radio mix | radio <song> [index] to play specific track",
    "like": "Like a song",
    "download": "Download audio from YouTube",
    "switch": "Switch to Offline mode",
    "help": "Show this help message",
    "short": "Show/update command shortcuts",
    "config": "Change primary/secondary/tertiary colors",
    "exit": "Exit Flow",
}


def run(cmd: str, extra: list[str], args):
    cmd = shortcuts.resolve(cmd)
    extra, args = merge_flags(extra, args)
    if cmd == "play":
        play(extra, args)
    elif cmd == "search":
        search(" ".join(extra) if extra else "")
    elif cmd in ("savan", "svn"):
        savan_cmd(extra, args)
    elif cmd in ("savan-s", "svn-s"):
        savan_search(" ".join(extra) if extra else "")
    elif cmd == "like":
        like_track()
    elif cmd == "download":
        download(extra)
    elif cmd == "switch":
        switch_mode()
    elif cmd == "help":
        show_help()
    elif cmd in ("radio", "rd"):
        radio(extra, args)
    elif cmd == "short":
        shortcuts.cmd_short(extra, m)
    elif cmd == "config":
        config.cmd_config(extra, args)
    else:
        print(f"Unknown command: {cmd}")


def _spinner(stop):
    chars = "|/-\\"
    i = 0
    while not stop():
        sys.stdout.write(f"\r{P}Searching... {chars[i]}{R}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()


def _do_search(query):
    global _last_results
    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    _last_results = youtube.search(query)
    stop = True
    t.join()


def play(extra: list[str], args):
    if config.kill_stored():
        print(f"{P}Stopped VLC{R}")
    global _last_results, _last_played
    arg = " ".join(extra) if extra else None
    if not arg:
        print("No song specified")
        return

    if arg == "liked":
        _play_liked(args)
        return

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_last_results):
            print("Index out of range")
            return
        entry, title, _ = _last_results[idx]
    else:
        _do_search(arg)
        if not _last_results:
            print("No results found")
            return
        entry, title, _ = _last_results[0]

    _last_played = (entry, title)

    if getattr(args, "bg", False):
        if not _fork_bg("Now playing"):
            return
    player.play_entry(entry, title, args)


def _play_liked(args):
    if not config.liked_music.exists():
        e("     No liked songs yet")
        return
    liked = config.liked_music.read_text().strip().splitlines()
    if not liked:
        e("     No liked songs yet")
        return
    for line in liked:
        if "|" not in line:
            continue
        title, url = line.split("|", 1)
        _do_search(title)
        if not _last_results:
            m(f"    Skipping {title} (not found)")
            continue
        entry, _, _ = _last_results[0]
        _last_played = (entry, title)
        player.play_entry(entry, title, args)


_savan_results = []


def savan_cmd(extra, args):
    if config.kill_stored():
        print(f"{P}Stopped VLC{R}")
    global _savan_results, _last_played
    arg = " ".join(extra) if extra else None
    if not arg:
        e("No song specified")
        return

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_savan_results):
            e("Index out of range")
            return
        entry, title, dur = _savan_results[idx]
    else:
        stop = False
        t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
        t.start()
        _savan_results = savan.search(arg)
        stop = True
        t.join()
        if not _savan_results:
            e("No results found")
            return
        entry, title, dur = _savan_results[0]

    url = savan.best_url(entry)
    if not url:
        e("No playable URL found")
        return

    _last_played = (entry, title)
    if getattr(args, "bg", False):
        if not _fork_bg("Now playing"):
            return
    player.play_url(url, title, args, dur)


def savan_search(query):
    global _savan_results
    if not query:
        e("Search query required")
        return
    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    _savan_results = savan.search(query)
    stop = True
    t.join()
    if not _savan_results:
        e("No results found")
        return
    for i, (_, title, dur) in enumerate(_savan_results, 1):
        mins, secs = divmod(int(dur), 60)
        m(f"  {i}. {title}  ({mins}:{secs:02d})")


def like_track():
    global _last_played
    if not _last_played:
        e("     No song currently playing")
        return
    entry, title = _last_played
    url = entry.get("webpage_url") or entry.get("original_url")
    if not url:
        e("     No URL for current song")
        return
    config.liked_music.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        config.liked_music.read_text().strip().splitlines()
        if config.liked_music.exists()
        else []
    )
    if any(title in line for line in existing):
        m(f"    {title} already liked")
        return
    with open(config.liked_music, "a") as f:
        f.write(f"{title}|{url}\n")
    i(f"    Liked: {title}")


def search(query: str):
    global _last_results
    if not query:
        print("Search query required")
        return
    _do_search(query)
    if not _last_results:
        print("No results found")
        return
    for i, (_, title, dur) in enumerate(_last_results, 1):
        mins, secs = divmod(int(dur), 60)
        m(f"  {i}. {title}  ({mins}:{secs:02d})")


def _truncate_title(title):
    words = title.split()
    return " ".join(words[:3]) if len(words) > 3 else title


def radio(extra, args):
    if config.kill_stored():
        print(f"{P}Stopped VLC{R}")
    global _radio_tracks
    query = " ".join(extra) if extra else None
    if not query:
        e("     Usage: radio <song_name> [index]")
        return

    parts = query.rsplit(" ", 1)
    if len(parts) == 1 and parts[0].isdigit():
        idx = int(parts[0]) - 1
        if _radio_tracks and 0 <= idx < len(_radio_tracks):
            title, vid, dur = _radio_tracks[idx]
            url = f"https://www.youtube.com/watch?v={vid}"
            entry = youtube.get_entry(url)
            if getattr(args, "bg", False):
                if not _fork_bg("Now playing"):
                    return
            player.play_entry(entry, title, args)
            return
        if _last_results and 0 <= idx < len(_last_results):
            entry, title, _ = _last_results[idx]
            query = title
        else:
            e("     Index out of range or no results loaded")
            return
    elif len(parts) > 1 and parts[-1].isdigit():
        idx = int(parts[-1]) - 1
        query = parts[0]
        if _radio_tracks and 0 <= idx < len(_radio_tracks):
            title, vid, dur = _radio_tracks[idx]
            url = f"https://www.youtube.com/watch?v={vid}"
            entry = youtube.get_entry(url)
            if getattr(args, "bg", False):
                if not _fork_bg("Now playing"):
                    return
            player.play_entry(entry, title, args)
            return
        e("     Index out of range or no radio loaded")
        return

    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    tracks = youtube.fetch_radio(query, config.MAX_RESULTS_RADIO)
    stop = True
    t.join()

    if not tracks:
        e("     No radio tracks found")
        return

    _radio_tracks = tracks

    global _radio_quit, _radio_skip
    _radio_quit = False
    _radio_skip = False

    if getattr(args, "bg", False):
        if not _fork_bg(f"Playing {len(_radio_tracks)} tracks"):
            return

    old_sigint = signal.signal(signal.SIGINT, _radio_sigint)
    old_sigquit = signal.signal(signal.SIGQUIT, _radio_sigquit)

    fd = sys.stdin.fileno()
    old_term = None
    try:
        old_term = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[0] &= ~termios.IXON
        new[6][termios.VQUIT] = 0x11  # Ctrl+Q -> SIGQUIT
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
    except (termios.error, OSError):
        pass

    flags = {"quit": lambda: _radio_quit, "skip": lambda: _radio_skip}

    idx = 0
    try:
        while idx < len(_radio_tracks) and not _radio_quit:
            title, vid, dur = _radio_tracks[idx]
            url = f"https://www.youtube.com/watch?v={vid}"
            entry = youtube.get_entry(url)
            short = _truncate_title(title)
            mins, secs = divmod(int(dur), 60)

            if idx + 1 < len(_radio_tracks):
                n_title, n_vid, n_dur = _radio_tracks[idx + 1]
                n_short = _truncate_title(n_title)
                n_mins, n_secs = divmod(int(n_dur), 60)
                print(f"{T}\n\t⥤ Next: {n_short:30s} {n_mins}:{n_secs:02d}{R}")

            _radio_skip = False
            player.play_entry(entry, title, args, flags=flags)
            idx += 1
    finally:
        if old_term is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGQUIT, old_sigquit)


def download(extra: list[str]):
    global _last_results
    arg = " ".join(extra) if extra else None
    if not arg:
        e("No song specified")
        return

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_last_results):
            e("     Index out of range")
            return
        entry, _, _ = _last_results[idx]
        url = entry.get("webpage_url") or entry.get("original_url")
        if not url:
            e("     No URL found for this entry")
            return
        title = entry.get("title", "Unknown")
        filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
        i(f"    Downloaded: {title} -> {filepath}")
    else:
        _do_search(arg)
        if not _last_results:
            e("     No results found")
            return
        entry, _, _ = _last_results[0]
        url = entry.get("webpage_url") or entry.get("original_url")
        if not url:
            e("     No URL found for this entry")
            return
        title = entry.get("title", "Unknown")
        filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
        i(f"    Downloaded: {title} -> {filepath}")


def switch_mode():
    config.Mode = "Offline"


def show_help():
    print(f"{T}Online Commands:{R}")
    for cmd, desc in COMMANDS.items():
        print(f"  {T}{cmd:12s}{R} {G}{desc}{R}")
    print(f"\n{T}Config:{R}")
    print(f"  {T}config{R}      {G}Configure colors, display mode, bars{R}")
    print(f"    {G}config help       Show all config targets and colors{R}")
    print(f"    {G}config display    Set display: none, bars, lyrics{R}")
    print(f"    {G}config primary    Set primary color (online songs){R}")
    print(f"    {G}config secondary  Set secondary color (offline songs){R}")
    print(f"    {G}config tertiary   Set tertiary color (labels){R}")
    print(f"    {G}config barwidth   Bar count: 4-80 (current: {config.BarWidth}){R}")
    print(f"    {G}config barheight  Bar height: 2-16 (current: {config.BarHeight}){R}")
    print(f"    {G}config barspacing 0-4, min, fit, max (current: {config.BarSpacing}){R}")
    print(f"\n{T}Display Modes:{R}")
    print(f"  {G}bars{R}   Audio-reactive spectrum analyzer (needs audio output){R}")
    print(f"  {G}lyrics{R}  Synced lyrics display with colors{R}")
    print(f"  {G}none{R}   No display during playback{R}")
