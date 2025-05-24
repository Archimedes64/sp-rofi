#!/usr/bin/env python3
import time
import sys
from typing import Callable, Union, Optional

from . import spotify_control as sc
from .album_manager import delete_album, add_an_album as add_album, play_album
from .config import ICONS, GO_BACK_MESSAGE, REMOVE_NOTIFICATIONS
from .utils import (
    GoBackSignal,
    prompt_rofi_menu,
    prompt_rofi_text,
    RofiTextCancelledError,
    RofiInvalidChoiceError,
    RofiCancelledError,
    RofiException,
    send_notification,
)


class Action:
    def __init__(
        self,
        name: str,  # What the user sees on rofi
        action: str,  # Action inputed to spotify_control
        arg: Optional[
            str
        ] = None,  # Optional argument to be put into spotify_control. ie: setting shuffle to off would need arg = "false"
        prompt: Optional[
            str
        ] = None,  # Prompt used to get input from the user for arg. ie: setting custom volume would need "Volume (%)"
    ) -> None:
        self.name = name
        self.action = action
        self.arg = arg
        self.prompt = prompt

    def execute(self):
        if self.prompt is not None:
            user_response = prompt_rofi_text(self.prompt)
            if not user_response:
                raise RofiTextCancelledError
            return sc.spotify_control(self.action, user_response)
        return sc.spotify_control(self.action, self.arg)


class CustomAction:
    "For actions not in spotify_control"

    def __init__(
        self,
        name: str,  # See above
        custom_handling: Callable,  # Function that does the custom handling
    ) -> None:
        self.name = name
        self.custom_handling = custom_handling

    def execute(self):
        return self.custom_handling()


class Menu:
    def __init__(
        self, name: str, items: list[Union[CustomAction, Action, "Menu"]]
    ) -> None:
        self.name = name
        self.items = items
        self.submenus = [item for item in items if isinstance(item, Menu)]

    def __repr__(self) -> str:
        return self.name

    def _construct_item_dictionary(self, previous_menu: Optional["Menu"] = None):
        item_dict = {item.name: item for item in self.items}
        if previous_menu is not None:
            item_dict[GO_BACK_MESSAGE] = previous_menu
        return item_dict

    def select_item(
        self, previous_menu: Optional["Menu"] = None
    ) -> Union[CustomAction, Action, "Menu"]:
        item_dict = self._construct_item_dictionary(
            previous_menu
        )  # make items a dict so its easier to tell which item was picked
        selected_item = prompt_rofi_menu(self.name, list(item_dict.keys()))
        if not selected_item:
            raise RofiCancelledError()
        if selected_item not in item_dict:
            raise RofiInvalidChoiceError(self.name, selected_item)
        return item_dict[selected_item]


def run_control(action: str, arg: Optional[str] = None):
    return sc.spotify_control(action, arg)


def switch_devices():
    devices = sc.sp.devices()
    if devices is None:
        raise NotImplementedError
    devices_dict = {}
    for device in devices["devices"]:
        if device["type"] == "Smartphone":
            device_icon = ICONS["phone"]
        elif device["type"] == "Computer":
            device_icon = ICONS["monitor"]
        else:
            device_icon = ICONS[
                "speaker"
            ]  # usally the types will just be Smartphone Computer and Speaker, but just in case all extras are speakers

        devices_dict[device_icon + device["name"]] = device
    devices_dict[GO_BACK_MESSAGE] = "place holder"
    selected_device_name = prompt_rofi_menu("Device", list(devices_dict.keys()))
    if selected_device_name == GO_BACK_MESSAGE:
        return GoBackSignal()
    if selected_device_name not in devices_dict:
        raise RofiInvalidChoiceError("Switch Devices", selected_device_name)
    if not selected_device_name:
        raise RofiTextCancelledError
    selected_device = devices_dict[selected_device_name]
    sc.sp.transfer_playback(device_id=selected_device["id"], force_play=True)
    return f"Switched playback to {selected_device_name}"


def set_volume():
    preset_volumes = [
        f"{ICONS['set_vol']} Custom",
        f"{ICONS['vol_up']} 75%",
        f"{ICONS['vol_down']} 50%",
        f"{ICONS['vol_mute']} 25%",
    ]

    preset_volumes = preset_volumes + [GO_BACK_MESSAGE]
    vol_selection = prompt_rofi_menu("Set Volume", preset_volumes)
    if not vol_selection:
        raise RofiCancelledError
    elif vol_selection == GO_BACK_MESSAGE:
        return GoBackSignal()
    elif vol_selection == preset_volumes[0]:
        custom_vol = prompt_rofi_text("Volume (%)").strip(
            "%"
        )  # no one would actualy put the % but just in case
        if not custom_vol:
            raise RofiTextCancelledError
        if not custom_vol.isdigit():
            return "Please set volume to a valid number"
        return run_control("set", custom_vol)
    else:
        if vol_selection not in preset_volumes:
            raise RofiInvalidChoiceError("Set Volume", vol_selection)
        return run_control("set", vol_selection[-3:].strip("%"))


def play_from_queue():
    queue = sc.sp.queue()
    if not queue:
        return "Queue is empty"
    queue = queue["queue"][:7]
    formated_queue = {
        f"{song['name']} <small> - {song['artists'][0]['name']} </small>".replace(
            "&", "&amp;"
        ): index
        for index, song in enumerate(queue)
    }
    formated_queue[GO_BACK_MESSAGE] = (
        0  # place holder but incase GO_BACK_MESSAGE somehow goes forward it wont skip any songs
    )
    print(formated_queue)
    selected_song = prompt_rofi_menu("Queue", list(formated_queue.keys()))
    if not selected_song:
        raise RofiCancelledError
    if selected_song not in formated_queue:
        raise RofiInvalidChoiceError("Queue", selected_song)
    if selected_song == GO_BACK_MESSAGE:
        return GoBackSignal()

    for _ in range(formated_queue[selected_song] + 1):
        try:
            sc.sp.next_track()
        except Exception:
            return "Spotify Failed Try again in a bit."
        time.sleep(0.4)

    return "Now Playing Your Song :)"


play_album_menu = Menu(
    name=f"{ICONS['album']} Play Album",
    items=[
        Action(name=f"{ICONS['random']} Random Album", action="play_random_album"),
        CustomAction(name=f"{ICONS['album']} Preset", custom_handling=play_album),
        Action(
            name=f"{ICONS['set_vol']} Custom Album", action="play_album", prompt="Album"
        ),
    ],
)
libary_add_menu = Menu(
    name=f"{ICONS['like']} Add to Libary",
    items=[
        Action(name=f"{ICONS['like']} Like Song", action="like_song"),
        CustomAction(name=f"{ICONS['set_vol']} Add Album", custom_handling=add_album),
        Action(
            name=f"{ICONS['list']} Add Current Song to Playlist",
            action="add_current_to_playlist",
        ),
        Action(
            name=f"{ICONS['song']} Add Song to Playlist",
            action="add_to_playlist",
            prompt="Song",
        ),
    ],
)
libary_delete_menu = Menu(
    name=f"{ICONS['delete']} Remove From Libary",
    items=[
        CustomAction(
            name=f"{ICONS['delete']} Delete Album", custom_handling=delete_album
        ),
        Action(name=f"{ICONS['hollow_heart']} Unlike Song", action="unlike_song"),
        Action(
            name=f"{ICONS['list']} Remove Current Song From Playlist",
            action="remove_current_from_playlist",
        ),
        Action(
            name=f"{ICONS['song']} Remove Song From Playlist",
            action="remove_from_playlist",
            prompt="Song",
        ),
    ],
)

loop_menu = Menu(
    name=f"{ICONS['repeat']} Loop",
    items=[
        Action(name=f"{ICONS['repeat1']} Context", action="loop", arg="context"),
        Action(name=f"{ICONS['repeat2']} Track", action="loop", arg="track"),
        Action(name=f"{ICONS['repeat_off']} Off", action="loop", arg="off"),
    ],
)
shuffle_menu = Menu(
    name=f"{ICONS['random']} Shuffle",
    items=[
        Action(name=f"{ICONS['shuffle_on']} On", action="shuffle", arg="true"),
        Action(name=f"{ICONS['shuffle_off']} Off", action="shuffle", arg="false"),
    ],
)

control_menu = Menu(
    name=f"{ICONS['play']} Controls",
    items=[
        Action(name=f"{ICONS['play']} Resume", action="play"),
        Action(name=f"{ICONS['pause']} Pause", action="pause"),
        Action(name=f"{ICONS['next']} Next Song", action="next_song"),
        Action(name=f"{ICONS['prev']} Previous Song", action="previous_song"),
    ],
)
change_playback_menu = CustomAction(
    name=f"{ICONS['speaker']} Change Device", custom_handling=switch_devices
)

main_menu = Menu(
    name=f"{ICONS['spotify']} Spotify",
    items=[
        Menu(
            name=f"{ICONS['album']} Quick Play",
            items=[
                play_album_menu,
                Action(
                    name=f"{ICONS['artist']} Play Artist",
                    action="play_artist",
                    prompt="Artist",
                ),
                Action(
                    name=f"{ICONS['list']} Play Playlist",
                    action="play_playlist",
                    prompt="Playlist",
                ),
                Menu(
                    name=f"{ICONS['song']} Play Song",  # icon for song is a record. so thats kinda stupid
                    items=[
                        Action(
                            name=f"{ICONS['play']} Play Song",
                            action="play_song",
                            prompt="Song",
                        ),
                        Action(
                            name=f"{ICONS['album']} Add to Queue",  # no good symbol for this. so just picking generic music notesI
                            action="add_to_queue",
                            prompt="Song",
                        ),
                        CustomAction(
                            name=f"{ICONS['list']} Play song in queue",
                            custom_handling=play_from_queue,
                        ),
                    ],
                ),
            ],
        ),
        Menu(
            name=f"{ICONS['lib']} Manage Libary",
            items=[libary_add_menu, libary_delete_menu],
        ),
        Menu(
            name=f"{ICONS['menu']} Playback",
            items=[
                control_menu,
                loop_menu,
                shuffle_menu,
                change_playback_menu,
            ],
        ),
        Menu(
            name=f"{ICONS['vol_up']} Volume",
            items=[
                Action(name=f"{ICONS['vol_up']} Increase", action="increase"),
                Action(name=f"{ICONS['vol_down']} Decrease", action="decrease"),
                Action(name=f"{ICONS['vol_mute']} Mute", action="set", arg="0"),
                CustomAction(
                    name=f"{ICONS['set_vol']} Set", custom_handling=set_volume
                ),
            ],
        ),
    ],
)


def main():
    try:
        menus = [main_menu]
        while True:
            current_menu = menus[-1]
            previous_menu = menus[-2] if len(menus) > 1 else None
            selection = current_menu.select_item(previous_menu)

            if isinstance(selection, (Action, CustomAction)):
                result = selection.execute()
                if isinstance(
                    result, GoBackSignal
                ):  # much cleaner than my original idea(please dont ask what it was)
                    continue

                elif isinstance(result, str):
                    if REMOVE_NOTIFICATIONS:
                        sys.exit(0)
                    send_notification(result)
                else:
                    raise Exception(
                        f"Result was of type {type(selection)} current menu is {current_menu}. please fix.(.execute must return a string or GoBackSignal)"
                    )
                sys.exit(0)
            elif isinstance(selection, Menu):
                if previous_menu is selection:
                    menus.pop()
                else:
                    menus.append(selection)
            else:
                raise Exception(
                    "Menu had item that is not a valid class. Either there is more classes than you thought, or you(me) messed up the menus"
                )

    except RofiException:
        sys.exit(1)


if __name__ == "__main__":
    main()
