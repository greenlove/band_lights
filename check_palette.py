from dmxpy import DmxPy
import time
import sys
import json

SWITCH_TIME = 10
BRIGHTNESS = 0.7


def get_hex(r, g, b):
    return "{0:0{1}x}".format(r, 2) + "{0:0{1}x}".format(g, 2) + "{0:0{1}x}".format(b, 2)

def get_rgb(color):
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:], 16)

    return (r, g, b)

def set_light_color(light_number, color):
    (r, g, b) = get_rgb(color)
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
    print ("palette.json number")
        
if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)

    palette_path = sys.argv[1]
    palette = open(palette_path, "r")
    palette_num = int(sys.argv[2])
    lines = palette.read()
    obj = json.loads(lines)
    
    palette = obj["palettes"][palette_num]
    print ("cycling: " + palette["name"])
    colors = [obj["colors"][x] for x in palette["colors"]]

    dmx = DmxPy.DmxPy('/dev/ttyUSB0')
    dmx.blackout()

    count = 0
    num_colors = len(colors)
    while True:
        fade_colors(colors[count % num_colors], colors[(count + 1)% num_colors],
                    colors[(count + 1)% num_colors], colors[(count + 2)% num_colors],
                    colors[(count + 2)% num_colors], colors[(count + 3)% num_colors])
        time.sleep(SWITCH_TIME)
        count += 1
    
