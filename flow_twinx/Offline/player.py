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


def play_file(filepath, title, args=None):
    repeat = args and getattr(args, "r", False)
    shuffle = args and getattr(args, "s", False)

    while True:
        instance = vlc.Instance("--no-video --quiet")
        player = instance.media_player_new()
        media = instance.media_new(str(filepath))
        player.set_media(media)
        player.play()

        duration = 0
        for _ in range(50):
            duration = player.get_length() / 1000
            if duration > 0:
                break
            time.sleep(0.1)
        if duration <= 0:
            duration = 0
        dur_min, dur_sec = divmod(int(duration), 60)
        i(f"\nPlaying : {title}")
        m(f"    {dur_min}:{dur_sec:02d} | repeat:{repeat} | shuffle:{shuffle}")

        start = time.time()
        try:
            while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
                elapsed = time.time() - start
                bar = _progress_bar(elapsed, duration)
                sys.stdout.write(f"\r{S}{bar}{R}")
                sys.stdout.flush()
                time.sleep(0.5)
        except KeyboardInterrupt:
            player.stop()
            sys.stdout.write("\n")
            sys.stdout.flush()
            break

        sys.stdout.write("\n")
        sys.stdout.flush()

        if not repeat:
            break
