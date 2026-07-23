import errno
import fcntl
import os
import random
import re
import signal
import sys
import termios
import threading
import time

from flow_twinx.config import MAX_SEARCH_RESULTS

from .. import help_detail, shortcuts
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
    inf = "-i" in extra
    extra = [x for x in extra if x != "-i"]
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
        show_help(inf)
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
    _last_results = youtube.search(query, MAX_SEARCH_RESULTS)
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

    if getattr(args, "download", False):
        download(extra)
        return

    if arg == "liked":
        _play_liked(args)
        return

    repeat = getattr(args, "repeat", False)
    shuffle = getattr(args, "shuffle", False)

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_last_results):
            print("Index out of range")
            return
        entry, title, _ = _last_results[idx]
        entry = _resolve_entry(entry)
        _last_played = (entry, title)
        if getattr(args, "bg", False):
            if not _fork_bg("Now playing"):
                return
        player.play_entry(entry, title, args)
        return

    _do_search(arg)
    if not _last_results:
        print("No results found")
        return

    if repeat or shuffle:
        results = list(_last_results)
        if shuffle:
            random.shuffle(results)
        repeat_count = getattr(args, "repeat_count", 0)
        iteration = 0
        try:
            while True:
                for entry, title, _ in results:
                    entry = _resolve_entry(entry)
                    _last_played = (entry, title)
                    if getattr(args, "bg", False):
                        if not _fork_bg("Now playing"):
                            return
                    player.play_entry(entry, title, args)
                if not repeat:
                    break
                iteration += 1
                if repeat_count > 0 and iteration >= repeat_count:
                    break
        except KeyboardInterrupt:
            pass
    else:
        entry, title, _ = _last_results[0]
        entry = _resolve_entry(entry)
        _last_played = (entry, title)
        if getattr(args, "bg", False):
            if not _fork_bg("Now playing"):
                return
        player.play_entry(entry, title, args)


def _resolve_entry(entry):
    if entry.get("formats"):
        return entry
    url = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
    if not url and entry.get("id"):
        url = f"https://www.youtube.com/watch?v={entry['id']}"
    if not url:
        return entry
    full = youtube.get_entry(url)
    return full if full else entry


def _play_liked(args):
    if not config.liked_music.exists():
        e("     No liked songs yet")
        return
    liked = config.liked_music.read_text().strip().splitlines()
    if not liked:
        e("     No liked songs yet")
        return
    songs = []
    for line in liked:
        if "|" not in line:
            continue
        title, url = line.split("|", 1)
        songs.append((title, url))
    if getattr(args, "shuffle", False):
        random.shuffle(songs)
    repeat = getattr(args, "repeat", False)
    repeat_count = getattr(args, "repeat_count", 0)
    iteration = 0
    try:
        while True:
            for title, url in songs:
                _do_search(title)
                if not _last_results:
                    m(f"    Skipping {_truncate_title(title)} (not found)")
                    continue
                entry, _, _ = _last_results[0]
                entry = _resolve_entry(entry)
                _last_played = (entry, title)
                player.play_entry(entry, title, args)
            if not repeat:
                break
            iteration += 1
            if repeat_count > 0 and iteration >= repeat_count:
                break
    except KeyboardInterrupt:
        pass


_savan_results = []


def savan_cmd(extra, args):
    if config.kill_stored():
        print(f"{P}Stopped VLC{R}")
    global _savan_results, _last_played
    arg = " ".join(extra) if extra else None
    if not arg:
        e("No song specified")
        return

    repeat = getattr(args, "repeat", False)
    shuffle = getattr(args, "shuffle", False)

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_savan_results):
            e("Index out of range")
            return
        entry, title, dur = _savan_results[idx]
        url = savan.best_url(entry)
        if not url:
            e("No playable URL found")
            return
        _last_played = (entry, title)
        if getattr(args, "bg", False):
            if not _fork_bg("Now playing"):
                return
        player.play_url(url, title, args, dur)
        return

    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    _savan_results = savan.search(arg)
    stop = True
    t.join()
    if not _savan_results:
        e("No results found")
        return

    if repeat or shuffle:
        results = list(_savan_results)
        if shuffle:
            random.shuffle(results)
        repeat_count = getattr(args, "repeat_count", 0)
        iteration = 0
        try:
            while True:
                for entry, title, dur in results:
                    url = savan.best_url(entry)
                    if not url:
                        e(f"No playable URL for {_truncate_title(title)}, skipping")
                        continue
                    _last_played = (entry, title)
                    if getattr(args, "bg", False):
                        if not _fork_bg("Now playing"):
                            return
                    player.play_url(url, title, args, dur)
                if not repeat:
                    break
                iteration += 1
                if repeat_count > 0 and iteration >= repeat_count:
                    break
        except KeyboardInterrupt:
            pass
    else:
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
        m(f"  {i}. {_truncate_title(title)}  ({mins}:{secs:02d})")


def like_track():
    global _last_played
    if not _last_played:
        e("     No song currently playing")
        return
    entry, title = _last_played
    url = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
    if not url and entry.get("id"):
        url = f"https://www.youtube.com/watch?v={entry['id']}"
    if not url:
        e("     No URL for current song")
        return
    config.dev_print(
        "Like Track",
        {
            "title": title,
            "url": url,
            "video_id": entry.get("id"),
            "webpage_url": entry.get("webpage_url"),
            "original_url": entry.get("original_url"),
        },
    )
    config.liked_music.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        config.liked_music.read_text().strip().splitlines()
        if config.liked_music.exists()
        else []
    )
    if any(title in line for line in existing):
        m(f"    {_truncate_title(title)} already liked")
        return
    with open(config.liked_music, "a") as f:
        f.write(f"{title}|{url}\n")
    i(f"    Liked: {_truncate_title(title)}")


def search(query: str):
    global _last_results
    if not query:
        print("Search query required")
        return
    _do_search(query)
    if not _last_results:
        print("No results found")
        return
    for i, (entry, title, dur) in enumerate(_last_results, 1):
        mins, secs = divmod(int(dur), 60)
        uploader = entry.get("uploader", "")
        m(f"  {i}. {_truncate_title(title)}  ({mins}:{secs:02d}) [{uploader}]")


def _truncate_title(title):
    title = re.sub(r"[^A-Za-z0-9\s]", "", title)
    words = title.split()
    return " ".join(words[:4]) + "..." if len(words) > 4 else title


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
            config.dev_print(
                "Radio (play by index)",
                {
                    "title": title,
                    "video_id": vid,
                    "url": url,
                    "duration": f"{dur}s",
                },
            )
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
            config.dev_print(
                "Radio (play by query+index)",
                {
                    "title": title,
                    "video_id": vid,
                    "url": url,
                    "duration": f"{dur}s",
                },
            )
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

    if getattr(args, "download", False):
        for idx, (title, vid, dur) in enumerate(_radio_tracks, 1):
            url = f"https://www.youtube.com/watch?v={vid}"
            config.dev_print(
                "Radio Download",
                {
                    "title": title,
                    "video_id": vid,
                    "url": url,
                    "duration": f"{dur}s",
                    "progress": f"{idx}/{len(_radio_tracks)}",
                },
            )
            filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
            i(f"    Downloaded ({idx}/{len(_radio_tracks)}): {_truncate_title(title)}")
        return

    if getattr(args, "shuffle", False):
        random.shuffle(_radio_tracks)

    global _radio_quit, _radio_skip
    _radio_quit = False
    _radio_skip = False

    if getattr(args, "bg", False):
        if not _fork_bg(f"Playing {len(_radio_tracks)} tracks"):
            return

    old_sigint = signal.signal(signal.SIGINT, _radio_sigint)
    old_sigquit = signal.signal(signal.SIGQUIT, _radio_sigquit)
    old_sigusr1 = signal.getsignal(signal.SIGUSR1)

    fd = sys.stdin.fileno()
    old_term = None
    old_fd_flags = None
    try:
        old_term = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[0] &= ~termios.IXON
        new[6][termios.VQUIT] = 0x11
        new[6][termios.VSUSP] = 0
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        old_fd_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, old_fd_flags | os.O_NONBLOCK)
    except termios.error, OSError:
        pass

    def _radio_sigusr1(sig, frame):
        player._sigusr1_toggle(sig, frame)

    signal.signal(signal.SIGUSR1, _radio_sigusr1)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    player._radio_active = True

    def _radio_input_reader():
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

    radio_reader = threading.Thread(target=_radio_input_reader, daemon=True)
    radio_reader.start()

    flags = {"quit": lambda: _radio_quit, "skip": lambda: _radio_skip}

    repeat = getattr(args, "repeat", False)
    repeat_count = getattr(args, "repeat_count", 0)
    iteration = 0

    try:
        while True:
            idx = 0
            while idx < len(_radio_tracks) and not _radio_quit:
                title, vid, dur = _radio_tracks[idx]
                url = f"https://www.youtube.com/watch?v={vid}"
                config.dev_print(
                    "Radio (playing track)",
                    {
                        "title": title,
                        "video_id": vid,
                        "url": url,
                        "duration": f"{dur}s",
                        "position": f"{idx + 1}/{len(_radio_tracks)}",
                    },
                )
                entry = youtube.get_entry(url)
                short = _truncate_title(title)
                mins, secs = divmod(int(dur), 60)

                if idx + 1 < len(_radio_tracks):
                    n_title, n_vid, n_dur = _radio_tracks[idx + 1]
                    n_short = _truncate_title(n_title)
                    n_mins, n_secs = divmod(int(n_dur), 60)
                    print(f"{T}\n\t[⥤ Next: {n_short:30s} {n_mins}:{n_secs:02d}]{R}")

                _radio_skip = False
                player.play_entry(entry, title, args, flags=flags)
                idx += 1
            if not repeat or _radio_quit:
                break
            iteration += 1
            if repeat_count > 0 and iteration >= repeat_count:
                break
    except KeyboardInterrupt:
        _radio_quit = True
    finally:
        player._radio_active = False
        if old_term is not None:
            try:
                if old_fd_flags is not None:
                    fcntl.fcntl(fd, fcntl.F_SETFL, old_fd_flags)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
            except termios.error, OSError:
                pass
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGQUIT, old_sigquit)
        signal.signal(signal.SIGUSR1, old_sigusr1)


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
        url = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
        if not url and entry.get("id"):
            url = f"https://www.youtube.com/watch?v={entry['id']}"
        if not url:
            e("     No URL found for this entry")
            return
        title = entry.get("title", "Unknown")
        config.dev_print(
            "Download (by index)",
            {
                "title": title,
                "url": url,
                "video_id": entry.get("id"),
                "output_dir": str(config.DOWNLOAD_DIR),
            },
        )
        filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
        i(f"    Downloaded: {_truncate_title(title)} -> {filepath}")
    else:
        _do_search(arg)
        if not _last_results:
            e("     No results found")
            return
        entry, _, _ = _last_results[0]
        url = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
        if not url and entry.get("id"):
            url = f"https://www.youtube.com/watch?v={entry['id']}"
        if not url:
            e("     No URL found for this entry")
            return
        title = entry.get("title", "Unknown")
        config.dev_print(
            "Download (by search)",
            {
                "title": title,
                "url": url,
                "video_id": entry.get("id"),
                "output_dir": str(config.DOWNLOAD_DIR),
            },
        )
        filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
        i(f"    Downloaded: {_truncate_title(title)} -> {filepath}")


def switch_mode():
    config.Mode = "Offline"


def show_help(inf=False):
    if inf:
        print(f"{T}Online Commands (detailed):{R}")
        for cmd, lines in help_detail.ONLINE_HELP.items():
            for line in lines:
                print(f"  {line}")
            print()
    else:
        print(f"{T}Online Commands:{R}")
        for cmd, desc in COMMANDS.items():
            print(f"  {T}{cmd:12s}{R} {G}{desc}{R}")
        print(f"{G}  Use 'help -i' for detailed usage{R}")
