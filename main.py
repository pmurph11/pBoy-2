from cpu import Registers
from mem import load_rom, fetch_opcode, serial_output
from decode import decode, service_interrupts

TIMA_PERIODS = [1024, 16, 64, 256]

def main():

    debug = False   # Set for debugging
    
    reg = Registers()
    boot_rom_path = "roms/dmg_boot.bin"
    cartridge_path = "roms/gb-test-roms-master/cpu_instrs/individual/02-interrupts.gb" # Passes 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 and 11
    rom_data = load_rom(cartridge_path)
    boot_rom_data = load_rom(boot_rom_path)

    mem = bytearray(0x10000)  # 64KB of memory

    mem[0x0000:0x0000 + len(rom_data)] = rom_data
    # Store first 256 bytes of ROM and set aside for boot ROM
    first_256_bytes = mem[0x0000:0x0100]
    mem[0x0000:0x0100] = boot_rom_data
    count = 0
    running = True
    line_cycles = 0
    div_cycles = 0
    ly = 0
    boot_rom_active = True
    total_cycles = 0
    tima_cycles = 0
    
    while running:

        interrupt_cycles = service_interrupts(mem, reg)
        if reg.halted:                                                
            cycles = 4                                                
        else:         
            enable_ime = reg.ime_pending                                                
            addr = reg.pc                                             
            opcode = fetch_opcode(mem, reg)                           
            running, display_opcode, cycles = decode(mem, reg, opcode)
            if enable_ime and reg.ime_pending:
                reg.ime = True
                reg.ime_pending = False 
        cycles += interrupt_cycles
        total_cycles += cycles
        line_cycles += cycles

        if line_cycles >= 456:
            line_cycles -= 456
            ly += 1
            if ly > 153:
                ly = 0
            mem[0xFF44] = ly  # Update LY register
            if ly == 144:
                mem[0xFF0F] |= 0x01 

        div_cycles += cycles
        if div_cycles >= 256:
            div_cycles -= 256
            mem[0xFF04] = (mem[0xFF04] + 1) & 0xFF

        if mem[0xFF07] & 0x04:
            tima_cycles += cycles
            period = TIMA_PERIODS[mem[0xFF07] & 0x03]
            while tima_cycles >= period:
                tima_cycles -= period
                if mem[0xFF05] == 0xFF:
                    mem[0xFF05] = mem[0xFF06]
                    mem[0xFF0F] |= 0x04
                else:
                    mem[0xFF05] = (mem[0xFF05] + 1) & 0xFF

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
        if count >= 10000000:
            running = False

    print("SERIAL OUTPUT:", "".join(serial_output))
    print(f"Stopped after {count} instructions at PC {reg.pc:04X}")
    print(f"Total cycles executed: {total_cycles}")
    print(f"Registers: {reg}")



if __name__ == "__main__":
    main()