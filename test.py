import vlc
import yt_dlp
import time

ydl_opts = {
    "quiet": False, "no_warnings": True, "noprogress": True,
    "noplaylist": True, "format": "bestaudio/best",
    "default_search": "ytsearch1", "skip_download": True,
}

query = input("Enter song name: ").strip()
if not query:
    exit()

print("Searching...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
    entry = info["entries"][0]
    title = entry.get("title", "Unknown")
    print(f"Now playing: {title}")
    stream_url = None
    for fmt in reversed(entry.get("formats", [])):
        if fmt.get("acodec") != "none":
            stream_url = fmt["url"]
            break

if not stream_url:
    print("Could not get stream URL")
    exit()

instance = vlc.Instance("--no-video --quiet")
player = instance.media_player_new()
media = instance.media_new(stream_url)
player.set_media(media)
print("Playing... Press Ctrl+C to stop.\n")
print(stream_url)

try:
    while True:
        player.play()
        time.sleep(0.5)
except KeyboardInterrupt:
    player.stop()
    print("\nStopped.")
