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
git clone https://github.com/yourusername/flow.git
cd flow
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Or use the installer script:

```bash
bash install.sh
```

## Usage

```bash
python main.py [-r] [-s] [-d]
```

Or direct if you have used install.sh

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
Flow/
├── config.py          # Configuration and theme settings
├── main.py            # Entry point and REPL loop
├── ping.py            # Internet connectivity check
├── tui.py             # Terminal UI helpers
├── requirements.txt   # Python dependencies
├── install.sh         # Installer script
├── Online/
│   ├── commands.py    # Online mode commands
│   ├── player.py      # VLC streaming player
│   └── youtube.py     # YouTube search and download
└── Offline/
    ├── commands.py    # Offline mode commands
    ├── file.py        # Library scanner and search
    └── player.py      # Local file player
```

## License

MIT
