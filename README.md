# Flow

A terminal-based music player with online streaming and offline library modes.

## Features

- **Dual-mode operation** — It will automatically detect internet and switch between online streaming and offline playback.
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
uv run flow_twinx/main.py
```

Or through pip:

```bash
pip install flow-twinx
```

### Note: Make sure you vlc installed or it will not play music.

## Usage

```bash
cd flow_twinx
uv run main.py
```
Or direct if you have used pypi
```bash
flow
```

| Flag | Description                                    |
| ---- | ---------------------------------------------- |
| `-r` | Repeat mode (loop current track)               |
| `-s` | Shuffle mode (random order)                    |
| `-d` | Download mode (save streamed audio to library) |
| `-i` | Use it in help command to show detailed help   |

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
| `help -i`                 | Show available commands with detailed explanation                      |

## Configuration

- Downloads and library are stored in `~/.flow/downloads/`
- Liked songs (online) are saved to `~/.flow/liked.txt`
- Liked songs (offline) are copied to `~/.flow/downloads/liked songs/`

## Project Structure

```
flow/
├── flow_twinx/
│   ├── __init__.py
│   ├── config.py               
│   ├── imports.py              
│   ├── main.py                 
│   ├── ping.py                 
│   ├── tui.py                  
│   ├── Online/
│   │   ├── __init__.py
│   │   ├── commands.py         
│   │   ├── player.py           
│   │   └── youtube.py
│   └── Offline/                
│       ├── __init__.py
│       ├── commands.py         
│       ├── file.py             
│       ├── player.py           
│       └── youtube.py         
├── pyproject.toml
└── README.md
```

## License

Use however you want just mention me for inspiration.
