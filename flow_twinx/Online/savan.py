import json
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://teenapi.dino.icu/api"


def search(query, limit=10):
    params = urllib.parse.urlencode({"query": query, "limit": str(limit)})
    url = f"{API_BASE}/search/songs?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return []
    if not data.get("success"):
        return []
    results = data["data"].get("results", [])
    out = []
    for r in results:
        name = r.get("name", "Unknown")
        dur = r.get("duration", 0)
        primary = r["artists"].get("primary", [])
        artist = primary[0]["name"] if primary else "Unknown"
        out.append((r, f"{name} - {artist}", dur))
    return out


def best_url(entry):
    dls = entry.get("downloadUrl", [])
    if not dls:
        return None
    pref = {"320kbps", "160kbps", "96kbps", "48kbps", "12kbps"}
    best = None
    for q in pref:
        for dl in dls:
            if dl["quality"] == q:
                best = dl["url"]
                break
        if best:
            break
    return best or dls[0]["url"]


def download(url, dest):
    urllib.request.urlretrieve(url, dest)
    return dest
