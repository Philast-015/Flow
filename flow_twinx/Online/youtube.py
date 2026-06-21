import yt_dlp

ydl_opts = {
    "quiet": True, "no_warnings": True, "noprogress": True,
    "noplaylist": True, "format": "bestaudio/best",
    "default_search": "ytsearch1", "skip_download": True,
}

ydl_opts_dwn = {
    "quiet": True, "no_warnings": True, "noprogress": True,
    "noplaylist": True, "format": "bestaudio/best",
    "outtmpl": "downloads/%(title)s.%(ext)s",
}

def search(query, limit=5):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        if not info.get("entries"):
            return []
        results = []
        for entry in info["entries"]:
            title = entry.get("title", "Unknown")
            dur = entry.get("duration", 0)
            results.append((entry, title, dur))
    return results

def download_url(url, outdir):
    opts = {**ydl_opts_dwn, "outtmpl": f"{outdir}/%(title)s.%(ext)s"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)