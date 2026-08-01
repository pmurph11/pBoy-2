from cpu import Registers


def main():
    reg = Registers()
    path = "roms/dmg_boot.bin"

    # Helpers
    def ld_sp_d16(mem, reg):
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        reg.sp = (high << 8) | low
        # Flags: Z=0, N=0, H=0, C=0

    def ld_r16_d16(mem, reg, high_name, low_name):
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        setattr(reg, high_name, high)
        setattr(reg, low_name, low)

    def ld_hl_dec_a(mem, reg):
        hl = (reg.h << 8) | reg.l
        mem[hl] = reg.a
        hl = (hl - 1) & 0xFFFF  # Decrement HL and wrap around at 16 bits
        reg.h = (hl >> 8) & 0xFF
        reg.l = hl & 0xFF

    def xor_a(reg):
        reg.a ^= reg.a
        reg.f = 0x80  # Set Z flag, clear N, H, C flags

    # CB instruction handlers
    def bit_7_h(reg):
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20

        # Clear N flag
        reg.f &= ~n_mask

        # Set H flag
        reg.f |= h_mask

        # Check Z bit
        if reg.h & z_mask:
            reg.f &= ~z_mask
        else:
            reg.f |= z_mask 



    def load_rom(path):
        with open(path, 'rb') as f:
            data = f.read()
        return data

    def dump_memory(mem, start=0, length=16):
        chunk = mem[start:start + length]
        hex_bytes = ' '.join(f'{byte:02X}' for byte in chunk)
        print(f"{start:04X}: {hex_bytes}")    

    def fetch_byte(mem, reg):
        byte = mem[reg.pc]
        reg.pc += 1
        return byte

    def decode_cb(mem, reg):
        cb_opcode = fetch_byte(mem, reg)
        print(f"CB Opcode: {cb_opcode:02X}")

        match cb_opcode:
            case 0x7C:
                # BIT 7, H
                bit_7_h(reg)

    def fetch_opcode(mem, reg):
        return fetch_byte(mem, reg)

    def decode(mem, reg, opcode):
        # IGNORE OP TABLE FOR NOW
        # op_table = {
        # # MISC instructions
        #     0x00: "NOP",

        # # LD instructions
        #     0x31: "LD SP, d16",
        # }
        
        match opcode:
            case 0xCB:
                decode_cb(mem, reg)
            case 0x31:
                ld_sp_d16(mem, reg)
            case 0xAF:
                xor_a(reg)
            case 0x21:
                ld_r16_d16(mem, reg, 'h', 'l')
            case 0x32:
                ld_hl_dec_a(mem, reg)
            case _:
                print(f"Unknown opcode: {opcode:02X}")

    rom_data = load_rom(path)

    mem = bytearray(0x10000)  # 64KB of memory

    mem[0x0000:0x0000 + len(rom_data)] = rom_data

    count = 0
    running = True

    while running:
        addr = reg.pc
        opcode = fetch_opcode(mem, reg)
        decode(mem, reg, opcode)
        print(f"PC: {addr:04X}, Opcode: {opcode:02X}, Registers: {reg}")
        count += 1
        if count >= 10:
            running = False
            
    dump_memory(mem, start=0x0000)
    dump_memory(mem, start=0x0100)
    dump_memory(mem, start=0x9FF0, length=16)
    
if __name__ == "__main__":
    main()
