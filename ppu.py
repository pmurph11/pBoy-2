from PIL import Image

SHADE_TO_GREY = [255, 170, 85, 0]



def frame_to_image(frame):
    img = Image.new('L', (160, 144))                              # job 1, moved here

    for y in range(144):
        for x in range(160):
            img.putpixel((x, y), SHADE_TO_GREY[frame[y][x]])

    return img                                                    # NEW: hand the image back

def save_png(frame, filename):
    img = frame_to_image(frame)                                   # NEW: get the image from above
    img.save(filename)                                            # job 2, unchanged

def save_gif(images, filename):
    images[0].save(filename, save_all=True, append_images=images[1:], duration=20, loop=0) 

def tile_pixel(mem, tile_addr, row, col):
    low_byte = mem[tile_addr + row * 2]
    high_byte = mem[tile_addr + row * 2 + 1]
    bit = 7 - col
    low = (low_byte >> bit) & 1
    high =(high_byte >> bit) & 1
    return (high << 1) | low

def bg_pixel(mem, x, y):
    SCX = mem[0xFF43]
    SCY = mem[0xFF42]

    bx = (x + SCX) & 0xFF
    by = (y + SCY) & 0xFF

    map_col = bx // 8
    map_row = by // 8
    tile_col = bx % 8
    tile_row = by % 8

    map_base = 0x9800 
    if mem[0xFF40] & 0x08:
        map_base = 0x9C00

    map_addr = map_base + map_row * 32 + map_col
    tile_num = mem[map_addr]

    if mem[0xFF40] & 0x10:
        tile_addr = 0x8000 + tile_num * 16
    else:
        if tile_num >= 0x80:
            tile_num -= 0x100
        tile_addr = 0x9000 + tile_num * 16

    return tile_pixel(mem, tile_addr, tile_row, tile_col)

# Print BG rectangle helper
def print_bg_area(mem, left, top, width, height):
    for y in range(top, top + height):
        for x in range(left, left +width):
            if bg_pixel(mem, x, y) != 0:
                print("#", end="")
            else:
                print(".", end="")
        print()

# Print tile helper
def print_tile(mem, tile_addr):
    for row in range(8):
        for col in range(8):
            if tile_pixel(mem, tile_addr, row, col) != 0:
                print("#", end="")
            else:
                print(".", end="")
        print()

def render_background(mem):
    bgp = mem[0xFF47]

    grid = []
    for y in range(144):
        row = []
        for x in range(160):
            value = bg_pixel(mem, x, y)
            row.append((bgp >>(value * 2)) & 0b11)
        grid.append(row)

    return grid
