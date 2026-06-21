import random
import sys
import threading
import time
from .. import config
from ..config import merge_flags
from . import youtube
from . import player
from ..tui import print as tprint

_last_results = []
_last_played = None

COMMANDS = {
    "play":  "Play a song from YouTube",
    "search": "Search YouTube for tracks",
    "like":  "Like a song",
    "download": "Download audio from YouTube",
    "switch": "Switch to Offline mode",
    "help":  "Show this help message",
    "exit":  "Exit Flow",
}

m = tprint(color="grey", border="none")
e = tprint(color="red", border="none")
i = tprint(color="theme", border="none")

def run(cmd: str, extra: list[str], args):
    extra, args = merge_flags(extra, args)
    if cmd == "play":
        play(extra, args)
    elif cmd == "search":
        search(" ".join(extra) if extra else "")
    elif cmd == "like":
        like_track()
    elif cmd == "download":
        download(extra)
    elif cmd == "switch":
        switch_mode()
    elif cmd == "help":
        show_help()
    else:
        print(f"Unknown command: {cmd}")


def _spinner(stop):
    chars = "|/-\\"
    i = 0
    while not stop():
        sys.stdout.write(f"\r\x1b[36mSearching... {chars[i]}\x1b[0m")
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
    filepath = None
    if getattr(args, "d", False):
        url = entry.get("webpage_url") or entry.get("original_url")
        if not url:
            print("No URL found for this entry")
            return
        m(f"   \n Downloading {title}...")
        filepath = youtube.download_url(url, config.DOWNLOAD_DIR)
        m(f"    Downloaded to {filepath}")

    player.play_entry(entry, title, args, filepath)


def _play_liked(args):
    if not config.liked_music.exists():
        e("     No liked songs yet")
        return
    liked = config.liked_music.read_text().strip().splitlines()
    if not liked:
        e("     No liked songs yet")
        return
    if getattr(args, "s", False):
        random.shuffle(liked)
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
    existing = config.liked_music.read_text().strip().splitlines() if config.liked_music.exists() else []
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
    config.THEME = config.OFFLINE_THEME
    m("Switched to Offline mode")


def show_help():
    print(f"{config.THEMES[config.THEME]['theme']}Online Commands:{chr(27)}[0m")
    for cmd, desc in COMMANDS.items():
        print(f"  {cmd:12s} {desc}")