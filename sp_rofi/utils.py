import subprocess
import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth

from .config import (
    SPOTIPY_CACHE_PATH,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_CLIENT_SECRET,
    ALBUMS_PATH,
)

"""functions used by multiple files. should be split up into multiple files, but this project is small enough so its fine"""


def prompt_rofi_text(prompt_text: str) -> str:
    proc = subprocess.run(
        ["rofi", "-dmenu", "-i", "-p", prompt_text, "-config", "text_box"],
        input="",
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def prompt_rofi_menu(prompt_text: str, entries: list) -> str:
    items = "\n".join(entries)
    proc = subprocess.run(
        ["rofi", "-dmenu", "-markup-rows", "-i", "-p", prompt_text],
        input=items,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


class RofiException(Exception):
    pass


class RofiCancelledError(RofiException):
    # When rofi is cancelled or returns a blank string
    def __init__(self):
        super().__init__("Rofi was cancelled by the user")


class RofiTextCancelledError(RofiException):
    def __init__(self):
        super().__init__("Rofi(text input mode) was cancelled by the user")


class RofiInvalidChoiceError(RofiException):
    def __init__(self, menu_name: str, selected_item: str):
        self.menu_name = menu_name
        self.selected_item = selected_item
        super().__init__(f"Invalid choice '{selected_item}' is not in menu {menu_name}")


class GoBackSignal:
    """
    returned when the user presses go back in a action.
    feels easier to read if it looks like this instead of None or 0
    """


def play_album_from_uri(sp, uri):
    sp.shuffle(False)
    sp.start_playback(context_uri=uri)
    return "Started album playback"


def load_albums():
    try:
        with open(ALBUMS_PATH, "r") as f:
            albums = json.load(f)
    except FileNotFoundError:
        print("ALBUMS NOT FOUND. making new file")
        albums = []
        with open(ALBUMS_PATH, "w") as f:
            json.dump(albums, f, indent=2)
    return albums


sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        open_browser=False,
        scope="user-modify-playback-state,user-library-modify,user-read-playback-state",
        cache_path=SPOTIPY_CACHE_PATH,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
    )
)


def send_notification(content):
    subprocess.run(["notify-send", "Spotify Rofi", content])
