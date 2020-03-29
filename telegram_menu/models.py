#!/usr/bin/env python
#
# A python library for generating Telegram menus
# Copyright (C) 2020
# Armel MEVELLEC <mevellea@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

"""Messages and navigation models."""

import datetime
import logging
from enum import Enum, auto

import emoji


class ButtonType(Enum):
    """Button type enumeration."""

    NOTIFICATION = auto()
    MESSAGE = auto()
    PICTURE = auto()


class MenuButton:  # pylint: disable=too-few-public-methods
    """Base button class, wrapper for label with _callback.
    
    Args:
        label (str): button label
        callback (obj, optional): method called on button selection
        btype (ButtonType, optional): button type
    
    """

    def __init__(self, label, callback=None, btype=ButtonType.NOTIFICATION):
        """Init MenuButton class."""
        self.label = label
        self.callback = callback
        self.btype = btype

    def __str__(self):
        """Represent button as text.
        
        Returns:
            str: button label
        
        """
        return self.label


class BaseMessage:
    """Base message class, buttons array and label updater.
    
    Args:
        navigation (telegram_menu.navigation.NavigationManager): navigation manager
        label (str): message label
    
    """

    def __init__(self, navigation, label):
        """Init BaseMessage class."""
        self.keyboard = []
        self.label = label
        self.is_inline = False
        self._navigation = navigation

        # previous values are used to check if it has changed, to skip sending identical message
        self._keyboard_previous: [MenuButton] = []
        self._content_previous = None

    def get_button(self, label):
        """Get button matching given label.
        
        Args:
            label (str): message label
    
        Returns:
            MenuButton: button matching label

        Raises:
            EnvironmentError: too many buttons matching label

        """
        buttons = [x for x in self.keyboard if x.label == label]
        if len(buttons) > 1:
            raise EnvironmentError("More than one button with same label")
        if not buttons:
            return None
        return buttons[0]

    @staticmethod
    def emojize(emoji_name):
        """Get utf-16 code for emoji, defined in https://www.webfx.com/tools/emoji-cheat-sheet/.

        Args:
            emoji_name (str): emoji label
    
        Returns:
            str: emoji encoded as string

        """
        return emoji.emojize(f":{emoji_name}:", use_aliases=True)

    def add_button(self, label, callback=None):
        """Add a button to keyboard attribute.

        Args:
            label (str): button label
            callback (obj, optional): method called on button selection
    
        """
        self.keyboard.append(MenuButton(label, callback))

    def edit_message(self):
        """Request navigation controller to update current message.
        
        Returns:
            bool: True if message was edited
        
        """
        return self._navigation.edit_message(self)

    def content_updater(self):
        """Update message content."""
        raise NotImplementedError


class MenuMessage(BaseMessage):
    """Base menu, wrapper for main keyboard.
    
    Args:
        navigation (telegram_menu.navigation.NavigationManager): navigation manager
        label (str): message label
    
    """

    def __init__(self, navigation, label):
        """Init MenuMessage class."""
        BaseMessage.__init__(self, navigation, label)

    def content_updater(self):
        """Update message content."""
        raise NotImplementedError


class AppMessage(BaseMessage):
    """Base menu, wrapper for message with inline keyboard.
    
    Args:
        navigation (telegram_menu.navigation.NavigationManager): navigation manager
        label (str): message label
    
    """

    EXPIRING_DELAY = 120  # seconds

    def __init__(self, navigation, label):
        """Init AppMessage class."""
        BaseMessage.__init__(self, navigation, label)
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._status = None
        self.home_after = False
        self.message_id = None
        self.is_inline = True
        self.time_alive = None
        self.expiry_period = datetime.timedelta(seconds=self.EXPIRING_DELAY)

    def is_alive(self):
        """Update message time stamp."""
        self.time_alive = datetime.datetime.now()

    def has_expired(self):
        """Return True if expiry date of message has expired.
        
        Returns:
            bool: True if timer has expired
        
        """
        return self.time_alive + self.expiry_period < datetime.datetime.now()

    def kill_message(self):
        """Display status before message is destroyed."""
        self._logger.debug("Removing message '%s' (%s)", self.label, self.message_id)

    def content_updater(self):
        """Update message content, virtual method."""
        raise NotImplementedError


def format_list_to_html(args_array):
    """Format array of strings in html, first element bold.
    
    Args:
        args_array (list): text content
    
    """
    content = ""
    for line in args_array:
        if isinstance(line, list):
            if line[0] != "":
                content += f"<b>{line[0]}</b>"
                if line[1] != "":
                    content += ": "
            if line[1] != "":
                content += line[1]
        else:
            content += f"<b>{line}</b>"

        content += "\n"
    return content
