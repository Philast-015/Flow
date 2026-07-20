import json
import logging
import mimetypes
import os
import pathlib

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

from ..imports import config

logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder=pathlib.Path(__file__).resolve().parent / "templates",
    static_url_path="/static",
)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

if not config.DEV_MODE:
    for name in ("werkzeug", "werkzeug.serving", "flask.app"):
        logging.getLogger(name).setLevel(logging.ERROR)

SETTINGS_FILE = pathlib.Path.home() / ".flow/web_ui.json"
FLOW_DIR = pathlib.Path.home() / ".flow/downloads"
MUSIC_DIR = pathlib.Path.home() / ".flow/music"

AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".ogg",
    ".opus",
    ".wma",
    ".aac",
    ".webm",
}

SEARCH_CACHE_MAX = 50
_search_cache = {}

BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "noplaylist": True,
    "format": "bestaudio*",
    "skip_download": True,
    "socket_timeout": 10,
    "retries": 2,
    "extractor_retries": 2,
}

_ydl_search = {**BASE_OPTS, "default_search": "ytsearch1", "extract_flat": True}
_ydl_entry = {**BASE_OPTS}
_ydl_radio = {**BASE_OPTS, "noplaylist": False, "extract_flat": True}


def _get_stream_url(entry):
    if entry.get("url"):
        return entry["url"]
    for fmt in reversed(entry.get("formats", [])):
        if fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
            return fmt.get("url")
    for fmt in reversed(entry.get("formats", [])):
        if fmt.get("acodec") != "none":
            return fmt.get("url")
    return None


def _get_thumbnail(entry):
    if entry.get("thumbnail"):
        return entry["thumbnail"]
    thumbs = entry.get("thumbnails", [])
    if thumbs:
        return thumbs[-1].get("url", "")
    return ""


def _entry_to_dict(entry):
    return {
        "title": entry.get("title", "Unknown"),
        "video_id": entry.get("id", ""),
        "stream_url": _get_stream_url(entry) or "",
        "thumbnail": _get_thumbnail(entry),
        "channel": entry.get("uploader", "Unknown"),
        "duration": entry.get("duration", 0),
    }


def _cached_search(query, limit):
    key = f"{query}:{limit}"
    if key in _search_cache:
        return _search_cache[key]
    results = []
    try:
        with yt_dlp.YoutubeDL(_ydl_search) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = info.get("entries", []) if info else []
            results = [_entry_to_dict(e) for e in entries if e]
    except Exception as exc:
        logger.warning("Search failed for %r: %s", query, exc)
    _search_cache[key] = results
    if len(_search_cache) > SEARCH_CACHE_MAX:
        del _search_cache[next(iter(_search_cache))]
    return results


def _fetch_radio(video_id, max_results=30):
    radio_url = f"https://www.youtube.com/watch?v={video_id}&list=RDMM{video_id}"
    opts = {**_ydl_radio, "playlistend": max_results}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(radio_url, download=False)
        entries = info.get("entries", []) if info else []
        return [
            {
                "title": e.get("title", "Unknown"),
                "video_id": e["id"],
                "duration": e.get("duration", 0),
                "thumbnail": _get_thumbnail(e),
            }
            for e in entries
            if e.get("id")
        ]


def _get_full_entry(video_id):
    try:
        with yt_dlp.YoutubeDL(_ydl_entry) as ydl:
            return ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
    except Exception as exc:
        logger.warning("Failed to get entry for %s: %s", video_id, exc)
        return None


def _scan_dir(base, depth=0, max_depth=2):
    if not base.exists() or not base.is_dir():
        return []
    results = []
    try:
        for item in sorted(base.iterdir()):
            if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
                results.append(
                    {
                        "title": item.stem,
                        "path": str(item),
                        "filename": item.name,
                        "source": "library"
                        if str(base).startswith(str(FLOW_DIR))
                        else "custom",
                    }
                )
            elif item.is_dir() and depth < max_depth and item.name != "liked songs":
                results.extend(_scan_dir(item, depth + 1, max_depth))
    except PermissionError:
        pass
    return results


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "missing query parameter 'q'"}), 400
    limit = min(int(request.args.get("limit", 10)), 25)
    return jsonify({"results": _cached_search(q, limit)})


@app.route("/trend")
def trend():
    return jsonify({"results": _cached_search("#trending #english #topsong", 15)})


@app.route("/recommend")
def recommend():
    vid = request.args.get("video_id", "").strip()
    if not vid:
        return jsonify({"error": "missing query parameter 'video_id'"}), 400
    limit = min(int(request.args.get("limit", 30)), 50)
    try:
        return jsonify({"results": _fetch_radio(vid, limit)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/play")
def play():
    vid = request.args.get("video_id", "").strip()
    if not vid:
        return jsonify({"error": "missing query parameter 'video_id'"}), 400
    try:
        entry = _get_full_entry(vid)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    if not entry:
        return jsonify({"error": "video not found"}), 404
    return jsonify(_entry_to_dict(entry))


@app.route("/offline")
def offline():
    songs = _scan_dir(FLOW_DIR)
    return jsonify({"results": songs})


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(force=True)
    vid = data.get("video_id", "").strip()
    save_dir = data.get("save_dir", str(FLOW_DIR))
    if not vid:
        return jsonify({"error": "missing video_id"}), 400
    save_path = pathlib.Path(save_dir).expanduser()
    save_path.mkdir(parents=True, exist_ok=True)
    opts = {
        **BASE_OPTS,
        "skip_download": False,
        "outtmpl": str(save_path / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}", download=True
            )
            filename = ydl.prepare_filename(info)
            mp3_path = pathlib.Path(filename).with_suffix(".mp3")
            return jsonify({
                "success": True,
                "path": str(mp3_path),
                "title": info.get("title", "Unknown"),
            })
    except Exception as exc:
        logger.warning("Download failed for %s: %s", vid, exc)
        return jsonify({"error": str(exc)}), 500


@app.route("/local/<path:filepath>")
def serve_local(filepath):
    p = pathlib.Path(filepath)
    if not p.is_absolute():
        p = pathlib.Path("/") / p
    if not p.exists() or not p.is_file():
        return jsonify({"error": "file not found"}), 404
    if p.suffix.lower() not in AUDIO_EXTENSIONS:
        return jsonify({"error": "not an audio file"}), 400
    mimetype, _ = mimetypes.guess_type(str(p))
    return send_file(str(p), mimetype=mimetype or "audio/mpeg", conditional=True)


@app.route("/api/albums")
def api_albums():
    if not MUSIC_DIR.exists():
        return jsonify({"albums": []})
    albums = sorted([d.name for d in MUSIC_DIR.iterdir() if d.is_dir()])
    return jsonify({"albums": albums})


@app.route("/api/album/<album_name>")
def api_album_songs(album_name):
    album_dir = MUSIC_DIR / album_name
    if not album_dir.exists() or not album_dir.is_dir():
        return jsonify({"error": "album not found"}), 404
    songs = []
    for f in sorted(album_dir.iterdir()):
        if f.suffix.lower() in AUDIO_EXTENSIONS:
            songs.append({
                "title": f.stem,
                "path": str(f),
                "filename": f.name,
                "album": album_name,
            })
    return jsonify({"results": songs})


@app.route("/api/local-search")
def api_local_search():
    q = request.args.get("q", "").strip().lower()
    results = []
    for f in sorted(FLOW_DIR.rglob("*")):
        if f.suffix.lower() in AUDIO_EXTENSIONS and q in f.stem.lower():
            results.append({
                "title": f.stem,
                "path": str(f),
                "filename": f.name,
            })
    if MUSIC_DIR.exists():
        for f in sorted(MUSIC_DIR.rglob("*")):
            if f.suffix.lower() in AUDIO_EXTENSIONS and q in f.stem.lower():
                results.append({
                    "title": f.stem,
                    "path": str(f),
                    "filename": f.name,
                })
    return jsonify({"results": results})


@app.route("/api/liked")
def api_liked():
    liked_file = config.liked_music
    if not liked_file.exists():
        return jsonify({"results": []})
    liked_ids = set()
    try:
        for line in liked_file.read_text().splitlines():
            line = line.strip()
            if line:
                liked_ids.add(line)
    except Exception:
        pass
    huge_liked = pathlib.Path.home() / ".flow/downloads/liked songs"
    songs = []
    if huge_liked.exists():
        for f in sorted(huge_liked.iterdir()):
            if f.suffix.lower() in AUDIO_EXTENSIONS:
                songs.append({
                    "title": f.stem,
                    "path": str(f),
                    "filename": f.name,
                })
    return jsonify({"results": songs, "liked_ids": list(liked_ids)})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if request.method == "POST":
        data = request.get_json(force=True)
        existing = {}
        if SETTINGS_FILE.exists():
            try:
                existing = json.loads(SETTINGS_FILE.read_text())
            except Exception:
                pass
        existing.update(data)
        SETTINGS_FILE.write_text(json.dumps(existing, indent=2))
        return jsonify({"saved": True, "settings": existing})
    if SETTINGS_FILE.exists():
        try:
            return jsonify(json.loads(SETTINGS_FILE.read_text()))
        except Exception:
            pass
    return jsonify({})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setting")
def setting_page():
    return render_template("setting.html")


@app.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")
