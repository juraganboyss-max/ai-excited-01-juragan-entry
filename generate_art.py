import zlib
import struct
import math
import random

WIDTH = 640
HEIGHT = 640

# Deterministic random generator
rng = random.Random(20261116)

# Generate lightning path
def generate_lightning(x0, y0, x1, y1, segments=8, displacement=25):
    pts = [(x0, y0)]
    for i in range(1, segments):
        t = i / segments
        bx = x0 + t * (x1 - x0)
        by = y0 + t * (y1 - y0)
        dx = (rng.random() - 0.5) * displacement * (1 - abs(t - 0.5))
        dy = (rng.random() - 0.5) * displacement * (1 - abs(t - 0.5))
        pts.append((bx + dx, by + dy))
    pts.append((x1, y1))
    return pts

lightning_branches = []
# Create 8 lightning bolts radiating from center
cx, cy = 320, 320
for i in range(8):
    angle = (i / 8.0) * 2 * math.pi + 0.2
    dist = 280 + rng.random() * 40
    tx = cx + math.cos(angle) * dist
    ty = cy + math.sin(angle) * dist
    lightning_branches.append(generate_lightning(cx, cy, tx, ty, segments=10, displacement=35))

# Generate particle sparks
sparks = []
for _ in range(180):
    angle = rng.random() * 2 * math.pi
    dist = rng.random() * 300
    sx = cx + math.cos(angle) * dist
    sy = cy + math.sin(angle) * dist
    sz = rng.random() * 3 + 1
    color = rng.choice([
        (255, 240, 150), # Gold
        (0, 245, 255),   # Cyan
        (255, 0, 128),   # Pink
        (255, 255, 255)  # White
    ])
    sparks.append((sx, sy, sz, color))

# Simple 8x12 pixel font bitmap for "WOAH JUDGE! MAXIMUM EXCITEMENT!"
FONT = {
    'A': [" 0 ", "1 1", "111", "1 1", "1 1"],
    'B': ["11 ", "1 1", "11 ", "1 1", "11 "],
    'C': [" 11", "1  ", "1  ", "1  ", " 11"],
    'D': ["11 ", "1 1", "1 1", "1 1", "11 "],
    'E': ["111", "1  ", "11 ", "1  ", "111"],
    'F': ["111", "1  ", "11 ", "1  ", "1  "],
    'G': [" 11", "1  ", "1 1", "1 1", " 11"],
    'H': ["1 1", "1 1", "111", "1 1", "1 1"],
    'I': ["111", " 1 ", " 1 ", " 1 ", "111"],
    'J': ["  1", "  1", "  1", "1 1", " 1 "],
    'K': ["1 1", "11 ", "11 ", "1 1", "1 1"],
    'L': ["1  ", "1  ", "1  ", "1  ", "111"],
    'M': ["1 1", "111", "111", "1 1", "1 1"],
    'N': ["1 1", "111", "111", "1 1", "1 1"],
    'O': [" 1 ", "1 1", "1 1", "1 1", " 1 "],
    'P': ["11 ", "1 1", "11 ", "1  ", "1  "],
    'Q': [" 1 ", "1 1", "1 1", "111", " 11"],
    'R': ["11 ", "1 1", "11 ", "1 1", "1 1"],
    'S': [" 11", "1  ", " 1 ", "  1", "11 "],
    'T': ["111", " 1 ", " 1 ", " 1 ", " 1 "],
    'U': ["1 1", "1 1", "1 1", "1 1", " 11"],
    'V': ["1 1", "1 1", "1 1", "1 1", " 1 "],
    'W': ["1 1", "1 1", "111", "111", "1 1"],
    'X': ["1 1", "1 1", " 1 ", "1 1", "1 1"],
    'Y': ["1 1", "1 1", " 1 ", " 1 ", " 1 "],
    'Z': ["111", "  1", " 1 ", "1  ", "111"],
    '!': [" 1 ", " 1 ", " 1 ", "   ", " 1 "],
    ' ': ["   ", "   ", "   ", "   ", "   "],
}

def draw_text(text, start_x, start_y, scale, color, buffer):
    cur_x = start_x
    for ch in text:
        bitmap = FONT.get(ch, FONT[' '])
        for row_i, row in enumerate(bitmap):
            for col_i, bit in enumerate(row):
                if bit == '1':
                    for px in range(scale):
                        for py in range(scale):
                            x = cur_x + col_i * scale + px
                            y = start_y + row_i * scale + py
                            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                                idx = (y * WIDTH + x) * 4
                                buffer[idx:idx+4] = color
        cur_x += (len(bitmap[0]) + 1) * scale

def dist_segment(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return math.hypot(px - x0, py - y0)
    t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    nx = x0 + t * dx
    ny = y0 + t * dy
    return math.hypot(px - nx, py - ny)

# Build image pixels
pixel_buf = bytearray(WIDTH * HEIGHT * 4)

for y in range(HEIGHT):
    for x in range(WIDTH):
        idx = (y * WIDTH + x) * 4
        
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx)
        
        # Base gradient: Deep space purple to midnight blue
        t_dist = min(1.0, dist / 450.0)
        r = int(12 * (1 - t_dist) + 5 * t_dist)
        g = int(5 * (1 - t_dist) + 2 * t_dist)
        b = int(35 * (1 - t_dist) + 15 * t_dist)
        
        # Radial dynamic rays (32 rays)
        ray_val = math.sin(angle * 16 + dist * 0.02)
        if ray_val > 0.4:
            ray_intensity = ((ray_val - 0.4) / 0.6) ** 2 * max(0, 1 - dist / 380)
            # Alternating ray colors
            ray_mod = int((angle + math.pi) / (2 * math.pi) * 8) % 3
            if ray_mod == 0:
                r += int(ray_intensity * 220) # Cyan
                g += int(ray_intensity * 240)
                b += int(ray_intensity * 255)
            elif ray_mod == 1:
                r += int(ray_intensity * 255) # Pink
                g += int(ray_intensity * 30)
                b += int(ray_intensity * 160)
            else:
                r += int(ray_intensity * 255) # Gold
                g += int(ray_intensity * 200)
                b += int(ray_intensity * 40)
                
        # Shockwave rings (slanted ellipse)
        ellipse_dist = math.hypot(dx * 1.0, dy * 1.3 - dx * 0.3)
        for ring_r in [100, 180, 260, 320]:
            ring_diff = abs(ellipse_dist - ring_r)
            if ring_diff < 12:
                ring_intensity = (1 - ring_diff / 12) * max(0, 1 - ellipse_dist / 400)
                r += int(ring_intensity * 180)
                g += int(ring_intensity * 220)
                b += int(ring_intensity * 255)
                
        # Central Star / Crest (8-pointed star)
        star_a = math.cos(angle * 8)
        star_r = 80 + 35 * star_a
        if dist < star_r:
            star_int = (1 - dist / star_r) ** 1.5
            r += int(star_int * 255)
            g += int(star_int * 230)
            b += int(star_int * 150)
            
        # Inner Core Blazing Glow
        if dist < 35:
            core_int = (1 - dist / 35) ** 0.8
            r += int(core_int * 255)
            g += int(core_int * 255)
            b += int(core_int * 255)
            
        # Clamp RGB
        r = min(255, max(0, r))
        g = min(255, max(0, g))
        b = min(255, max(0, b))
        
        pixel_buf[idx:idx+4] = bytes([r, g, b, 255])

# Draw lightning and sparks as localized overlays
def blend_pixel(x, y, color, intensity=1.0):
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return
    idx = (y * WIDTH + x) * 4
    for c in range(3):
        pixel_buf[idx+c] = min(255, pixel_buf[idx+c] + int(color[c] * intensity))

for branch in lightning_branches:
    for x0, y0 in branch:
        for ox in range(-6, 7):
            for oy in range(-6, 7):
                d2 = ox*ox + oy*oy
                if d2 <= 36:
                    blend_pixel(int(x0)+ox, int(y0)+oy, (100, 180, 255), (1-d2/49)**2)

for sx, sy, sz, scolor in sparks:
    radius = int(sz) + 1
    for ox in range(-radius, radius+1):
        for oy in range(-radius, radius+1):
            d = math.hypot(ox, oy)
            if d <= radius:
                blend_pixel(int(sx)+ox, int(sy)+oy, scolor, 1-d/(radius+1))

# Draw Text Banners
# Top Banner for "WOAH JUDGE!"
draw_text("WOAH JUDGE!", 150, 40, 5, bytes([255, 235, 0, 255]), pixel_buf)
# Bottom Banner for "MAXIMUM EXCITEMENT!"
draw_text("MAXIMUM EXCITEMENT!", 40, 570, 4, bytes([0, 245, 255, 255]), pixel_buf)

def create_png(width, height, get_pixel):
    import struct
    import zlib

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(get_pixel(x, y))

    header = struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))

# Save PNG
png_bytes = create_png(WIDTH, HEIGHT, lambda px, py: pixel_buf[(py * WIDTH + px) * 4 : (py * WIDTH + px) * 4 + 4])

with open("/output/entry.png", "wb") as f:
    f.write(png_bytes)

print(f"entry.png created: {len(png_bytes)} bytes, dimensions {WIDTH}x{HEIGHT}")
