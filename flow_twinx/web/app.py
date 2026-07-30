import json
import logging
import mimetypes
import os
import pathlib

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

from ..imports import config
from . import devlog

logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder=pathlib.Path(__file__).resolve().parent / "templates",
    static_url_path="/static",
)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def _log_response(response):
    if config.DEV_MODE:
        status = response.status_code
        method = request.method
        route = request.path
        msg = ""
        if (
            hasattr(response, "get_json")
            and response.content_type == "application/json"
        ):
            try:
                body = response.get_json(silent=True)
                if isinstance(body, dict):
                    if "error" in body:
                        msg = body["error"]
                    elif "success" in body:
                        msg = "ok"
            except Exception:
                pass
        if status >= 500:
            devlog.log_error(method, status, route, "flask", msg)
        elif status >= 400:
            devlog.log_warn(method, status, route, "flask", msg)
        elif method == "POST":
            devlog.log_success(method, status, route, "flask", msg)
        else:
            devlog.log_info(method, status, route, "flask", msg)
    return response


if config.DEV_MODE:
    devlog.setup_werkzeug_handler()
else:
    for name in ("werkzeug", "werkzeug.serving", "flask.app"):
        logging.getLogger(name).setLevel(logging.ERROR)

SETTINGS_FILE = pathlib.Path.home() / ".flow/web_ui.json"
FLOW_DIR = pathlib.Path.home() / ".flow/downloads"
MUSIC_DIR = pathlib.Path.home() / ".flow/music"

_truncate_title = config._truncate_title

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
    "format": "bestaudio",
    "skip_download": True,
    "socket_timeout": 10,
    "retries": 2,
    "extractor_retries": 2,
}

_ydl_search = {**BASE_OPTS, "default_search": "ytsearch1", "extract_flat": True}
_ydl_entry = {**BASE_OPTS}
_ydl_radio = {**BASE_OPTS, "noplaylist": False, "extract_flat": True}


def _get_stream_url(entry):
    if not entry.get("formats"):
        return None
    for fmt in reversed(entry["formats"]):
        if fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
            return fmt.get("url")
    for fmt in reversed(entry["formats"]):
        if fmt.get("acodec") != "none":
            return fmt.get("url")
    return entry.get("url")


def _get_thumbnail(entry):
    if entry.get("thumbnail"):
        return entry["thumbnail"]
    thumbs = entry.get("thumbnails", [])
    if thumbs:
        return thumbs[-1].get("url", "")
    return ""


def _entry_to_dict(entry):
    return {
        "title": _truncate_title(entry.get("title", "Unknown")),
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
        devlog.log_error("FETCH", 500, "/search", "yt_dlp", f"query={query} err={exc}")
        _search_cache[key] = results
        return results
    devlog.log_info(
        "FETCH", 200, "/search", "yt_dlp", f"query={query} {len(results)} results"
    )
    _search_cache[key] = results
    if len(_search_cache) > SEARCH_CACHE_MAX:
        del _search_cache[next(iter(_search_cache))]
    return results


def _fetch_radio(video_id, max_results=30):
    radio_url = f"https://www.youtube.com/watch?v={video_id}&list=RDMM{video_id}"
    opts = {**_ydl_radio, "playlistend": max_results}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(radio_url, download=False)
            entries = info.get("entries", []) if info else []
            tracks = [
                {
                    "title": _truncate_title(e.get("title", "Unknown")),
                    "video_id": e["id"],
                    "duration": e.get("duration", 0),
                    "thumbnail": _get_thumbnail(e),
                }
                for e in entries
                if e.get("id")
            ]
            devlog.log_info(
                "FETCH",
                200,
                "/recommend",
                "yt_dlp",
                f"radio vid={video_id} {len(tracks)} tracks",
            )
            return tracks
    except Exception as exc:
        devlog.log_error(
            "FETCH", 500, "/recommend", "yt_dlp", f"radio vid={video_id} err={exc}"
        )
        raise


def _get_full_entry(video_id):
    try:
        with yt_dlp.YoutubeDL(_ydl_entry) as ydl:
            entry = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            if entry:
                devlog.log_info("FETCH", 200, "/play", "yt_dlp", f"vid={video_id}")
            return entry
    except Exception as exc:
        logger.warning("Failed to get entry for %s: %s", video_id, exc)
        devlog.log_error("FETCH", 500, "/play", "yt_dlp", f"vid={video_id} err={exc}")
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
    try:
        limit = min(int(request.args.get("limit", 10)), 25)
    except ValueError, TypeError:
        limit = 10
    return jsonify({"results": _cached_search(q, limit)})


@app.route("/trend")
def trend():
    return jsonify({"results": _cached_search("#trending #english #topsong", 15)})


@app.route("/recommend")
def recommend():
    vid = request.args.get("video_id", "").strip()
    if not vid:
        return jsonify({"error": "missing query parameter 'video_id'"}), 400
    try:
        limit = min(int(request.args.get("limit", 30)), 50)
    except ValueError, TypeError:
        limit = 30
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
    fmt = data.get("format", config.FORMAT)
    if not vid:
        return jsonify({"error": "missing video_id"}), 400
    if fmt not in ("webm", "opus", "m4a", "mp3"):
        return jsonify({"error": f"unsupported format '{fmt}'"}), 400
    if fmt != "webm" and not config.FFMPEG:
        return jsonify({"error": f"ffmpeg not found, cannot convert to {fmt}"}), 400
    save_path = pathlib.Path(save_dir).expanduser()
    save_path.mkdir(parents=True, exist_ok=True)
    opts = {
        **BASE_OPTS,
        "skip_download": False,
        "outtmpl": str(save_path / "%(title).50B.%(ext)s"),
    }
    if fmt != "webm":
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": fmt}]
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}", download=True
            )
            filename = ydl.prepare_filename(info)
            if fmt != "webm":
                ext = fmt
                stem = pathlib.Path(filename).stem
                filename = str(pathlib.Path(save_path) / f"{stem}.{ext}")
            devlog.log_success("FETCH", 200, "/download", "yt_dlp", f"downloaded {vid}")
            return jsonify(
                {
                    "success": True,
                    "path": str(filename),
                    "title": _truncate_title(info.get("title", "Unknown")),
                }
            )
    except Exception as exc:
        logger.warning("Download failed for %s: %s", vid, exc)
        devlog.log_error("FETCH", 500, "/download", "yt_dlp", f"vid={vid} err={exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/local/<path:filepath>")
def serve_local(filepath):
    p = pathlib.Path(filepath)
    if not p.is_absolute():
        p = pathlib.Path("/") / p
    home = pathlib.Path.home()
    try:
        p = p.resolve()
    except OSError, ValueError:
        return jsonify({"error": "invalid path"}), 400
    if not str(p).startswith(str(home)):
        return jsonify({"error": "access denied"}), 403
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
    album_dir = (MUSIC_DIR / album_name).resolve()
    home = pathlib.Path.home()
    if not str(album_dir).startswith(str(home)):
        return jsonify({"error": "access denied"}), 403
    if not album_dir.exists() or not album_dir.is_dir():
        return jsonify({"error": "album not found"}), 404
    songs = []
    for f in sorted(album_dir.iterdir()):
        if f.suffix.lower() in AUDIO_EXTENSIONS:
            songs.append(
                {
                    "title": f.stem,
                    "path": str(f),
                    "filename": f.name,
                    "album": album_name,
                }
            )
    return jsonify({"results": songs})


@app.route("/api/local-search")
def api_local_search():
    q = request.args.get("q", "").strip().lower()
    results = []
    for f in sorted(FLOW_DIR.rglob("*")):
        if f.suffix.lower() in AUDIO_EXTENSIONS and q in f.stem.lower():
            results.append(
                {
                    "title": f.stem,
                    "path": str(f),
                    "filename": f.name,
                }
            )
    if MUSIC_DIR.exists():
        for f in sorted(MUSIC_DIR.rglob("*")):
            if f.suffix.lower() in AUDIO_EXTENSIONS and q in f.stem.lower():
                results.append(
                    {
                        "title": f.stem,
                        "path": str(f),
                        "filename": f.name,
                    }
                )
    return jsonify({"results": results})


@app.route("/api/liked")
def api_liked():
    liked_file = config.liked_music
    if not liked_file.exists():
        return jsonify({"results": []})
    liked_ids = set()
    liked_entries = []
    try:
        songs = json.loads(liked_file.read_text())
        for s in songs:
            url = s.get("url", "")
            title = s.get("title", "")
            if "v=" in url:
                vid = url.split("v=", 1)[1].split("&")[0]
                liked_ids.add(vid)
                liked_entries.append({"video_id": vid, "title": title})
    except Exception:
        pass
    huge_liked = pathlib.Path.home() / ".flow/downloads/liked songs"
    songs = []
    if huge_liked.exists():
        for f in sorted(huge_liked.iterdir()):
            if f.suffix.lower() in AUDIO_EXTENSIONS:
                songs.append(
                    {
                        "title": f.stem,
                        "path": str(f),
                        "filename": f.name,
                    }
                )
    return jsonify(
        {"results": songs, "liked_ids": list(liked_ids), "liked_entries": liked_entries}
    )


@app.route("/api/like", methods=["POST"])
def api_like():
    data = request.get_json(force=True)
    video_id = data.get("video_id", "").strip()
    title = data.get("title", "Unknown")
    if not video_id:
        return jsonify({"error": "missing video_id"}), 400
    liked_file = config.liked_music
    liked_file.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    songs = []
    if liked_file.exists():
        try:
            songs = json.loads(liked_file.read_text())
        except Exception:
            songs = []
    match = next((s for s in songs if s.get("url", "").endswith(f"v={video_id}")), None)
    if match:
        songs.remove(match)
        liked_file.write_text(json.dumps(songs, indent=2))
        return jsonify({"liked": False, "video_id": video_id})
    songs.append({"title": title, "url": url})
    liked_file.write_text(json.dumps(songs, indent=2))
    return jsonify({"liked": True, "video_id": video_id})


@app.route("/api/is-liked")
def api_is_liked():
    video_id = request.args.get("video_id", "").strip()
    if not video_id:
        return jsonify({"liked": False})
    liked_file = config.liked_music
    if not liked_file.exists():
        return jsonify({"liked": False})
    try:
        songs = json.loads(liked_file.read_text())
        for s in songs:
            if video_id in s.get("url", ""):
                return jsonify({"liked": True})
    except Exception:
        pass
    return jsonify({"liked": False})


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
        if "format" in data:
            if not config.set_format(data["format"]):
                return jsonify({"error": f"invalid format '{data['format']}'"}), 400
        existing.update(data)
        SETTINGS_FILE.write_text(json.dumps(existing, indent=2))
        return jsonify({"saved": True, "settings": existing})
    result = {}
    if SETTINGS_FILE.exists():
        try:
            result = json.loads(SETTINGS_FILE.read_text())
        except Exception:
            pass
    result["format"] = config.FORMAT
    return jsonify(result)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setting")
def setting_page():
    return render_template("setting.html")


@app.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")
