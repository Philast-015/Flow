import random
from ..imports import config, merge_flags, tprint, is_connected
from .. import shortcuts
from .. import help_detail
from . import file as lib
from . import player

try:
    import readline
    _HAS_READLINE = True
except ImportError:
    _HAS_READLINE = False

_last_results = []
_last_played = None

COMMANDS = {
    "play":    "Play song(s) from local library | all by play all | and liked",
    "search":  "Search local music library",
    "list":    "List local music library",
    "like":    "Like the currently playing song",
    "switch":  "Switch to Online mode (checks connection)",
    "help":    "Show this help message",
    "short":   "Show/update command shortcuts",
    "exit":    "Exit Flow",
}

m = tprint(color="grey", border="none")
e = tprint(color="red", border="none")
i = tprint(color="theme", border="none")


class _Completer:
    def __init__(self):
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            line = readline.get_line_buffer()
            parts = line.split()
            if len(parts) <= 1:
                options = [c for c in COMMANDS if c.startswith(text)]
            elif parts[0] == "play":
                songs = lib.get_song_names()
                albums = lib.get_album_names()
                all_names = songs + albums
                options = sorted(set(
                    n for n in all_names
                    if n.lower().startswith(text.lower())
                ))
            else:
                options = []
            self.matches = options
        try:
            return self.matches[state]
        except IndexError:
            return None


def _setup_completion():
    if not _HAS_READLINE:
        return
    readline.set_completer(_Completer().complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(' \t\n;')


def run(cmd: str, extra: list[str], args):
    _setup_completion()
    cmd = shortcuts.resolve(cmd)
    inf = "-i" in extra
    extra, args = merge_flags(extra, args)
    if cmd == "play":
        play(extra, args)
    elif cmd == "search":
        search(" ".join(extra) if extra else "")
    elif cmd == "list":
        list_library()
    elif cmd == "like":
        like_track()
    elif cmd == "switch":
        switch_mode()
    elif cmd == "help":
        show_help(inf)
    elif cmd == "short":
        shortcuts.cmd_short(extra, m)
    else:
        e(f"Unknown command: {cmd}")


def play(extra: list[str], args):
    global _last_results, _last_played
    arg = " ".join(extra) if extra else None
    if not arg:
        e("No song specified")
        return

    if arg == "liked":
        _play_liked(args)
        return
    elif arg == "all":
        _play_all(args)
        return
    if arg in lib.get_album_names():
        _play_album(arg, args)
        return

    if arg.isdigit():
        idx = int(arg) - 1
        if idx < 0 or idx >= len(_last_results):
            e("Index out of range")
            return
        song_path = _last_results[idx]
    else:
        results = lib.find_songs(arg)
        if not results:
            e(f"No songs found matching '{arg}'")
            return
        if len(results) == 1:
            song_path = results[0]
        else:
            _last_results = results
            m("Multiple matches:")
            for i, p in enumerate(results, 1):
                m(f"  {i}. {p.stem}")
            return

    _last_played = song_path
    player.play_file(song_path, song_path.stem, args)


def _play_liked(args):
    liked = lib.get_liked_songs()
    if not liked:
        e("No liked songs yet")
        return
    if getattr(args, "s", False):
        random.shuffle(liked)
    for song in liked:
        _last_played = song
        player.play_file(song, song.stem, args)

def _play_all(args):
    all = lib.get_all_songs()
    if not all:
        e("No downloaded songs yet")
        return
    if getattr(args, "s", False):
        random.shuffle(all)
    for song in all:
        _last_played = song
        player.play_file(song, song.stem, args)

def _play_album(album: str, args):
    songs = lib.get_album_songs(album)
    if not songs:
        e(f"No songs found in album '{album}'")
        return
    if getattr(args, "s", False):
        random.shuffle(songs)
    for song in songs:
        _last_played = song
        player.play_file(song, song.stem, args)


def like_track():
    global _last_played
    if not _last_played:
        e("No song currently playing")
        return
    dest = lib.like_song(_last_played)
    if dest:
        i(f"Liked: {_last_played.stem}")
    else:
        m(f"{_last_played.stem} is already liked")


def search(query: str):
    global _last_results
    if not query:
        e("Search query required")
        return
    results = lib.find_songs(query)
    if not results:
        e("No results found")
        return
    _last_results = results
    for i, p in enumerate(results, 1):
        m(f"  {i}. {p.stem}")


def list_library():
    songs = lib.get_songs()
    albums = lib.get_albums()
    liked = lib.get_liked_songs()

    if songs:
        i("\nSongs:")
        for p in songs:
            m(f"  {p.stem}")
    if albums:
        i("\nAlbums:")
        for a in albums:
            m(f"  {a}/")
    if liked:
        i("\nLiked Songs:")
        for p in liked:
            m(f"  {p.stem}")
    if not songs and not albums and not liked:
        e("No music in library")


def switch_mode():
    if is_connected():
        i("Switched to Online mode")
    else:
        e("No internet connection")


def show_help(inf=False):
    _t = config.THEMES[config.THEME]["theme"]
    _g = "\033[90m"
    _r = "\033[0m"
    if inf:
        print(f"{_t}Offline Commands (detailed):{_r}")
        for cmd, lines in help_detail.OFFLINE_HELP.items():
            for line in lines:
                print(f"  {line.replace('{theme}', _t)}")
            print()
    else:
        print(f"{_t}Offline Commands:{_r}")
        for cmd, desc in COMMANDS.items():
            print(f"  {_t}{cmd:12s}{_r} {_g}{desc}{_r}")
        print(f"{_g}  Use 'help -i' for detailed usage{_r}")
