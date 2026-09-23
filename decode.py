from mem import fetch_byte
from alu import (
    inc8, dec8, cp_a_hl, cpl, cp_d8, add_a_hl, sub_a_b,
    and_a_r8, and_a_d8, xor_a_r8, or_r8_r8, step_r16, rla, rl_r8,
    sra_a, swap_r8, bit_7_h,
)

# LD r8 to R8 mapper
r8_order = ['b', 'c', 'd', 'e', 'h', 'l', None, 'a']  # None represents (HL) which is not handled here

ld_r8_r8_table = {}
for dst_index, dst_name in enumerate(r8_order):
    for src_index, src_name in enumerate(r8_order):
        if dst_name is None or src_name is None:
            continue  # Skip (HL) cases and skip 0x76 (HAL) naturally
        opcode = 0x40 + (dst_index << 3) + src_index
        ld_r8_r8_table[opcode] = (dst_name, src_name)

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
def ld_a_hl_step(mem, reg, step):
    addr = (reg.h << 8) | reg.l
    reg.a = mem[addr]
    addr = (addr + step) & 0xFFFF  # Increment/Decrement
    reg.h = (addr >> 8) & 0xFF
    reg.l = addr & 0xFF

def ld_hl_d8(mem, reg):
    d8 = fetch_byte(mem, reg)
    hl = (reg.h << 8) | reg.l
    mem[hl] = d8

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

def rst(mem, reg, addr):
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
def jp(mem, reg):
    low = fetch_byte(mem, reg)
    high = fetch_byte(mem, reg)
    addr = (high << 8) | low
    reg.pc = addr

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
    addr = (high << 8) | low
    reg.pc = addr

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
        case 0x2F:
            sra_a(reg)
            return True, cb_opcode
        case 0x30:
            swap_r8(reg, 'b')
            return True, cb_opcode
        case 0x31:
            swap_r8(reg, 'c')
            return True, cb_opcode
        case 0x32:
            swap_r8(reg, 'd')
            return True, cb_opcode
        case 0x33:
            swap_r8(reg, 'e')
            return True, cb_opcode
        case 0x34:
            swap_r8(reg, 'h')
            return True, cb_opcode
        case 0x35:
            swap_r8(reg, 'l')
            return True, cb_opcode
        case 0x37:
            # SWAP A
            swap_r8(reg, 'a')
            return True, cb_opcode
        case _:
            print(f"Unknown CB opcode: {cb_opcode:02X} at PC {(reg.pc - 2) & 0xFFFF:04X}")
            print(f"  Registers: {reg}")
            return False, cb_opcode

def decode(mem, reg, opcode):
    if opcode in ld_r8_r8_table:
        dst, src = ld_r8_r8_table[opcode]
        ld_r8_r8(reg, dst, src)
        return True, opcode

    match opcode:
        case 0x00:
            pass  # NOP
        case 0x01:
            ld_r16_d16(mem, reg, 'b', 'c')
        case 0x04:
            inc8(reg, 'b')
        case 0x05:
            dec8(reg, 'b')
        case 0x06:
            ld_r8_d8(mem, reg, 'b')
        case 0x0B:
            step_r16(reg, 'b', 'c', -1)
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
        case 0x2A:
            ld_a_hl_step(mem, reg, 1)
        case 0x2E:
            ld_r8_d8(mem, reg, 'l')
        case 0x2F:
            cpl(reg)
        case 0x31:
            ld_sp_d16(mem, reg)
        case 0x32:
            ld_hl_step_a(mem, reg, -1)
        case 0x36:
            ld_hl_d8(mem, reg)
        case 0x3D:
            dec8(reg, 'a')
        case 0x3E:
            ld_r8_d8(mem, reg, 'a')                
        case 0x90:
            sub_a_b(reg)
        case 0x77:
            ld_hl_a(mem, reg)
        case 0x86:
            add_a_hl(mem, reg)
        case 0xA0:
            and_a_r8(reg, 'b')
        case 0xA1:
            and_a_r8(reg, 'c')
        case 0xA2:
            and_a_r8(reg, 'd')
        case 0xA3:
            and_a_r8(reg, 'e')
        case 0xA4:
            and_a_r8(reg, 'h')
        case 0xA5:
            and_a_r8(reg, 'l')
        case 0xA7:
            and_a_r8(reg, 'a')
        case 0xA8:
            xor_a_r8(reg, 'b')
        case 0xA9:
            xor_a_r8(reg, 'c')
        case 0xAA:
            xor_a_r8(reg, 'd')
        case 0xAB:
            xor_a_r8(reg, 'e')
        case 0xAC:
            xor_a_r8(reg, 'h')
        case 0xAD:
            xor_a_r8(reg, 'l')
        case 0xAF:
            xor_a_r8(reg, 'a')
        case 0xB0:
            or_r8_r8(reg, 'a', 'b')
        case 0xB1:
            or_r8_r8(reg, 'a', 'c')
        case 0xB2:
            or_r8_r8(reg, 'a', 'd')
        case 0xB3:
            or_r8_r8(reg, 'a', 'e')
        case 0xB4:
            or_r8_r8(reg, 'a', 'h')
        case 0xB5:
            or_r8_r8(reg, 'a', 'l')
        case 0xBE:
            cp_a_hl(mem, reg)
        case 0xC1:
            pop_r16(mem, reg, 'b', 'c')
        case 0xC3:
            jp(mem, reg)
        case 0xC5:
            push_r16(mem, reg, 'b', 'c')
        case 0xC7:
            rst(mem, reg, 0x00)
        case 0xC9:
            ret(mem, reg)
        case 0xCB:
            return decode_cb(mem, reg)
        case 0xCD:
            call_a16(mem, reg)
        case 0xCF:
            rst(mem, reg, 0x08)
        case 0xD7:
            rst(mem, reg, 0x10)
        case 0xDF:
            rst(mem, reg, 0x18)
        case 0xE0:
            ldh_a8_a(mem, reg)
        case 0xE2:
            ld_c_a(mem, reg)
        case 0xE6:
            and_a_d8(mem, reg)
        case 0xE7:
            rst(mem, reg, 0x20)
        case 0xEA:
            ld_a16_a(mem, reg)
        case 0xEF:
            rst(mem, reg, 0x28)
        case 0xF0:
            ld_a_a8(mem, reg)
        case 0xF3:
            reg.ime = False
        case 0xF7:
            rst(mem, reg, 0x30)
        case 0xFB:
            # EI — on real hardware interrupts are enabled AFTER the next
            # instruction executes, not immediately. Harmless until
            # interrupt dispatch exists; revisit then.
            reg.ime = True
        case 0xFE:
            cp_d8(mem, reg)
        case 0xFF:
            rst(mem, reg, 0x38)
        case _:
            print(f"Unknown opcode: {opcode:02X} at PC {(reg.pc - 1) & 0xFFFF:04X}")
            print(f"  Registers: {reg}")
            return False, opcode
    return True, opcode
