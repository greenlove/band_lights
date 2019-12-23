import sys
import colorsys
import json
import re

def get_hex(r, g, b):
    return "{0:0{1}x}".format(r, 2) + "{0:0{1}x}".format(g, 2) + "{0:0{1}x}".format(b, 2)

def get_rgb(color):
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:], 16)

    return (r, g, b)

def color_shift(color, hue_shift):
    (r, g, b) = get_rgb(color)
    (h, l, s) = colorsys.rgb_to_hls(r / 255.0, g/ 255.0, b / 255.0)
    (r_new, g_new, b_new) = colorsys.hls_to_rgb(h + hue_shift, l, s)
    return get_hex(int(r_new * 255), int(g_new * 255), int(b_new * 255))

def color_next(color1, color2):
    (r1, g1, b1) = get_rgb(color1)
    (r2, g2, b2) = get_rgb(color2)
    (h1, l1, s1) = colorsys.rgb_to_hls(r1 / 255.0, g1/ 255.0, b1 / 255.0)
    (h2, l2, s2) = colorsys.rgb_to_hls(r2 / 255.0, g2/ 255.0, b2 / 255.0)
    h3 = h2 + (h2 - h1) # shift h3 same distance ahead that h2 was
    (r_new, g_new, b_new) = colorsys.hls_to_rgb(h3, l1, s1)
    
    return get_hex(int(r_new * 255), int(g_new * 255), int(b_new * 255))


def color_mid(color1, color2):
    (r1, g1, b1) = get_rgb(color1)
    (r2, g2, b2) = get_rgb(color2)
    (h1, l1, s1) = colorsys.rgb_to_hls(r1 / 255.0, g1/ 255.0, b1 / 255.0)
    (h2, l2, s2) = colorsys.rgb_to_hls(r2 / 255.0, g2/ 255.0, b2 / 255.0)
    h3 = (h1 + h2) / 2.0 # h3 average of h1 and h2
    (r_new, g_new, b_new) = colorsys.hls_to_rgb(h3, l1, s1)
    
    return get_hex(int(r_new * 255), int(g_new * 255), int(b_new * 255))


def resolve_color(color_str, palettes):
    if color_str in palettes["colors"]:
        return palettes["colors"][color_str]

    shift_pattern = "color_shift\(([a-z0-9]*),\s?(-?[0-9]*.[0-9]*)\)"
    shift_match = re.match(shift_pattern, color_str)
    if shift_match:
        color = resolve_color(shift_match.group(1), palettes)
        shift = float(shift_match.group(2))
        return color_shift(color, shift)

    next_pattern = "color_next\(([a-z0-9]*),\s?([a-z0-9]*)\)"
    next_match = re.match(next_pattern, color_str)
    if next_match:
        color1 = resolve_color(next_match.group(1), palettes)
        color2 = resolve_color(next_match.group(2), palettes)
        return color_next(color1, color2)

    mid_pattern = "color_mid\(([a-z0-9]*),\s?([a-z0-9]*)\)"
    mid_match = re.match(mid_pattern, color_str)
    if mid_match:
        color1 = resolve_color(mid_match.group(1), palettes)
        color2 = resolve_color(mid_match.group(2), palettes)
        return color_mid(color1, color2)

    return color_str


def usage():
    print ("palette.json color_string")
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        sys.exit(-1)

    palettes_path = sys.argv[1]
    color_string = sys.argv[2]
    
    palettes_f = open(palettes_path, "r")
    palettes = json.loads(palettes_f.read())

    print(resolve_color(color_string, palettes))

