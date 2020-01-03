from dmxpy import DmxPy
import time
import sys
import json
import rtmidi
from colors import *

SWITCH_TIME = 10
FRONT_BRIGHTNESS = 0.7
BACK_BRIGHTNESS = 0.7
MIDI_SLEEP = 0.1
PALETTE_NUM = 0
NUM_PALETTES = 0
PALETTE = {}
COLOR_VALUES = {}
JELLY_ON = False
MODE="brightness"

def jelly_code(color_name):
    if color_name == "red":
        return 1
    else:
        return 0

def set_color(location, color, change_fraction=1.0):
    (r, g, b) = get_rgb(color)
    COLOR_VALUES[location] = color #save_these

    #print ("back_brightness:" + str(BACK_BRIGHTNESS))
    #print ("front_brightness:" + str(FRONT_BRIGHTNESS))
    
    for light in lights["lights"]:
        if location in light["location"]:
            channel = light["channel"]
            brightness = BACK_BRIGHTNESS
            if "front" in light["location"]:
                brightness = FRONT_BRIGHTNESS
                
            if light["type"] == "RGB":
                dmx.setChannel(channel, (int) (r * brightness))
                dmx.setChannel(channel + 1, (int) (g * brightness))
                dmx.setChannel(channel + 2, (int) (b * brightness))
            elif light["type"] == "RGBx3":
                dmx.setChannel(channel, (int) (r * brightness))
                dmx.setChannel(channel + 1, (int) (g * brightness))
                dmx.setChannel(channel + 2, (int) (b * brightness))
                dmx.setChannel(channel + 3, (int) (r * brightness))
                dmx.setChannel(channel + 4, (int) (g * brightness))
                dmx.setChannel(channel + 5, (int) (b * brightness))
                dmx.setChannel(channel + 6, (int) (r * brightness))
                dmx.setChannel(channel + 7, (int) (g * brightness))
                dmx.setChannel(channel + 8, (int) (b * brightness))
            elif light["type"] == "jelly_dome" and change_fraction == 1.0:
                bright_val = brightness * 199

                (closest, c_dist) = closest_color(color, ["red", "green", "blue", "yellow", "cyan", "magenta", "white"])
                if c_dist > 0.1:
                    closest = "white"

                rotation = 255 # sound active
                if not JELLY_ON:
                    bright_val = 0
                    rotation = 0 # off
                    
                dmx.setChannel(channel, int(bright_val))
                dmx.setChannel(channel + 1, int(jelly_code(closest) * 16))
                dmx.setChannel(channel + 2, rotation)

def fade_colors(left_start, left_end, center_start, center_end, right_start, right_end):
    for i in range(1, 11):
        change_fraction = (i / 10.0)
        left_color = change_color(left_start, left_end, change_fraction)
        center_color = change_color(center_start, center_end, change_fraction)
        right_color = change_color(right_start, right_end, change_fraction)
        set_color("left", left_color, change_fraction)
        set_color("center", center_color, change_fraction)
        set_color("right", right_color, change_fraction)
        dmx.render()
        time.sleep(0.2)

def usage():
    print ("palette.json controls.json lights.json")

def handle_midi_command(midi_in, commands):
    global PALETTE_NUM
    global NUM_PALETTES
    global FRONT_BRIGHTNESS
    global BACK_BRIGHTNESS
    global SWITCH_TIME
    global MODE
    
    while True:
        msg = midi_in.get_message()
        if not msg:
            return

        (t, velocity) = msg
        l = [ hex(e) for e in t]
        first = l[0]
        second = l[1]
        value = None
        if len(l) > 2:
            value = int(l[2], 16)

        #print ("first:" + str(first) + " second:" + str(second) + " value:" + str(value))
        key = (first, second)
        if not key in commands:
            continue
        command = commands[key]

        #print ("command:" + str(command))
        
        if (command == "next_palette" and value == 0):
            PALETTE_NUM = (PALETTE_NUM + 1) % NUM_PALETTES
            set_palette()
        elif (command == "prev_palette" and value == 0):
            PALETTE_NUM = (PALETTE_NUM + NUM_PALETTES - 1) % NUM_PALETTES
            set_palette()
        elif (command == "brightness"):
            MODE = "brightness"
        elif (command == "timing"):
            MODE = "timing"
        elif (command == "first_adjust" and MODE == "brightness"):
            FRONT_BRIGHTNESS = float(value) / 123.0
            set_brightness()
        elif (command == "second_adjust" and MODE == "brightness"):
            BACK_BRIGHTNESS = float(value) / 123.0
            set_brightness()
        elif (command == "first_adjust" or command == "back_adjust") and MODE == "timing":
            SWITCH_TIME = 40.0 * (float(value) / 123.0)
        elif (command == "home"):
            PALETTE_NUM = 0
            set_palette()
        elif (command == "toggle_palette"):
            JELLY_ON = not JELLY_ON
            set_brightness()


def commands_from_controls(controls):
    midi_to_command = {}
    for (command,matchers) in controls.items():
        key = (matchers["first"], matchers["second"])
        if key in midi_to_command:
            print ("same midi for:" + midi_to_command[key] + " and " + command)
            continue
        midi_to_command[key] = command

    #print str("midi_to_command:" + str(midi_to_command))
    return midi_to_command

def set_palette():
    global PALETTE
    global COLORS
    global PALETTE_NUM
    PALETTE = palettes["palettes"][PALETTE_NUM]
    print ("cycling: " + PALETTE["name"])
    COLORS = [resolve_color(c, palettes) for c in PALETTE["colors"]]
    #print ("COLORS:" + str(COLORS))
    num_colors = len(COLORS)
    set_color("left", COLORS[0])
    set_color("center", COLORS[1])
    set_color("right", COLORS[2% num_colors])
    dmx.render()

def set_brightness():
    set_color("left", COLOR_VALUES["left"])
    set_color("center", COLOR_VALUES["center"])
    set_color("right", COLOR_VALUES["right"])
    dmx.render()
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
        sys.exit(-1)

    midiin = rtmidi.MidiIn()
    midiin.close_port()
    midiin.open_port(1)

    dmx = DmxPy.DmxPy('/dev/ttyUSB0')
    dmx.blackout()

    palette_path = sys.argv[1]
    palette_f = open(palette_path, "r")
    controls_path = sys.argv[2]
    # starting_palette = sys.argv[3].strip()
    controls_f = open(controls_path, "r")
    controls_lines = controls_f.read()
    controls = json.loads(controls_lines)
    commands = commands_from_controls(controls)
    lights_path = sys.argv[3]
    lights_f = open(lights_path, "r")
    lights_lines = lights_f.read()
    lights = json.loads(lights_lines)
    
    palette_lines = palette_f.read()
    palettes = json.loads(palette_lines)
    NUM_PALETTES = len(palettes["palettes"])
    # for p in range(0, len(palettes["palettes"])):
    #     if palettes["palettes"][p]["name"] == starting_palette:
    #         break
    # PALETTE_NUM = p

    set_palette()
    
    count = 0
    while True:
        num_colors = len(COLORS)
        fade_colors(COLORS[count % num_colors], COLORS[(count + 1)% num_colors],
                    COLORS[(count + 1)% num_colors], COLORS[(count + 2)% num_colors],
                    COLORS[(count + 2)% num_colors], COLORS[(count + 3)% num_colors])

        i = 0
        while True:
            num_sleeps = int(SWITCH_TIME / MIDI_SLEEP)
            if i > num_sleeps:
                break
            
            i+= 1
            time.sleep(MIDI_SLEEP)
            handle_midi_command(midiin, commands)
        count += 1
    
