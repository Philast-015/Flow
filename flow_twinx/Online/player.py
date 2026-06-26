import sys
import time
import vlc
from ..imports import tprint

m = tprint(color="grey", border="none")
e = tprint(color="red", border="none")
i = tprint(color="theme", border="none")

BAR_WIDTH = 40


def _progress_bar(elapsed, total):
    if total <= 0:
        return ""
    fraction = min(elapsed / total, 1.0)
    filled = int(fraction * BAR_WIDTH)
    bar = "/" * filled + " " * (BAR_WIDTH - filled)
    pct = int(fraction * 100)
    return f"  [{bar}] {pct}%"


def play_entry(entry, title, args=None, filepath=None, stop_on_interrupt=False):
    title = title.split("|")[0]
    repeat = args and getattr(args, "r", False)

    while True:
        instance = vlc.Instance("--no-video --quiet")
        player = instance.media_player_new()

        if filepath:
            media = instance.media_new(filepath)
        else:
            stream_url = None
            for fmt in reversed(entry.get("formats", [])):
                if fmt.get("acodec") != "none":
                    stream_url = fmt["url"]
                    break
            if not stream_url:
                e("     No playable stream found")
                return
            media = instance.media_new(stream_url)

        player.set_media(media)
        player.play()

        duration = entry.get("duration", 0)
        dur_min, dur_sec = divmod(int(duration), 60)
        i(f"\n>> Now : {title}")
        m(f"    {dur_min}:{dur_sec:02d} | repeat:{args.r} | shuffle:{args.s}")

        start = time.time()
        try:
            while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
                elapsed = time.time() - start
                bar = _progress_bar(elapsed, duration)
                sys.stdout.write(f"\r\x1b[36m{bar}\x1b[0m")
                sys.stdout.flush()
                time.sleep(0.5)
        except KeyboardInterrupt:
            player.stop()
            sys.stdout.write("\n")
            sys.stdout.flush()
            if stop_on_interrupt:
                raise
            break

        sys.stdout.write("\n")
        sys.stdout.flush()

        if not repeat:
            break