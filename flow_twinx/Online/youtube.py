import yt_dlp

BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "noplaylist": True,
    "format": "bestaudio/best",
    "skip_download": True,
}

ydl_opts = {
    **BASE_OPTS,
    "default_search": "ytsearch1",
}

ydl_opts_dwn = {
    **BASE_OPTS,
    "skip_download": False,
    "outtmpl": "downloads/%(title)s.%(ext)s",
}

ydl_opts_search = {
    **BASE_OPTS,
    "default_search": "ytsearch1",
}

ydl_opts_radio = {
    **BASE_OPTS,
    "noplaylist": False,
    "extract_flat": True,
}

ydl_opts_play = {
    **BASE_OPTS,
}


def search(query, limit=3):
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


def fetch_radio(query, max_results=30):
    with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info.get("entries"):
            return []
        video_id = info["entries"][0].get("id")
        if not video_id:
            return []

    radio_url = f"https://www.youtube.com/watch?v={video_id}&list=RDMM{video_id}"
    opts = {**ydl_opts_radio, "playlistend": max_results}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(radio_url, download=False)
        entries = info.get("entries", [])
        results = []
        for entry in entries:
            title = entry.get("title", "Unknown")
            vid = entry.get("id")
            dur = entry.get("duration", 0)
            if vid:
                results.append((title, vid, dur))
    return results


def get_entry(url):
    with yt_dlp.YoutubeDL(ydl_opts_play) as ydl:
        return ydl.extract_info(url, download=False)
