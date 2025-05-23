import json
from urllib.parse import uses_relative
from .spotify_control import play_album_from_uri
from .config import ICONS, ALBUMS_PATH
from .utils import (
    RofiCancelledError,
    RofiInvalidChoiceError,
    RofiTextCancelledError,
    prompt_rofi_menu,
    prompt_rofi_text,
    load_albums,
    sp,
)


class AlbumNotFound(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


def search_for_albums(query, limit=10):
    results = sp.search(q=query, type="album", limit=limit, market="US")
    if results is None or not results["albums"]["items"]:
        raise AlbumNotFound(f"No album found with query {query}")
    albums = []
    for album in results["albums"]["items"]:
        artist = album["artists"][0]["name"]
        artist_id = album["artists"][0]["id"]
        genres = sp.artist(artist_id)["genres"]  # pyright: ignore
        release_year = album["release_date"][:4]
        name = album["name"]
        album_uri = album["uri"]
        albums.append(
            {
                "name": name,
                "artist": artist,
                "release_year": release_year,
                "genres": genres,
                "uri": album_uri,
            }
        )
    return albums


def format_albums_for_rofi(albums):
    formated_albums = {}
    for a in albums:
        formated_albums[
            f"{a['name']} - <small> {a['artist']}</small>  <small>[{a['release_year']} | {'/'.join(a['genres'])}]</small>".replace(
                "&", "&amp;"
            )
        ] = a
    return formated_albums


def add_album(album):
    albums = load_albums()
    albums.append(album)
    write_to_albums(albums)


def _delete_album(index):
    index = int(index)
    albums = load_albums()
    del albums[index]
    write_to_albums(albums)


def delete_album_from_string(album_str: str):
    indexs = []
    print(album_str)
    for index, album in enumerate(load_albums()):
        if album["name"] == album_str:
            indexs.append(index)
    if indexs:
        _delete_album(max(indexs))
    return


def delete_album():
    albums = format_albums_for_rofi(load_albums())
    album_strs = list(albums.keys())
    album_strs += [f"{ICONS['back']} Back"]
    album_selection = prompt_rofi_menu("Album", album_strs)

    if not album_selection:
        raise RofiCancelledError
    if album_selection == f"{ICONS['back']} Back":
        raise RofiTextCancelledError  # scummy. scummy. scummy.
    selected_album_name = albums[album_selection]["name"]
    delete_album_from_string(selected_album_name)
    return f"Deleting Album {selected_album_name}."


def write_to_albums(albums):
    with open(ALBUMS_PATH, "w") as f:
        json.dump(albums, f, indent=2)


def list_albums():
    albums = load_albums()

    return albums


def update_album(album):
    changes = ["Change Name", "Change Artist", "Change Year", "Change Genres"]
    picked_change = prompt_rofi_menu(album["name"], changes)
    if picked_change == changes[3]:
        while True:
            new_genres = prompt_rofi_text('Genres? sepereate by "/" ')
            if not new_genres:
                raise RofiTextCancelledError
            options = ["Yes", "No"]
            choice = prompt_rofi_menu(
                f"Are you sure you want genres: {new_genres}", options
            )
            if choice not in options:
                raise RofiInvalidChoiceError("Update Albums", choice)
            if choice == "Yes":
                break
        album["genres"] = new_genres.split("/")
    elif picked_change == changes[0]:
        while True:
            new_genres = prompt_rofi_text("Album Name?")
            if not new_genres:
                raise RofiTextCancelledError
            options = ["Yes", "No"]
            choice = prompt_rofi_menu(
                f"Are you sure you want to change the name to: {new_genres}", options
            )
            if choice not in options:
                raise RofiInvalidChoiceError("Update Albums", choice)
            if choice == "Yes":
                break
        album["name"] = new_genres
    elif picked_change == changes[2]:
        while True:
            new_genres = prompt_rofi_text("Year?")
            if not new_genres:
                raise RofiTextCancelledError
            options = ["Yes", "No"]
            choice = prompt_rofi_menu(
                f"Are you sure you want to change the year to: {new_genres}",
                options,
            )
            if choice not in options:
                raise RofiInvalidChoiceError("Update Albums", choice)
            if choice == "Yes":
                break
        album["release_year"] = new_genres
    elif picked_change == changes[1]:
        while True:
            new_genres = prompt_rofi_text("Artist/Band Name?")
            if not new_genres:
                raise RofiTextCancelledError
            options = ["Yes", "No"]
            choice = prompt_rofi_menu(
                f"Are you sure you want to change the artist/band to: {new_genres}",
                options,
            )
            if choice not in options:
                raise RofiInvalidChoiceError("Update Albums", choice)
            if choice == "Yes":
                break
        album["artist"] = new_genres
    return album


def play_album():
    albums = format_albums_for_rofi(load_albums())
    picked_album = prompt_rofi_menu("Album", list(albums.keys()))

    if not picked_album:
        raise RofiCancelledError
    if picked_album not in albums:
        raise RofiInvalidChoiceError("Play Preset Album", picked_album)
    album = albums[picked_album]
    play_album_from_uri(sp, album["uri"])
    return f"Playing ALbum{album['name']}"


def add_an_album():
    query = prompt_rofi_text("Album Name")
    albums = format_albums_for_rofi(search_for_albums(query))
    picked_album = prompt_rofi_menu(query.title(), list(albums.keys()))
    album = albums[picked_album]
    message = "Do you want to change anything"
    while True:
        options = ["Yes", "No"]
        user_choice = prompt_rofi_menu(message, options)
        if not user_choice:
            raise RofiCancelledError
        if user_choice not in options:
            raise RofiInvalidChoiceError("Add Album", user_choice)
        if user_choice == "Yes":
            album = update_album(album)
            message = "Do you want to change anything else?"
            continue
        break
    add_album(album)
    return f"Adding Album {album['name']}"
