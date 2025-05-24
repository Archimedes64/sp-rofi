import json
from .config import GO_BACK_MESSAGE, ALBUMS_PATH
from .utils import (
    RofiCancelledError,
    RofiInvalidChoiceError,
    RofiTextCancelledError,
    GoBackSignal,
    prompt_rofi_menu,
    prompt_rofi_text,
    load_albums,
    sp,
    play_album_from_uri,
)


class AlbumNotFound(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


def search_for_albums(query, limit=10) -> list:
    """Searches albums formats into a dict to easily tell if seen before.
    if seen before then that means theres a clean version of the albums. usally this is the second album in the list returned
    but just in case check if the second album is explicit if so overwrite the original.(i assume no one would want it to not work like this)
    """

    results = sp.search(q=query, type="album", limit=limit, market="US")
    if results is None or not results["albums"]["items"]:
        raise AlbumNotFound(f"No album found with query {query}")
    albums = {}
    for album in results["albums"]["items"]:
        artist = album["artists"][0]["name"]
        artist_id = album["artists"][0]["id"]
        genres = sp.artist(artist_id)["genres"]

        release_year = album["release_date"][:4]
        name = album["name"]
        if name in albums and albums[name]["artist"] == artist:
            print(
                "multiple albums found of same name and by same artist. taking the explicit one"
            )
            tracks = sp.album_tracks(album["id"])["items"]
            if not any(track["explicit"] for track in tracks):
                print("second album was clean. keeping original")
                continue
        album_uri = album["uri"]
        albums[name] = {
            "name": name,
            "artist": artist,
            "release_year": release_year,
            "genres": genres,
            "uri": album_uri,
        }

    return list(albums.values())


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
    album_strs += [GO_BACK_MESSAGE]
    album_selection = prompt_rofi_menu("Album", album_strs)

    if not album_selection:
        raise RofiCancelledError
    if album_selection == GO_BACK_MESSAGE:
        return GoBackSignal()
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
