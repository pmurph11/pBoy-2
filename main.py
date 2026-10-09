from cpu import Registers
from mem import load_rom, fetch_opcode, serial_output
from decode import decode


def main():

    debug = False   # Set for debugging

    reg = Registers()
    boot_rom_path = "roms/dmg_boot.bin"
    cartridge_path = "roms/gb-test-roms-master/cpu_instrs/individual/02-interrupts.gb" # Passes 01, 03, 04, 05, 06, 07, 08, 

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
    boot_rom_active = True

    
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
        if boot_rom_active and mem[0xFF50] != 0x00:
            print("Boot ROM handover complete. Restoring first 256 bytes of cartridge ROM.")
            mem[0x0000:0x0100] = first_256_bytes  
            boot_rom_active = False
        prefix = "CB " if opcode == 0xCB else ""

        # Show debug if count between x-x value
        # if count > 2525000:
        #     debug = True
        #     print(count)
        if debug:
            print(f"PC: {addr:04X}, Opcode: {prefix}{display_opcode:02X}, Registers: {reg}")
        count += 1
        if count > 15000000:
            running = False

    print("SERIAL OUTPUT:", "".join(serial_output))
    print(f"Stopped after {count} instructions at PC {reg.pc:04X}")
    print(f"Registers: {reg}")



if __name__ == "__main__":
    main()
