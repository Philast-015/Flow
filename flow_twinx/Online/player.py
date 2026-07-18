import sys
import time
import threading
import vlc
from ..imports import config
from .. import lyrics, visualizer

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


def _display_loop(player, title, video_id=None, duration=0, stop_check=None):
    display = config.Display
    if display == "none":
        return

    fetched_lyrics = None
    if display == "lyrics":
        if video_id:
            fetched_lyrics = lyrics.fetch_lyrics(video_id, title=title)
        if not fetched_lyrics:
            m("    No synced lyrics found")

    if display == "bars":
        visualizer.start()

    start = time.time()
    last_lyric_line = None
    try:
        while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
            if stop_check and stop_check():
                break
            elapsed = time.time() - start
            if display == "bars":
                bar_str = visualizer.render(color=P, reset=R)
                sys.stdout.write(f"\r{bar_str}")
                sys.stdout.flush()
            elif display == "lyrics" and fetched_lyrics:
                line = lyrics.find_line(fetched_lyrics, elapsed)
                if line and line != last_lyric_line:
                    last_lyric_line = line
                    time.sleep(0.3)
                    print(f"  {P}{line}{R}")
            time.sleep(0.08)
    finally:
        if display == "bars":
            visualizer.stop()


def play_url(url, title, args=None, duration=0):
    instance = vlc.Instance("--no-video --quiet")
    player = instance.media_player_new()
    media = instance.media_new(url)
    player.set_media(media)
    player.play()

    dur_min, dur_sec = divmod(int(duration), 60)
    i(f"\n⤘ Now : {title}")
    m(f"    {dur_min}:{dur_sec:02d}")

    try:
        _display_loop(player, title, duration=duration)
    except KeyboardInterrupt:
        player.stop()
        sys.stdout.write("\n")
        sys.stdout.flush()


def play_entry(entry, title, args=None, flags=None):
    title = title.split("|")[0]

    instance = vlc.Instance("--no-video --quiet")
    player = instance.media_player_new()

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
    video_id = entry.get("id")
    dur_min, dur_sec = divmod(int(duration), 60)
    i(f"\n⤘ Now : {title}")
    m(f"    {dur_min}:{dur_sec:02d}")

    skipped = False

    def stop_check():
        nonlocal skipped
        if flags:
            if flags.get("quit", lambda: False)():
                player.stop()
                return True
            if flags.get("skip", lambda: False)():
                skipped = True
                player.stop()
                return True
        return False

    try:
        _display_loop(player, title, video_id=video_id, duration=duration, stop_check=stop_check)
    except KeyboardInterrupt:
        player.stop()
        sys.stdout.write("\n")
        sys.stdout.flush()
