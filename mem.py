def load_rom(path):
    with open(path, 'rb') as f:
        data = f.read()
    return data

debug = False  # Set to True to enable debug output
def fetch_byte(mem, reg):
    byte = mem[reg.pc]
    if debug:
        print(f"    fetch_byte @ {reg.pc:04X} -> {byte:02X}")
    reg.pc += 1
    return byte

def fetch_opcode(mem, reg):
    return fetch_byte(mem, reg)

def dump_memory(mem, start=0, length=16):
    chunk = mem[start:start + length]
    hex_bytes = ' '.join(f'{byte:02X}' for byte in chunk)
    print(f"{start:04X}: {hex_bytes}")
