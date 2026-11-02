from mem import Registers

reg = Registers()

def tile_pixel(mem, tile_addr, row, col):
    low_byte = mem[reg.pc]
    high_byte = mem[reg.pc]
    bit = 7 - col
    low = (low_byte >> bit) & 1
    high =(high_byte >> bit) & 1
    return (high << 1) | low