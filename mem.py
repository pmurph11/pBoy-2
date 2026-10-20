def load_rom(path):
    with open(path, 'rb') as f:
        data = f.read()
    return data

serial_output = []
debug = False  

def fetch_byte(mem, reg):
    byte = mem[reg.pc]
    if debug:
        print(f"    fetch_byte @ {reg.pc:04X} -> {byte:02X}")
    reg.pc += 1
    return byte

def write_byte(mem, addr, val):
    mem[addr] = val

    if addr == 0xFF02 and (val & 0x80):
        serial_output.append(chr(mem[0xFF01]))
        mem[0xFF02] = val & 0x7F   # clear bit 7 = transfer finished

    if addr == 0xFF04:
        mem[0xFF04] = 0
    if debug:
        print(f"    write_byte @ {addr:04X} <- {val:02X}")

def fetch_opcode(mem, reg):
    return fetch_byte(mem, reg)

def dump_memory(mem, start=0, length=16):
    chunk = mem[start:start + length]
    hex_bytes = ' '.join(f'{byte:02X}' for byte in chunk)
    print(f"{start:04X}: {hex_bytes}")
