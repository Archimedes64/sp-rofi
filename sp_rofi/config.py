import sys
import importlib.util
import os


spec = importlib.util.spec_from_file_location(
    "user_config", os.path.expanduser("~/.config/sp-rofi/config.py")
)
if spec is None or spec.loader is None:
    print(
        "Failure to load config please make sure that config.py is exists in ~/.config/sp-rofi/. quitting..."
    )
    sys.exit(1)

user_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_config)
try:
    SPOTIFY_CLIENT_ID = user_config.SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET = user_config.SPOTIFY_CLIENT_SECRET
    SPOTIFY_REDIRECT_URI = user_config.SPOTIFY_REDIRECT_URI
    SPOTIPY_CACHE_PATH = user_config.SPOTIPY_CACHE_PATH
    ALBUMS_PATH = user_config.ALBUMS_PATH
except AttributeError:
    print(
        "Config failed to load. Could you like maybe add SPOTIFY_CLIENT_ID SPOTIFY_CLIENT_SECRET SPOTIFY_REDIRECT_URI SPOTIPY_CACHE_PATH and ALBUMS_PATH to config.py?(for more information go to github.com/Archimedes64/sp-rofi"
    )
    sys.exit(1)
try:
    REMOVE_NOTIFICATIONS = user_config.REMOVE_NOTIFICATIONS
except AttributeError:
    print("REMOVE_NOTIFICATIONS not set. defaulting to False")
    REMOVE_NOTIFICATIONS = False

SPOTIPY_CACHE_PATH = os.path.expanduser(SPOTIPY_CACHE_PATH)
ALBUMS_PATH = os.path.expanduser(ALBUMS_PATH)

SPACE_BETWEEN_ICONS = "  "

ICONS = {
    "spotify": f"\uf1bc{SPACE_BETWEEN_ICONS}",
    "play": f"\uf04b{SPACE_BETWEEN_ICONS}",
    "pause": f"\uf04c{SPACE_BETWEEN_ICONS}",
    "next": f"\uf051{SPACE_BETWEEN_ICONS}",
    "prev": f"\uf048{SPACE_BETWEEN_ICONS}",
    "shuffle_on": f"\uf205{SPACE_BETWEEN_ICONS}",
    "shuffle_off": f"\uf204{SPACE_BETWEEN_ICONS}",
    "repeat": f"\uf01e{SPACE_BETWEEN_ICONS}",
    "vol_up": f"\uf028{SPACE_BETWEEN_ICONS}",
    "vol_down": f"\uf027{SPACE_BETWEEN_ICONS}",
    "vol_mute": f"\uf026{SPACE_BETWEEN_ICONS}",
    "set_vol": f"\uf1de{SPACE_BETWEEN_ICONS}",
    "artist": f"\uf007{SPACE_BETWEEN_ICONS}",
    "album": f"\uf001{SPACE_BETWEEN_ICONS}",
    "like": f"\uf004{SPACE_BETWEEN_ICONS}",
    "random": f"\uf074{SPACE_BETWEEN_ICONS}",
    "back": f"\uf053{SPACE_BETWEEN_ICONS}",
    "menu": f"\uf064{SPACE_BETWEEN_ICONS}",
    "lib": f"\uf02e{SPACE_BETWEEN_ICONS}",
    "delete": f"\uf05c{SPACE_BETWEEN_ICONS}",
    "monitor": f"󰍹{SPACE_BETWEEN_ICONS}",
    "speaker": f"󰓃{SPACE_BETWEEN_ICONS}",
    "phone": f"\uf10b{SPACE_BETWEEN_ICONS}",
    "hollow_heart": f"\uf08a{SPACE_BETWEEN_ICONS}",
    "list": f"\uf03a{SPACE_BETWEEN_ICONS}",
}
GO_BACK_MESSAGE = f"{ICONS['back']} Back"
