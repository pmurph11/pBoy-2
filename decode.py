from mem import fetch_byte, write_byte
from alu import (ADD_16, add_hl_r16, ALU_OPS, inc8, dec8, cpl, step_r16, rla, rra, rl_r8,
    sra_a, swap_r8, bit_7_h, Z_MASK, N_MASK, H_MASK, C_MASK)   


r8_order = ['b', 'c', 'd', 'e', 'h', 'l', None, 'a']  # None represents (HL) which is not handled here

# Misc 
def ld_r16_a(mem, reg, pair_name):
    # Store A at pairs address
    write_byte(mem, getattr(reg, pair_name), reg.a)

def get_operand(mem, reg, index):
    if index == 6:
        return mem[reg.hl]
    else:
        return getattr(reg, r8_order[index])

def set_operand(mem, reg, index, value):
    if index == 6:
        write_byte(mem, reg.hl, value)
    else:
        setattr(reg, r8_order[index], value)


ld_r8_r8_table = {}
for dst_index in range(len(r8_order)):
    for src_index in range(len(r8_order)):
        opcode = 0x40 + (dst_index << 3) + src_index
        if opcode == 0x76:  # HALT instruction, not a valid LD instruction
            continue
        ld_r8_r8_table[opcode] = (dst_index, src_index)
        
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
    write_byte(mem, reg.hl, reg.a)
    reg.hl = (reg.hl + step) & 0xFFFF

def ld_hl_a(mem, reg):
    write_byte(mem, reg.hl, reg.a)

def ld_a_a8(mem, reg):
    a8 = fetch_byte(mem, reg)
    reg.a = mem[0xFF00 + a8]

def ldh_a8_a(mem, reg):
    a8 = fetch_byte(mem, reg)
    write_byte(mem, 0xFF00 + a8, reg.a)

def ld_c_a(mem, reg):
    base = 0xFF00
    val = reg.c
    write_byte(mem, base + val, reg.a)

# --- 16-bit Load instructions ---
def ld_a_hl_step(mem, reg, step):
    reg.a = mem[reg.hl]
    reg.hl = (reg.hl + step) & 0xFFFF


def ld_hl_d8(mem, reg):
    d8 = fetch_byte(mem, reg)
    write_byte(mem, reg.hl, d8)

def ld_a16_a(mem, reg):
    low = fetch_byte(mem, reg)
    high = fetch_byte(mem, reg)
    addr = high << 8 | low
    write_byte(mem, addr, reg.a)

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

def check_condition(reg, flag_number):
    if flag_number == 0:
        return (reg.f & Z_MASK) == 0  # Z flag not set
    elif flag_number == 1:
        return (reg.f & Z_MASK) != 0  # Z flag set
    elif flag_number == 2:
        return (reg.f & C_MASK) == 0  # C flag not set
    elif flag_number == 3:
        return (reg.f & C_MASK) != 0  # C flag set
    
# --- 8-bit Jump/Call instructions ---
def jr_r8(mem, reg):
    r8 = fetch_byte(mem, reg)
    if r8 >= 0x80:
        r8 -= 0x100  # Convert to signed
    reg.pc = (reg.pc + r8) & 0xFFFF

def rst(mem, reg, addr):
    # Push the current PC onto the stack
    ret_addr = reg.pc
    high_byte = (ret_addr >> 8) & 0xFF
    low_byte = ret_addr & 0xFF

    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, high_byte)
    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, low_byte)

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
    write_byte(mem, reg.sp, high_byte)
    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, low_byte)

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
    write_byte(mem, reg.sp, high)

    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, low)

def push_pc(mem, reg):
    # PUSH PC onto the stack, high byte first, then low byte
    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, (reg.pc >> 8) & 0xFF)  # High byte
    reg.sp = (reg.sp - 1) & 0xFFFF
    write_byte(mem, reg.sp, reg.pc & 0xFF)  # Low byte

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
        value = get_operand(mem, reg, src)
        set_operand(mem, reg, dst, value)
        return True, opcode

    if 0x80 <= opcode <= 0xBF:
        operation_index = (opcode >> 3) & 0x07
        operand_index = opcode & 0x07
        val = get_operand(mem, reg, operand_index)
        ALU_OPS[operation_index](reg, val)
        return True, opcode

    # Inc 8 family
    if (opcode & 0xC7) == 0x04:
        operand_index = (opcode >> 3) & 0x07
        val = get_operand(mem, reg, opcode & 0x07)
        new_val = inc8(reg, val)
        set_operand(mem, reg, operand_index, new_val)
        return True, opcode

    # Dec 8 family
    if (opcode & 0xC7) == 0x05:
        operand_index = (opcode >> 3) & 0x07
        val = get_operand(mem, reg, opcode & 0x07)
        new_val = dec8(reg, val)
        set_operand(mem, reg, operand_index, new_val)
        return True, opcode
    
    # ALU Immediate table
    if (opcode & 0xC7) == 0xC6:
        operation_index = (opcode >> 3) & 0x07
        val = fetch_byte(mem, reg)
        ALU_OPS[operation_index](reg, val)
        return True, opcode
    
    # ALU 16-bit add table
    if (opcode & 0xCF) == 0x09:
        pair_index = (opcode >> 4) & 0x03
        val = getattr(reg, ADD_16[pair_index])  # Get the value of BC, DE, HL, or SP
        add_hl_r16(reg, val)
        return True, opcode
    
    # --- Conditional jumps and calls ---
    if (opcode & 0xE7) == 0x20:
        val = fetch_byte(mem, reg)
        if val >= 0x80:
            val -= 0x100  # Convert to signed
        if check_condition(reg, (opcode >> 3) & 0x03):
            reg.pc = (reg.pc + val) & 0xFFFF  # Jump to new address, wrap around at 16 bits
        return True, opcode
    
    if (opcode & 0xE7) == 0xC0:
        if check_condition(reg, (opcode >> 3) & 0x03):
            low = mem[reg.sp]
            reg.sp = (reg.sp + 1) & 0xFFFF
            high = mem[reg.sp]
            reg.sp = (reg.sp + 1) & 0xFFFF
            reg.pc = (high << 8) | low
        return True, opcode

    if (opcode & 0xE7) == 0xC2:
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        addr = (high << 8) | low
        if check_condition(reg, (opcode >> 3) & 0x03):
            reg.pc = addr
        return True, opcode

    if (opcode & 0xE7) == 0xC4:
        low = fetch_byte(mem, reg)
        high = fetch_byte(mem, reg)
        addr = (high << 8) | low    
        if check_condition(reg, (opcode >> 3) & 0x03):
            push_pc(mem, reg)
            reg.pc = addr
        return True, opcode

    match opcode:
        case 0x00:
            pass  # NOP
        case 0x01:
            ld_r16_d16(mem, reg, 'b', 'c')
        case 0x02:
            ld_r16_a(mem, reg, 'bc')
        case 0x03:
            step_r16(reg, 'b', 'c', 1)
        case 0x06:
            ld_r8_d8(mem, reg, 'b')
        case 0x0B:
            step_r16(reg, 'b', 'c', -1)
        case 0x0E:
            ld_r8_d8(mem, reg, 'c')
        case 0x11:
            ld_r16_d16(mem, reg, 'd', 'e')
        case 0x12:
            ld_r16_a(mem, reg, 'de')
        case 0x13:
            step_r16(reg, 'd', 'e', 1)
        case 0x16:
            ld_r8_d8(mem, reg, 'd')
        case 0x17:
            rla(reg)
        case 0x18:
            jr_r8(mem, reg)
        case 0x1A:
            ld_a_r16(mem, reg, 'd', 'e')
        case 0x1B:
            step_r16(reg, 'd', 'e', -1)
        case 0x1E:
            ld_r8_d8(mem, reg, 'e')
        case 0x1F:
            rra(reg)
        case 0x21:
            ld_r16_d16(mem, reg, 'h', 'l')
        case 0x22:
            ld_hl_step_a(mem, reg, 1)
        case 0x23:
            step_r16(reg, 'h', 'l', 1)
        case 0x26:
            ld_r8_d8(mem, reg, 'h')
        case 0x2A:
            ld_a_hl_step(mem, reg, 1)
        case 0x2B:
            step_r16(reg, 'h', 'l', -1)
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
        case 0x3E:
            ld_r8_d8(mem, reg, 'a')   
        case 0x76:
            pass  # HALT instruction, do nothing for now            
        case 0x77:
            ld_hl_a(mem, reg)
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
        case 0xD1:
            pop_r16(mem, reg, 'd', 'e')
        case 0xD5:
            push_r16(mem, reg, 'd', 'e')
        case 0xD7:
            rst(mem, reg, 0x10)
        case 0xDF:
            rst(mem, reg, 0x18)
        case 0xE0:
            ldh_a8_a(mem, reg)
        case 0xE1:
            pop_r16(mem, reg, 'h', 'l')
        case 0xE2:
            ld_c_a(mem, reg)
        case 0xE5:
            push_r16(mem, reg, 'h', 'l')
        case 0xE7:
            rst(mem, reg, 0x20)
        case 0xE9:
            reg.pc = reg.hl
        case 0xEA:
            ld_a16_a(mem, reg)
        case 0xEF:
            rst(mem, reg, 0x28)
        case 0xF0:
            ld_a_a8(mem, reg)
        case 0xF3:
            reg.ime = False
        case 0xF5:
            push_r16(mem, reg, 'a', 'f')
        case 0xF7:
            rst(mem, reg, 0x30)
        case 0xFB:
            # EI — on real hardware interrupts are enabled AFTER the next
            # instruction executes, not immediately. Harmless until
            # interrupt dispatch exists; revisit then.
            reg.ime = True
        case 0xFF:
            rst(mem, reg, 0x38)
        case _:
            print(f"Unknown opcode: {opcode:02X} at PC {(reg.pc - 1) & 0xFFFF:04X}")
            print(f"  Registers: {reg}")
            return False, opcode
    return True, opcode
