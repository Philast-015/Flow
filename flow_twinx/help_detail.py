from . import config

_T = config.Primary
_M = config.Tertiary
_B = config.Secondary
_G = config.Muted
_R = config.Reset

ONLINE_HELP = {
    "play": [
        f"{_T}> play{_R} {_M}<query | index | liked>{_R}",
        f"{_G}  Search and play a song from YouTube.{_R}",
        f"  {_M}<query>{_R}   {_G}Search YouTube and play the top result{_R}",
        f"  {_M}<index>{_R}   {_G}Play a song by index from last search results{_R}",
        f"  {_M}liked{_R}     {_G}Play all liked songs{_R}",
        f"  {_M}Flags:{_R} {_G}{_M}-bg{_R} {_G}background{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}play never gonna give you up{_R}",
        f"    {_G}play 3{_R}",
        f"    {_G}play liked{_R}",
    ],
    "search": [
        f"{_T}> search{_R} {_M}<query>{_R}",
        f"{_G}  Search YouTube for tracks. Lists results with indices.{_R}",
        f"{_G}  Use the index with {_M}'play <index>' {_G}to play a specific result.{_R}",
        f"  {_G}Example:{_R}",
        f"    {_G}search daft punk{_R}",
    ],
    "like": [
        f"{_T}> like{_R}",
        f"{_G}  Like the currently playing song.{_R}",
        f"{_G}  Liked songs are saved to {_M}~/.flow/liked.txt{_R}",
        f"{_G}  Use {_M}'play liked'{_G} to play all liked songs.{_R}",
    ],
    "download": [
        f"{_T}> download{_R} {_M}<query | index>{_R}",
        f"{_G}  Download audio from YouTube without playing.{_R}",
        f"  {_M}<query>{_R}   {_G}Search and download the top result{_R}",
        f"  {_M}<index>{_R}   {_G}Download by index from last search results{_R}",
        f"{_G}  Downloads are saved to {_M}~/.flow/downloads/{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}download never gonna give you up{_R}",
        f"    {_G}download 2{_R}",
    ],
    "savan": [
        f"{_T}> savan{_R} {_M}<query | index>{_R}",
        f"{_G}  Search and play a song from JioSaavn.{_R}",
        f"  {_M}<query>{_R}   {_G}Search JioSaavn and play the top result{_R}",
        f"  {_M}<index>{_R}   {_G}Play song by index from last savan-s results{_R}",
        f"  {_M}Flags:{_R} {_G}{_M}-bg{_R} {_G}background{_R}",
        f"  {_G}Alias:{_R} {_M}svn{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}savan hello{_R}",
        f"    {_G}savan 2{_R}",
    ],
    "savan-s": [
        f"{_T}> savan-s{_R} {_M}<query>{_R}",
        f"{_G}  Search JioSaavn for tracks. Lists results with indices.{_R}",
        f"{_G}  Use the index with {_M}'savan <index>' {_G}to play a specific result.{_R}",
        f"  {_G}Alias:{_R} {_M}svn-s{_R}",
        f"  {_G}Example:{_R}",
        f"    {_G}savan-s daft punk{_R}",
    ],
    "radio": [
        f"{_T}> radio{_R} {_M}<song_name> [index]{_R}",
        f"{_G}  Generate a radio mix based on a reference song.{_R}",
        f"  {_M}<song_name>{_R}  {_G}Search and play a radio mix from YouTube{_R}",
        f"  {_M}[index]{_R}       {_G}Play a specific track from the last radio list{_R}",
        f"  {_M}Flags:{_R} {_G}{_M}-bg{_R} {_G}background{_R}",
        f"{_G}  Press Ctrl+C for next track, Ctrl+Q to quit. Alias:{_R} {_M}rd{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}radio daft punk{_R}",
        f"    {_G}radio 5{_R}",
    ],
    "switch": [
        f"{_T}> switch{_R}",
        f"{_G}  Switch to Offline mode.{_R}",
        f"{_G}  Requires an active internet connection.{_R}",
    ],
    "help": [
        f"{_T}> help{_R}",
        f"{_G}  Show this help message.{_R}",
    ],
    "short": [
        f"{_T}> short{_R} {_M}[index] [new_command]{_R}",
        f"{_G}  View or edit command shortcuts.{_R}",
        f"{_G}  With no arguments, list all shortcuts.{_R}",
        f"  {_M}<index>{_R}          {_G}Show shortcut at that index{_R}",
        f"  {_M}<index> <value>{_R}  {_G}Update shortcut at index to new command{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}short{_R}",
        f"    {_G}short 3{_R}",
        f"    {_G}short 3 list{_R}",
    ],
    "exit": [
        f"{_T}> exit{_R}",
        f"{_G}  Exit Flow Music Player.{_R}",
        f"{_G}  Aliases:{_R} {_M}quit{_R}, {_M}q{_R}",
    ],
    "stop": [
        f"{_T}> flow --stop{_R}",
        f"{_G}  Stop all background VLC processes.{_R}",
        f"{_G}  Use from shell: {_M}flow --stop{_R}",
    ],
}

OFFLINE_HELP = {
    "play": [
        f"{_T}> play{_R} {_B}<query | index | all | liked | album>{_R}",
        f"{_G}  Play a song from your local music library.{_R}",
        f"  {_B}<query>{_R}   {_G}Search and play matching song{_R}",
        f"  {_B}<index>{_R}   {_G}Play song by index from last search results{_R}",
        f"  {_B}all{_R}       {_G}Play all songs in the library{_R}",
        f"  {_B}liked{_R}     {_G}Play all liked songs{_R}",
        f"  {_B}<album>{_R}   {_G}Play all songs in a specific album{_R}",
        f"  {_B}Flags:{_R} {_G}{_B}-bg{_R} {_G}background{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}play never gonna{_R}",
        f"    {_G}play 2{_R}",
        f"    {_G}play all{_R}",
        f"    {_G}play liked{_R}",
        f"    {_G}play Greatest Hits{_R}",
    ],
    "search": [
        f"{_T}> search{_R} {_B}<query>{_R}",
        f"{_G}  Search your local music library for matching songs.{_R}",
        f"{_G}  Lists results with indices for use with {_B}'play <index>'{_R}",
        f"  {_G}Example:{_R}",
        f"    {_G}search daft punk{_R}",
    ],
    "list": [
        f"{_T}> list{_R}",
        f"{_G}  List your entire music library.{_R}",
        f"{_G}  Shows Songs, Albums, and Liked Songs sections.{_R}",
    ],
    "like": [
        f"{_T}> like{_R}",
        f"{_G}  Like the currently playing song from offline mode.{_R}",
        f"{_G}  Liked songs are copied to {_B}~/.flow/music/Liked/{_R}",
        f"{_G}  Use {_B}'play liked'{_G} to play all liked songs.{_R}",
    ],
    "switch": [
        f"{_T}> switch{_R}",
        f"{_G}  Switch to Online mode.{_R}",
        f"{_G}  Requires an active internet connection.{_R}",
    ],
    "help": [
        f"{_T}> help{_R}",
        f"{_G}  Show this help message.{_R}",
    ],
    "short": [
        f"{_T}> short{_R} {_B}[index] [new_command]{_R}",
        f"{_G}  View or edit command shortcuts.{_R}",
        f"{_G}  With no arguments, list all shortcuts.{_R}",
        f"  {_B}<index>{_R}          {_G}Show shortcut at that index{_R}",
        f"  {_B}<index> <value>{_R}  {_G}Update shortcut at index to new command{_R}",
        f"  {_G}Examples:{_R}",
        f"    {_G}short{_R}",
        f"    {_G}short 3{_R}",
        f"    {_G}short 3 list{_R}",
    ],
    "exit": [
        f"{_T}> exit{_R}",
        f"{_G}  Exit Flow Music Player.{_R}",
        f"{_G}  Aliases:{_R} {_B}quit{_R}, {_B}q{_R}",
    ],
    "stop": [
        f"{_T}> flow --stop{_R}",
        f"{_G}  Stop all background VLC processes.{_R}",
        f"{_G}  Use from shell: {_B}flow --stop{_R}",
    ],
}
