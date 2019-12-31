from dmxpy import DmxPy
import time
import sys
import json
import rtmidi
from colors import *

SWITCH_TIME = 10
BRIGHTNESS = 0.7
MIDI_SLEEP = 0.1
PALETTE_NUM = 0
NUM_PALETTES = 0
PALETTE = {}
LIGHTS_VALUES = {}


def set_light_color(light_number, color):
    (r, g, b) = get_rgb(color)
    LIGHTS_VALUES[light_number] = color #save_these
    dmx.setChannel(light_number * 3 + 1, (int) (r * BRIGHTNESS))
    dmx.setChannel(light_number * 3 + 2, (int) (g * BRIGHTNESS))
    dmx.setChannel(light_number * 3 + 3, (int) (b * BRIGHTNESS))
                   
def change_color(color_start, color_end, change_fraction):
    (r_start, g_start, b_start) = get_rgb(color_start)
    (r_end, g_end, b_end) = get_rgb(color_end)
    new_r = (r_end * change_fraction + r_start * (1 - change_fraction))
    new_g = (g_end * change_fraction + g_start * (1 - change_fraction))
    new_b = (b_end * change_fraction + b_start * (1 - change_fraction))

    new_color = get_hex(int(new_r), int(new_g), int(new_b))
    return new_color


def fade_colors(light1_start, light1_end, light2_start, light2_end, light3_start, light3_end):
    for i in range(1, 11):
        change_fraction = (i / 10.0)
        light1_color = change_color(light1_start, light1_end, change_fraction)
        light2_color = change_color(light2_start, light2_end, change_fraction)
        light3_color = change_color(light3_start, light3_end, change_fraction)
        set_light_color(0, light1_color)
        set_light_color(1, light2_color)
        set_light_color(2, light3_color)
        dmx.render()
        time.sleep(0.2)

def usage():
    print ("palette.json controls.json")

def handle_midi_command(midi_in, commands):
    global PALETTE_NUM
    global NUM_PALETTES
    global BRIGHTNESS
    global SWITCH_TIME
    
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

        key = (first, second)
        if not key in commands:
            continue
        command = commands[key]

        if (command == "next_palette" and value == 0):
            PALETTE_NUM = (PALETTE_NUM + 1) % NUM_PALETTES
            set_palette()
        elif (command == "prev_palette" and value == 0):
            PALETTE_NUM = (PALETTE_NUM + NUM_PALETTES - 1) % NUM_PALETTES
            set_palette()
        elif (command == "brightness"):
            BRIGHTNESS = float(value) / 123.0
            set_brightness()
        elif (command == "timing"):
            SWITCH_TIME = 40.0 * (float(value) / 123.0)
        elif (command == "home"):
            PALETTE_NUM = 0
            set_palette()


def commands_from_controls(controls):
    midi_to_command = {}
    for (command,matchers) in controls.items():
        key = (matchers["first"], matchers["second"])
        if key in midi_to_command:
            print ("same midi for:" + midi_to_command[key] + " and " + command)
            continue
        midi_to_command[key] = command
        
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
    set_light_color(0, COLORS[0])
    set_light_color(1, COLORS[1])
    set_light_color(2, COLORS[2% num_colors])
    dmx.render()

def set_brightness():
    set_light_color(0, LIGHTS_VALUES[0])
    set_light_color(1, LIGHTS_VALUES[1])
    set_light_color(2, LIGHTS_VALUES[2])
    dmx.render()
    
if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
        sys.exit(-1)

    # midiin = rtmidi.MidiIn()
    # midiin.close_port()
    # midiin.open_port(1)

    dmx = DmxPy.DmxPy('/dev/ttyUSB0')
    dmx.blackout()

    palette_path = sys.argv[1]
    palette_f = open(palette_path, "r")
    controls_path = sys.argv[2]
    starting_palette = sys.argv[3].strip()
    controls_f = open(controls_path, "r")
    controls_lines = controls_f.read()
    controls = json.loads(controls_lines)
    commands = commands_from_controls(controls)
    
    palette_lines = palette_f.read()
    palettes = json.loads(palette_lines)
    NUM_PALETTES = len(palettes["palettes"])
    for p in range(0, len(palettes["palettes"])):
        if palettes["palettes"][p]["name"] == starting_palette:
            break
        
    PALETTE_NUM = p
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
            #handle_midi_command(midiin, commands)
        count += 1
    
