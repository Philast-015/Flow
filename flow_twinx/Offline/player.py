import sys
import time
import vlc
from ..imports import config
from .. import visualizer

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


def _display_loop(player, duration=0):
    display = config.Display
    if display == "none":
        return

    if display == "bars":
        visualizer.start()

    start = time.time()
    try:
        while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
            if display == "bars":
                bar_str = visualizer.render(color=S, reset=R)
                sys.stdout.write(f"\r{bar_str}")
                sys.stdout.flush()
            time.sleep(0.08)
    finally:
        if display == "bars":
            visualizer.stop()
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()


def play_file(filepath, title, args=None):
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
    m(f"    {dur_min}:{dur_sec:02d}")

    try:
        _display_loop(player, duration=duration)
    except KeyboardInterrupt:
        player.stop()
        sys.stdout.write("\n")
        sys.stdout.flush()
