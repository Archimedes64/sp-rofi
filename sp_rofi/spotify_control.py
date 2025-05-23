from .utils import sp, load_albums
import time
from typing import Optional

"""
so uh. this file is a bit hard to explain. it was originially a script i made to use in the terminal. 
and i ported some of the functions from a previous project of mine. 
i need to a refactor but for now there is no issue with it.(will be an issue when i add notifications)
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
        elif action == "play_random_album":
            return play_random_album(sp)
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


def play_playlist(sp, query=None):
    # NOTE: vibe coded this 5 months ago. it works, so im fine with it.

    if query is None:
        return "Make sure to include the search query when setting the playlist"
    results = sp.current_user_playlists()
    user_playlists = results["items"]
    while results["next"]:
        results = sp.next(results)
        user_playlists.extend(results["items"])
    user_playlist = next(
        (p for p in user_playlists if p["name"].lower() == query.lower()), None
    )
    user_playlist = next(
        (p for p in user_playlists if p["name"].lower() in query.lower()),
        user_playlist,
    )
    if user_playlist:
        playlist_uri = user_playlist["uri"]
        sp.start_playback(context_uri=playlist_uri)
        return f"Playing user made playlist '{user_playlist['name']}'."

    results = sp.search(q=query, type="playlist", limit=1)
    if results["playlists"]["items"]:
        playlist_uri = results["playlists"]["items"][0]["uri"]
        sp.start_playback(context_uri=playlist_uri)
        return f"Playing playlist: {results['playlists']['items'][0]['name']}"
    else:
        return f"No matching playlist found for the query: {query}."


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
    query = album_name
    results = sp.search(q=query, type="album", limit=10)
    if not results["albums"]["items"]:
        return f"Album '{query}' not found."

    album = results["albums"]["items"][0]
    sp.shuffle(False)
    sp.start_playback(context_uri=album["uri"])
    return f"Playing '{album['name']}'."


def play_album_from_uri(sp, uri):
    sp.shuffle(False)
    sp.start_playback(context_uri=uri)
    return "Started album playback"


def play_random_album(sp):
    from random import choice

    albums = load_albums()
    chosen_album = choice(albums)
    play_album_from_uri(sp, chosen_album["uri"])
    return f"Playing random album: {chosen_album['name']}"
