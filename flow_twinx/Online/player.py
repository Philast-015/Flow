import sys
import time
import vlc
from ..imports import config

P = config.Primary
S = config.Secondary
T = config.Tertiary
M = config.Muted
E = config.Red
R = config.Reset

m = lambda t: print(f"{M}{t}{R}")
e = lambda t: print(f"{E}{t}{R}")
i = lambda t: print(f"{P if config.Mode == 'Online' else S}{t}{R}")
t = lambda t: print(f"{T}{t}{R}")

BAR_WIDTH = 40


def _progress_bar(elapsed, total):
    if total <= 0:
        return ""
    fraction = min(elapsed / total, 1.0)
    filled = int(fraction * BAR_WIDTH)
    bar = "/" * filled + " " * (BAR_WIDTH - filled)
    pct = int(fraction * 100)
    return f"  [{bar}] {pct}%"


def play_entry(entry, title, args=None, filepath=None, flags=None):
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
        i(f"\n⤘ Now : {title}")
        m(f"    {dur_min}:{dur_sec:02d} | repeat:{args.r} | shuffle:{args.s}")

        start = time.time()
        skipped = False
        try:
            while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
                if flags:
                    if flags.get("quit", lambda: False)():
                        player.stop()
                        return
                    if flags.get("skip", lambda: False)():
                        skipped = True
                        player.stop()
                        break
                elapsed = time.time() - start
                bar = _progress_bar(elapsed, duration)
                sys.stdout.write(f"\r{P}{bar}{R}")
                sys.stdout.flush()
                time.sleep(0.5)
        except KeyboardInterrupt:
            player.stop()
            sys.stdout.write("\n")
            sys.stdout.flush()
            break

        sys.stdout.write("\n")
        sys.stdout.flush()

        if skipped or not repeat:
            break