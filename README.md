# Flow

A terminal-based music player with online streaming and offline library modes.

## Features

- **Dual-mode operation** — Automatically detects internet and switches between online streaming and offline playback
- **Online mode** — Search and stream audio from YouTube via `yt-dlp` and `python-vlc`
- **Offline mode** — Play local audio files with album support, search, and a liked-songs collection
- **Download** — Save tracks from YouTube to your local library with the `-d` flag
- **Repeat & shuffle** — Loop tracks or play in random order
- **Like/unlike** — Save favorites to a dedicated playlist
- **Tab completion** — Auto-complete commands and song names in offline mode
- **Colored TUI** — Cyan theme for online, magenta for offline, with borders and banners

## Requirements

- Python 3
- [VLC](https://www.videolan.org/vlc/) media player (for `python-vlc` bindings)

## Installation

```bash
git clone https://github.com/Philast-015/Flow.git
cd flow
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Or through pip:

```bash
pip install flow-twinx
```

### Note: Make sure you have python and vlc installed

## Usage

```bash
cd flow_twinx
python main.py [-r] [-s] [-d]
```

Or direct if you have used pypi

```bash
flow <command> <flag>
```

| Flag | Description                                    |
| ---- | ---------------------------------------------- |
| `-r` | Repeat mode (loop current track)               |
| `-s` | Shuffle mode (random order)                    |
| `-d` | Download mode (save streamed audio to library) |

### Commands

| Command                | Description                                  |
| ---------------------- | -------------------------------------------- |
| `play <name or #>`     | Play a song by name or search result number  |
| `search <query>`       | Search YouTube (online) or library (offline) |
| `list`                 | Show all songs, albums, or liked tracks      |
| `like <name or #>`     | Add a song to your liked collection          |
| `download <name or #>` | Save a streamed song to the local library    |
| `switch`               | Toggle between online and offline mode       |
| `help`                 | Show available commands                      |

## Configuration

- Downloads and library are stored in `~/.flow/downloads/`
- Liked songs (online) are saved to `~/.flow/liked.txt`
- Liked songs (offline) are copied to `~/.flow/downloads/liked songs/`

## Project Structure

```
flow/
├── flow_twinx/                 # Main application package
│   ├── __init__.py
│   ├── config.py               # Configuration, themes, paths
│   ├── imports.py              # Central import hub
│   ├── main.py                 # Entry point / CLI
│   ├── ping.py                 # Connection checker
│   ├── tui.py                  # Terminal UI helpers (colors, banner, input)
│   ├── Online/                 # Online streaming mode
│   │   ├── __init__.py
│   │   ├── commands.py         # Online command handlers
│   │   ├── player.py           # VLC-based stream player
│   │   └── youtube.py          # YouTube search & download via yt-dlp
│   └── Offline/                # Offline local library mode
│       ├── __init__.py
│       ├── commands.py         # Offline command handlers
│       ├── file.py             # Local file & library management
│       ├── player.py           # VLC-based local file player
│       └── youtube.py          # Placeholder
├── pyproject.toml              # Package metadata & build config
├── requirements.txt            # Dependencies (python-vlc, yt_dlp)
└── README.md
```

## License

MIT
