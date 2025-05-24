from sp_rofi.album_manager import format_albums_for_rofi, search_for_albums
from sp_rofi.config import GO_BACK_MESSAGE
from .utils import (
    GoBackSignal,
    sp,
    play_album_from_uri,
    load_albums,
    prompt_rofi_menu,
    RofiCancelledError,
    RofiInvalidChoiceError,
)
import time
from typing import Optional

"""
so uh. this file is a bit hard to explain(bc it sucks). it was originially a script i made to use in the terminal, but that kind of sucks(alot to remeber). 
so thats why the weird main spotify_control function parses strings.
Additionally, I ported most of the functions from a previous project of mine that i made a while ago.
"""


def spotify_control(action: str, arg: Optional[str]):
    try:
        if action == "next_song":
            sp.next_track()
            return "Skipped to next track."
        elif action == "previous_song":
            sp.previous_track()
            return "Went back to previous track."
        elif action == "play":
            sp.start_playback()
            return "Playback started."
        elif action == "pause":
            sp.pause_playback()
            return "Playback paused."
        elif action == "shuffle":
            if arg == "true":
                return shuffle(sp, True)
            elif arg == "false":
                return shuffle(sp, False)
        elif action == "play_artist":
            return play_artist(sp, arg)
        elif action == "play_album":
            return play_album(sp, arg)
        elif action == "play_song":
            return play_song(sp, arg)
        elif action == "add_to_queue":
            return add_to_queue(sp, arg)
        elif action == "play_random_album":
            return play_random_album(sp)
        elif action == "remove_current_from_playlist":
            return delete_current_song_from_playlist(sp)
        elif action == "add_current_to_playlist":
            return add_current_song_to_playlist(sp)
        elif action == "add__to_playlist":
            song = prompt_for_song(arg)
            if isinstance(song, GoBackSignal):
                return song
            return add_song_to_playlist(sp, song["name"], song["uri"])
        elif action == "remove_from_playlist":
            song = prompt_for_song(arg)
            if isinstance(song, GoBackSignal):
                return song
            return delete_song_from_playlist(sp, song["name"], song["uri"])
        elif action == "loop":
            arg = arg.strip().lower()
            if arg not in ["off", "track", "context"]:
                return "Argument of loop must be off, track, or context"
            sp.repeat(arg)
            return f"Loop mode set to {arg}."
        elif action == "like_song":
            return save_current_track(sp)
        elif action == "unlike_song":
            return unsave_current_track(sp)
        elif action == "set":
            return set_volume(sp, arg)
        elif action == "decrease":
            return decrease_volume(sp)
        elif action == "increase":
            return increase_volume(sp)
        elif action == "play_playlist":
            return play_playlist(sp, arg)
        else:
            return "Unknown command"
    except Exception as e:
        return f"Error: {e}"


def search_for_song(song, limit):
    results = sp.search(q=song, type="track", limit=limit)
    if not results:
        return None
    results = results["tracks"]["items"]
    return {
        f"{song['name']} <small> - {song['artists'][0]['name']}  {'[E]' if song['explicit'] else ''}</small>".replace(
            "&", "&amp;"
        ): song
        for song in results
    }


def prompt_for_song(arg):
    formated_searches = search_for_song(arg, limit=7)
    if not formated_searches:
        return f"No songs found for query {arg}"
    formated_searches[GO_BACK_MESSAGE] = "placeholder"
    selected_song = prompt_rofi_menu("Song", list(formated_searches.keys()))
    if not selected_song:
        raise RofiCancelledError
    if selected_song not in formated_searches:
        raise RofiInvalidChoiceError("Add Song To queue", selected_song)
    if selected_song == GO_BACK_MESSAGE:
        return GoBackSignal()
    return formated_searches[selected_song]


def add_to_queue(sp, arg):
    song = prompt_for_song(arg)
    if isinstance(song, GoBackSignal):
        return song
    sp.add_to_queue(song["uri"])
    return f"Adding {song['name']} to queue"


def play_song(sp, arg):
    song = prompt_for_song(arg)
    if isinstance(song, GoBackSignal):
        return song
    sp.start_playback(uris=[song["uri"]])
    return f"Playing {song['name']}"


def save_current_track(sp, trys=2):
    current = sp.current_playback()
    track_id = current["item"]["id"]
    for _ in range(trys + 1):
        sp.current_user_saved_tracks_add([track_id])
        time.sleep(1)
    return "Liked the current track."


def unsave_current_track(sp, trys=2):
    current = sp.current_playback()
    track_id = current["item"]["id"]
    for _ in range(trys + 1):
        sp.current_user_saved_tracks_delete([track_id])
        time.sleep(1)
    return "Removed current track from liked songs."


def retreive_editable_playlists():
    current_user = sp.current_user()
    user_id = current_user["id"]

    editable_playlists = {}

    limit = 50
    offset = 0

    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        for playlist in playlists["items"]:
            if playlist["owner"]["id"] == user_id or playlist["collaborative"]:
                editable_playlists[playlist["name"]] = {
                    "id": playlist["id"],
                }
        if playlists["next"]:
            offset += limit
        else:
            break
    return editable_playlists


def delete_current_song_from_playlist(sp):
    playlist_id = select_playlist()
    if isinstance(playlist_id, GoBackSignal):
        return playlist_id
    current_track = sp.current_user_playing_track()
    if not current_track:
        return "No current playback"
    sp.playlist_remove_all_occurrences_of_items(
        playlist_id, [current_track["item"]["uri"]]
    )
    return f"Removing {current_track['item']['name']} from your playlist"


def add_current_song_to_playlist(sp):
    playlist_id = select_playlist()
    if isinstance(playlist_id, GoBackSignal):
        return playlist_id
    current_track = sp.current_user_playing_track()
    if not current_track:
        return "No current playback"
    sp.playlist_add_items(playlist_id, [current_track["item"]["uri"]])
    return f"Adding {current_track['item']['name']} to your playlist"


def add_song_to_playlist(sp, song_name, song_uri):
    playlist_id = select_playlist()
    if isinstance(playlist_id, GoBackSignal):
        return playlist_id
    sp.playlist_add_items(playlist_id, [song_uri])
    return f"Adding {song_name} to your playlist"


def delete_song_from_playlist(sp, song_name, song_uri):
    playlist_id = select_playlist()
    if isinstance(playlist_id, GoBackSignal):
        return playlist_id
    sp.playlist_remove_all_occurrences_of_items(playlist_id, [song_uri])
    return f"Removing {song_name} from your playlist"


def select_playlist():
    playlists = retreive_editable_playlists()
    playlists[GO_BACK_MESSAGE] = "playlist"
    selected_playlist = prompt_rofi_menu("Playlist", list(playlists.keys()))
    if not selected_playlist:
        raise RofiCancelledError
    if selected_playlist not in playlists:
        raise RofiInvalidChoiceError("Playlist", selected_playlist)
    if selected_playlist == GO_BACK_MESSAGE:
        return GoBackSignal()
    return playlists[selected_playlist]["id"]


def play_playlist(sp, query=None):
    # NOTE: vibe coded this 5 months ago. it works, so im fine with it. well ive had to edit it now. so function isnt completly vibecoded i guess?

    if query is None:
        return "Make sure to include the search query when setting the playlist"
    results = sp.current_user_playlists()
    user_playlists = results["items"]
    while results["next"]:
        results = sp.next(results)
        user_playlists.extend(results["items"])

    user_playlist = next(
        (p for p in user_playlists if p["name"].lower() in query.lower()),
        None,
    )
    user_playlist = next(
        (p for p in user_playlists if p["name"].lower() == query.lower()), user_playlist
    )
    if user_playlist:
        playlists = user_playlist
    else:
        playlists = []
    results = sp.search(q=query, type="playlist", limit=10 - len(playlists))

    if results["playlists"]["items"]:
        playlists.extend(results["playlists"]["items"])
    if not playlists:
        return f"No matching playlist found for the query: {query}."

    playlist_dict = {
        f"{playlist['name']} - <small>{playlist['owner']['display_name']} ({playlist['tracks']['total']})</small>": playlist
        for playlist in playlists
        if playlist is not None
    }  # make it a dict so its easy
    playlist_dict[GO_BACK_MESSAGE] = "placeholder"
    selected_playlist = prompt_rofi_menu("Playlist", list(playlist_dict.keys()))
    if not selected_playlist:
        raise RofiCancelledError()
    elif selected_playlist not in playlist_dict:
        raise RofiInvalidChoiceError("Play Playlist", selected_playlist)
    elif selected_playlist == GO_BACK_MESSAGE:
        return GoBackSignal()
    playlist = playlist_dict[selected_playlist]
    sp.start_playback(context_uri=playlist["uri"])
    return (
        f"Playling playlist {playlist['name']} by {playlist['owner']['display_name']}"
    )


def shuffle(sp, param):
    playback = sp.current_playback()
    if playback and not playback["actions"]["disallows"].get("toggling_shuffle", False):
        device_id = playback["device"]["id"]
        sp.shuffle(param, device_id=device_id)
    return f"Shuffle {'enabled' if param else 'disabled'}."


def set_volume(sp, volume_percent=0):
    volume_percent = int(volume_percent)
    if volume_percent > 100 or volume_percent < 0:
        return "Volume must be between 0 and 100"
    sp.volume(volume_percent)
    return f"Volume set to {volume_percent}%."


def decrease_volume(sp):
    volume = next(
        device["volume_percent"]
        for device in sp.devices()["devices"]
        if device["is_active"]
    )
    if volume - 10 < 0:
        return "Volume too low to decrease"
    sp.volume(volume - 10)
    return f"Volume decreased to {volume - 10}%"


def increase_volume(sp):
    volume = next(
        device["volume_percent"]
        for device in sp.devices()["devices"]
        if device["is_active"]
    )
    if volume + 10 > 100:
        return "Volume too high to increase"
    sp.volume(volume + 10)
    return f"Volume increased to {volume + 10}%"


def play_artist(sp, artist=None):
    # NOTE: vibe coded this 5 months ago. it works, so im fine with it.
    artist_query = artist
    if not artist_query:
        return "Provide an artist name."

    search_results = sp.search(q=artist_query, type="artist", limit=1)
    if not search_results["artists"]["items"]:
        return f"Artist '{artist_query}' not found."

    artist = search_results["artists"]["items"][0]
    artist_id = artist["id"]
    albums = []
    album_results = sp.artist_albums(artist_id, album_type="album,single", limit=50)
    albums.extend(album_results["items"])
    while album_results.get("next"):
        album_results = sp.next(album_results)
        albums.extend(album_results["items"])

    if not albums:
        return f"No albums found for artist '{artist_query}'."

    track_uris = {}
    for album in albums:
        album_tracks = sp.album_tracks(album["id"])
        for track in album_tracks["items"]:
            track_uris[track["uri"]] = track["name"]

    if not track_uris:
        return f"No tracks found for artist '{artist_query}'."

    import random

    track_list = list(track_uris.keys())
    random.shuffle(track_list)
    sp.start_playback(uris=track_list)
    return f"Now playing shuffled tracks of '{artist['name']}'."


def play_album(sp, album_name=None):
    albums = format_albums_for_rofi(search_for_albums(album_name, limit=5))
    if not albums:
        return f"No albums found for query: {album_name}"
    albums[GO_BACK_MESSAGE] = "placeholder"

    selected_album = prompt_rofi_menu("Album", list(albums.keys()))
    if not selected_album:
        raise RofiCancelledError
    if selected_album not in albums:
        raise RofiInvalidChoiceError("Play Album", selected_album)
    if selected_album == GO_BACK_MESSAGE:
        return GoBackSignal()
    album = albums[selected_album]
    play_album_from_uri(sp, album["uri"])

    return f"Playing '{album['name']}' by {album['artist']}."


def play_random_album(sp):
    from random import choice

    albums = load_albums()
    chosen_album = choice(albums)
    play_album_from_uri(sp, chosen_album["uri"])
    return f"Playing random album: {chosen_album['name']}"
