from cpu import Registers


def main():
    reg = Registers()
    boot_rom_path = "roms/dmg_boot.bin"

    # LD r8 to R8 mapper
    r8_order = ['b', 'c', 'd', 'e', 'h', 'l', None, 'a']  # None represents (HL) which is not handled here

    ld_r8_r8_table = {}
    for dst_index, dst_name in enumerate(r8_order):
        for src_index, src_name in enumerate(r8_order):
            if dst_name is None or src_name is None:
                continue  # Skip (HL) cases and skip 0x76 (HAL) naturally
            opcode = 0x40 + (dst_index << 3) + src_index
            ld_r8_r8_table[opcode] = (dst_name, src_name)

    ## Helpers
    # --- 8-bit Load instructions ---
    def ld_r8_d8(mem, reg, reg_name):
        r8 = fetch_byte(mem, reg)
        setattr(reg, reg_name, r8)

    def ld_a_r16(mem, reg, high_name, low_name):
        high = getattr(reg, high_name)
        low = getattr(reg, low_name)
        addr = (high << 8) | low
        reg.a = mem[addr]

    def ld_hl_step_a(mem, reg, step):
        hl = (reg.h << 8) | reg.l
        mem[hl] = reg.a
        hl = (hl + step) & 0xFFFF  # Increment/Decrement HL and wrap around at 16 bits
        reg.h = (hl >> 8) & 0xFF
        reg.l = hl & 0xFF

    def ld_r8_r8(reg, dest_name, src_name):
        setattr(reg, dest_name, getattr(reg, src_name))

    def ld_hl_a(mem, reg):
        hl = (reg.h << 8) | reg.l
        mem[hl] = reg.a

    def ld_a_a8(mem, reg):
        a8 = fetch_byte(mem, reg)
        reg.a = mem[0xFF00 + a8]

    def ldh_a8_a(mem, reg):
        a8 = fetch_byte(mem, reg)
        mem[0xFF00 + a8] = reg.a

    def ld_c_a(mem, reg):
        base = 0xFF00
        val = reg.c
        mem[base + val] = reg.a

    # --- 16-bit Load instructions ---

    def ld_a16_a(mem, reg):
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        addr = high << 8 | low
        mem[addr] = reg.a

    def ld_r16_d16(mem, reg, high_name, low_name):
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        setattr(reg, high_name, high)
        setattr(reg, low_name, low)

    def ld_sp_d16(mem, reg):
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        reg.sp = (high << 8) | low
        # Flags: Z=0, N=0, H=0, C=0

    # --- 8-bit Arithmetic/Logic instructions ---
    def dec8(reg, reg_name):
        val = getattr(reg, reg_name)
        low = val & 0x0F
        half_borrow = (low == 0x00)
        dec_val = (val - 1) & 0xFF
        setattr(reg, reg_name, dec_val)

        # Set flags
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20

        # CLEAR THE FLAGS
        reg.f &= ~(z_mask | n_mask | h_mask)

        if dec_val == 0:
            reg.f |= z_mask
        if half_borrow:
            reg.f |= h_mask
        reg.f |= n_mask  # Set N flag for decrement operation

    def cp_a_hl(mem, reg):
        hl = (reg.h << 8) | reg.l
        val = mem[hl]
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20
        c_mask = 0x10
        low_a = reg.a & 0x0F
        low_val = val & 0x0F

        reg.f &= ~(z_mask | n_mask | h_mask | c_mask)        
        if reg.b == reg.a:
            reg.f |= 0x80  # Set Z flag if result is zero
        else:
            reg.f &= ~0x80  # Clear Z flag if result is not zero
        if low_a < low_val:
            reg.f |= h_mask  # Set H flag for half borrow
        # If B > A set C
        if val > reg.a:
            reg.f |= c_mask
        reg.f |= 0x40  # Set N flag for subtraction

    def cp_d8(mem, reg):
        val = fetch_byte(mem, reg)
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20
        c_mask = 0x10

        reg.f &= ~(z_mask | n_mask | h_mask | c_mask)

        if reg.a == val:
            reg.f |= z_mask

        # SET N REGARDLESS
        reg.f |= n_mask

        # Half and full borrow

        low_a = reg.a & 0x0F
        low_val = val & 0x0F
        half_borrow = low_a < low_val

        if half_borrow : 
            reg.f |= h_mask

        full_borrow = reg.a < val
        if full_borrow:
            reg.f |= c_mask

    def sub_a_b(reg):
        # subtract b from a
        val = reg.b
        reg.a = (reg.a - val) & 0xFF

        # get both nibbles
        low_a = reg.a & 0x0F
        low_val = val & 0x0F
        # Flags
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20
        c_mask = 0x10

        reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
        if reg.b == reg.a:
            reg.f |= 0x80  # Set Z flag if result is zero
        else:
            reg.f &= ~0x80  # Clear Z flag if result is not zero
        if low_a < low_val:
            reg.f |= h_mask  # Set H flag for half borrow
        # If B > A set C
        if val > reg.a:
            reg.f |= c_mask
        reg.f |= 0x40  # Set N flag for subtraction

    


    def inc8(reg, reg_name):
        val = getattr(reg, reg_name)
        low = val & 0x0F
        half_carry = (low == 0x0F)
        inc_val = (val + 1) & 0xFF 
        setattr(reg, reg_name, inc_val)

        # Set flags
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20

        reg.f &= ~(z_mask | n_mask | h_mask)  # clear only Z, N, H — leave C alone
        if inc_val == 0:
            reg.f |= z_mask
        if half_carry:
            reg.f |= h_mask

    def xor_a(reg):
        reg.a ^= reg.a
        reg.f = 0x80  # Set Z flag, clear N, H, C flags

   # --- 16-bit Arithmetic/Logic instructions ---
    def step_r16(reg, high_name, low_name, step):
        high = getattr(reg, high_name)
        low = getattr(reg, low_name)
        val = (high << 8) | low
        val = (val + step) & 0xFFFF  # Increment/Decrement
        high = (val >> 8) & 0xFF
        low = val & 0xFF
        setattr(reg, high_name, (high))
        setattr(reg, low_name, (low))

    # --- Rotate/Shift instructions ---
    def rla(reg):
        carry = (reg.f & 0x10) >> 4  # Get the current carry flag (C)
        new_carry = (reg.a & 0x80) >> 7
        reg.a = ((reg.a << 1) | carry) & 0xFF  # Shift left and add old carry
        # Clear Z, N, H flags, set C flag
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20
        reg.f &= ~(z_mask | n_mask | h_mask)  # Clear Z, N, H flags
        if new_carry:
            reg.f |= 0x10  # Set C flag if new carry is 1

    # --- 8-bit Jump/Call instructions ---
    def jr_nz_r8(mem, reg):
        r8 = fetch_byte(mem, reg)
        if r8 >= 0x80:
            r8 -= 0x100  # Convert to signed
        if reg.f & 0x80 == 0:
            reg.pc = (reg.pc + r8) & 0xFFFF  # Jump to new address, wrap around at 16 bits

    def jr_r8(mem, reg):
        r8 = fetch_byte(mem, reg)
        if r8 >= 0x80:
            r8 -= 0x100  # Convert to signed
        reg.pc = (reg.pc + r8) & 0xFFFF

    def jr_z_r8(mem, reg):
        r8 = fetch_byte(mem, reg)
        if r8 >= 0x80:
            r8 -= 0x100  # Convert to signed
        if reg.f & 0x80 == 0x80:
            reg.pc = (reg.pc + r8) & 0xFFFF  # Jump to new address, wrap around at 16 bits

    def call_a16(mem, reg):
        # Fetch the 16-bit address
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        addr = (high << 8) | low

        # Push the current PC onto the stack
        ret_addr = reg.pc
        high_byte = (ret_addr >> 8) & 0xFF
        low_byte = ret_addr & 0xFF

        reg.sp = (reg.sp - 1) & 0xFFFF
        mem[reg.sp] = high_byte
        reg.sp = (reg.sp - 1) & 0xFFFF
        mem[reg.sp] = low_byte

        # Jump to the address
        reg.pc = addr

    # --- Stack instructions ---
    def pop_r16(mem, reg, high_name, low_name):
        low = mem[reg.sp]
        reg.sp = (reg.sp + 1) & 0xFFFF
        high = mem[reg.sp]
        reg.sp = (reg.sp + 1) & 0xFFFF
        setattr(reg, high_name, high)
        setattr(reg, low_name, low)

    def push_r16(mem, reg, high_name, low_name):
        low = getattr(reg, low_name)
        high = getattr(reg, high_name)

        reg.sp = (reg.sp - 1) & 0xFFFF
        mem[reg.sp] = high

        reg.sp = (reg.sp - 1) & 0xFFFF
        mem[reg.sp] = low

    def ret(mem, reg):
        low = mem[reg.sp]
        reg.sp = (reg.sp + 1) & 0xFFFF
        high = mem[reg.sp]
        reg.sp = (reg.sp + 1) & 0xFFFF
        addr = (high << 8 ) | low
        reg.pc = addr

    # --- CB-prefixed instruction handlers ---
    def rl_r8(reg, reg_name):
        carry = (reg.f & 0x10) >> 4  # Get the current carry flag (C) 0101 0000
        val = getattr(reg, reg_name)
        new_carry = (val & 0x80) >> 7
        val = ((val << 1) | carry) & 0xFF
        setattr(reg, reg_name, val)
        # Clear Z, N, H flags, set C flag
        z_mask = 0x80
        n_mask = 0x40
        h_mask = 0x20
        reg.f &= ~(z_mask | n_mask | h_mask)  # Clear Z, N, H flags
        if val == 0:
            reg.f |= z_mask  # Set Z flag if result is zero
        if new_carry:
            reg.f |= 0x10  # Set C flag if new carry is 1

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

    def decode_cb(mem, reg):
        cb_opcode = fetch_byte(mem, reg)

        match cb_opcode:
            case 0x7C:
                # BIT 7, H
                bit_7_h(reg)
                return True, cb_opcode
            case 0x11:
                rl_r8(reg, 'c')
                return True, cb_opcode
            case _:
                print(f"Unknown opcode: {cb_opcode:02X}")
                return False, cb_opcode

    # --- Utility functions ---
    def fetch_byte(mem, reg):
        byte = mem[reg.pc]
        print(f"    fetch_byte @ {reg.pc:04X} -> {byte:02X}")
        reg.pc += 1
        return byte

    def fetch_opcode(mem, reg):
        return fetch_byte(mem, reg)

    def load_rom(path):
        with open(path, 'rb') as f:
            data = f.read()
        return data

    def dump_memory(mem, start=0, length=16):
        chunk = mem[start:start + length]
        hex_bytes = ' '.join(f'{byte:02X}' for byte in chunk)
        print(f"{start:04X}: {hex_bytes}")

    def decode(mem, reg, opcode):
        
        if opcode in ld_r8_r8_table:
            dst, src = ld_r8_r8_table[opcode]
            ld_r8_r8(reg, dst, src)
            return True, opcode

        match opcode:
            case 0x04:
                inc8(reg, 'b')
            case 0x05:
                dec8(reg, 'b')
            case 0x06:
                ld_r8_d8(mem, reg, 'b')
            case 0x0C:
                inc8(reg, 'c')
            case 0x0D:
                dec8(reg, 'c')
            case 0x0E:
                ld_r8_d8(mem, reg, 'c')
            case 0x11:
                ld_r16_d16(mem, reg, 'd', 'e')
            case 0x13:
                step_r16(reg, 'd', 'e', 1)
            case 0x15:
                dec8(reg, 'd')
            case 0x16:
                ld_r8_d8(mem, reg, 'd')
            case 0x17:
                rla(reg)
            case 0x18:
                jr_r8(mem, reg)
            case 0x1A:
                ld_a_r16(mem, reg, 'd', 'e')
            case 0x1D:
                dec8(reg, 'e')
            case 0x1E:
                ld_r8_d8(mem, reg, 'e')
            case 0x20:
                jr_nz_r8(mem, reg)
            case 0x21:
                ld_r16_d16(mem, reg, 'h', 'l')
            case 0x22:
                ld_hl_step_a(mem, reg, 1)
            case 0x23:
                step_r16(reg, 'h', 'l', 1)
            case 0x24:
                inc8(reg, 'h')
            case 0x28:
                jr_z_r8(mem, reg)
            case 0x2E:
                ld_r8_d8(mem, reg, 'l')
            case 0x3D:
                dec8(reg, 'a')
            case 0x31:
                ld_sp_d16(mem, reg)
            case 0x32:
                ld_hl_step_a(mem, reg, -1)
            case 0x3E:
                ld_r8_d8(mem, reg, 'a')
            case 0x90:
                sub_a_b(reg)
            case 0x77:
                ld_hl_a(mem, reg)
            case 0xAF:
                xor_a(reg)
            case 0xBE:
                cp_a_hl(mem, reg)
            case 0xC1:
                pop_r16(mem, reg, 'b', 'c')
            case 0xC5:
                push_r16(mem, reg, 'b', 'c')
            case 0xC9:
                ret(mem, reg)
            case 0xCB:
                return decode_cb(mem, reg)
            case 0xCD:
                call_a16(mem, reg)
            case 0xE0:
                ldh_a8_a(mem, reg)
            case 0xE2:
                ld_c_a(mem, reg)
            case 0xEA:
                ld_a16_a(mem, reg)
            case 0xF0:
                ld_a_a8(mem, reg)
            case 0xFE:
                cp_d8(mem, reg)
            case _:
                print(f"Unknown opcode: {opcode:02X}")
                return False, opcode
        return True, opcode

    boot_rom_data = load_rom(boot_rom_path)

    mem = bytearray(0x10000)  # 64KB of memory

    mem[0x0000:0x0000 + len(boot_rom_data)] = boot_rom_data
    mem[0xFF44] = 0x90
    count = 0
    running = True

    while running:
        addr = reg.pc
        opcode = fetch_opcode(mem, reg)
        running, display_opcode = decode(mem, reg, opcode)
        prefix = "CB " if opcode == 0xCB else ""
        print(f"PC: {addr:04X}, Opcode: {prefix}{display_opcode:02X}, Registers: {reg}")
        count += 1
        if count >= 50000:
            running = False

        print(count)


if __name__ == "__main__":
    main()
