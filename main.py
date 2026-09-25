from cpu import Registers
from mem import load_rom, fetch_opcode
from decode import decode


def main():

    debug = False   # Set for debugging

    reg = Registers()
    boot_rom_path = "roms/dmg_boot.bin"
    cartridge_path = "roms/Tetris.gb"

    rom_data = load_rom(cartridge_path)
    boot_rom_data = load_rom(boot_rom_path)

    mem = bytearray(0x10000)  # 64KB of memory

    mem[0x0000:0x0000 + len(rom_data)] = rom_data
    # Store first 256 bytes of ROM and set aside for boot ROM
    first_256_bytes = mem[0x0000:0x0100]
    mem[0x0000:0x0100] = boot_rom_data
    count = 0
    running = True
    instruction_count = 0
    ly = 0

    while running:
        # Fake scanline counter for LY register, incrementing every 10 instructions
        instruction_count += 1
        if instruction_count >= 10:
            instruction_count = 0
            ly += 1
            if ly > 153:
                ly = 0
            mem[0xFF44] = ly  # Update LY register

        addr = reg.pc
        opcode = fetch_opcode(mem, reg)
        running, display_opcode = decode(mem, reg, opcode)
        prefix = "CB " if opcode == 0xCB else ""

        # Show debug if count between x-x value
        if count > 2525000:
            debug = True
            print(count)
        if debug:
            print(f"PC: {addr:04X}, Opcode: {prefix}{display_opcode:02X}, Registers: {reg}")
        count += 1
        if count > 2600000:
            running = False

    print(f"Stopped after {count} instructions at PC {reg.pc:04X}")
    print(f"Registers: {reg}")



if __name__ == "__main__":
    main()
