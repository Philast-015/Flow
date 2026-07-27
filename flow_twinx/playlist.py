import json
import pathlib

PLAYLISTS_FILE = pathlib.Path.home() / ".flow/playlists.json"
PLAYLIST_DIR = pathlib.Path.home() / ".flow/playlist"

_SUBCOMMANDS = {
    "add": "add",
    "a": "add",
    "remove": "remove",
    "r": "remove",
    "list": "list",
    "l": "list",
    "create": "create",
    "c": "create",
    "delete": "delete",
    "d": "delete",
}


def resolve_subcmd(word):
    return _SUBCOMMANDS.get(word, word)


def _load():
    if not PLAYLISTS_FILE.exists():
        return {}
    try:
        return json.loads(PLAYLISTS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data):
    PLAYLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAYLISTS_FILE.write_text(json.dumps(data, indent=2))


def list_all():
    return list(_load().keys())


def get(name):
    return _load().get(name, [])


def create(name):
    data = _load()
    if name in data:
        return False
    data[name] = []
    _save(data)
    return True


def delete(name):
    data = _load()
    if name not in data:
        return False
    del data[name]
    _save(data)
    return True


def add_song(name, title, video_id="", url=""):
    data = _load()
    if name not in data:
        data[name] = []
    data[name].append({"title": title, "video_id": video_id, "url": url})
    _save(data)
    return True


def remove_song(name, index=None, title_match=None):
    data = _load()
    if name not in data:
        return False, "Playlist not found"
    songs = data[name]
    if index is not None:
        if index < 0 or index >= len(songs):
            return False, "Index out of range"
        removed = songs.pop(index)
        _save(data)
        return True, removed["title"]
    if title_match:
        for i, s in enumerate(songs):
            if title_match.lower() in s["title"].lower():
                removed = songs.pop(i)
                _save(data)
                return True, removed["title"]
        return False, "Song not found"
    return False, "Specify index or song name"


def download_dir(name):
    d = PLAYLIST_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d
