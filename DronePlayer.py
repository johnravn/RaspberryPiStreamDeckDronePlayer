#!/usr/bin/env python3

# Program for raspberry pi drone player mainlny intended for house of worship use
# This program is used with the Elgato Stream Deck.
# The implementation of the streamdeck is based og the following library:

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Enjoy!

import time

time.sleep(10)

import os
import threading
import vlc
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Folder location of image assets used by this example
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

# Using two vlc players to achieve smooth transitions when switching keys
playerOne = vlc.MediaPlayer(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/C.mp3"))
playerTwo = vlc.MediaPlayer(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/D.mp3"))

# Lists for selecting images and songs
nowPlayingIcon = "blank"
keyIconsReleased = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "NowPlaying", nowPlayingIcon, "Stop"]
keySongs = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]

# Variable used for looping files
lastUsedMedia = vlc.Media(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/{}.mp3".format(keySongs[0])))

# List for counting how many buttons are pressed at once
quitList = []


# Function for when mediaPlayer one is finished, this is to trigger the
# second one to play the same Media as this is finished playing
def on_end_reached_one(event):
    global playerOne

    playerOne = vlc.MediaPlayer(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/C.mp3"))
    playerOne.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached_one)
    md = lastUsedMedia
    playerOne.set_media(md)
    playerOne.audio_set_volume(100)
    playerOne.play()
    playerOne.audio_set_volume(100)


# Same for the other Media player
def on_end_reached_two(event):
    global playerTwo

    playerTwo = vlc.MediaPlayer(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/C.mp3"))
    playerTwo.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached_two)
    md = lastUsedMedia
    playerTwo.set_media(md)
    playerTwo.audio_set_volume(100)
    playerTwo.play()
    playerTwo.audio_set_volume(100)
    
# Telling the media players to do the functions above when they are finished
playerOne.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached_one)
playerTwo.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached_two)

# Generates a custom tile with run-time generated text and custom image via the PIL module.
def render_key_image(deck, icon_filename):
    # Create new key image of the correct dimensions, black background
    image = PILHelper.create_image(deck)
    draw = ImageDraw.Draw(image)

    # Add image overlay, rescaling the image asset if it is too large to fit
    # the requested dimensions via a high quality Lanczos scaling algorithm
    icon = Image.open(icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, 0)
    image.paste(icon, icon_pos, icon)

    return PILHelper.to_native_format(deck, image)


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    
    if key == 13:
        name = "Now playing"
        icon = "Icons/{}.png".format(nowPlayingIcon)
    else:
        name = "emoji"
        # icon = "Icons/{}.png".format("Pressed" if state else "Released") -- Use this if you want to change button image when pressed
        icon = "Icons/{}.png".format(keyIconsReleased[key])

    return {
        "name": name,
        "icon": os.path.join(ASSETS_PATH, icon),
    }


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key
    key_style = get_key_style(deck, key, state)

    # Generate the custom key with the requested image and label
    image = render_key_image(deck, key_style["icon"])

    # Update requested key with the generated image
    deck.set_key_image(key, image)


# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):

    global nowPlayingIcon
    global lastUsedMedia
    
    # Variables for easy change of key values
    stopPlayingKey = 14
    fadeInTime = 2500
    fadeOutTime = 4000

    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)

    if state:
        # The program will quit if 3 or more buttons is pressed at once
        quitList.append(key)

        if len(quitList) > 2:
            quit(deck)

        
    else:

        key_style = get_key_style(deck, key, state)

        # Fades out both players when stop button is pressed
        if key == stopPlayingKey:
            fadeOut(playerOne, 5000)
            fadeOut(playerTwo, 5000)            
            nowPlayingIcon = "blank"
        elif key == 13:
            pass
        else:
            # Gets the media from button and changes the nowPlayingIcon
            newMedia = vlc.Media(os.path.join(os.path.dirname(__file__), "Assets/DronesTwo/{}.mp3".format(keySongs[key])))
            nowPlayingIcon = keyIconsReleased[key]

            # Switches player and plays media
            if playerOne.is_playing() == 1:
                playerTwo.set_media(newMedia)
                lastUsedMedia = newMedia
                
                fadeIn(playerTwo, fadeInTime)
                fadeOut(playerOne, fadeOutTime)
                
            else:
                playerOne.set_media(newMedia)
                lastUsedMedia = newMedia
                
                fadeIn(playerOne, fadeInTime)
                fadeOut(playerTwo, fadeOutTime)
                

        # Removes key from quitList when button is released
        quitList.remove(key)

    # Update the key image based on the new key state
    update_key_image(deck, key, state)
    update_key_image(deck, 13, state)

# Fade out function
def fadeOut(player, timer):
    while player.audio_get_volume() > 0:
        player.audio_set_volume(player.audio_get_volume() - 1)
        time.sleep(timer/100/1000)
    player.stop()

# Fade in function
def fadeIn(player, timer):
    player.play()
    while player.audio_get_volume() < 100:
        player.audio_set_volume(player.audio_get_volume() + 1)
        time.sleep(timer/100/1000)

# Quit function
def quit(deck):
    deck.reset()
    deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        
        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}')\n".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 50%
        deck.set_brightness(50)

        # Set initial key images
        for key in range(deck.key_count()):
            update_key_image(deck, key, False)

        # Register callback function for when a key state changes
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed)
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue

            if t.is_alive():
                t.join()