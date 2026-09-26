Z_MASK = 0x80
N_MASK = 0x40
H_MASK = 0x20
C_MASK = 0x10


from mem import fetch_byte

# --- 8-bit Arithmetic/Logic instructions ---
def sra_a(reg):
    reg.a = (reg.a >> 1) | (reg.a & 0x80)  # Preserve the MSB

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero

def or_r8_r8(reg, dest_name, src_name):
    dest_byte = getattr(reg, dest_name)
    src_byte = getattr(reg, src_name)
    result = dest_byte | src_byte
    setattr(reg, dest_name, result)

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if result == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero

def or_a_c(reg):
    reg.a |= reg.c


    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero

def dec8(reg, reg_name):
    val = getattr(reg, reg_name)
    low = val & 0x0F
    half_borrow = (low == 0x00)
    dec_val = (val - 1) & 0xFF
    setattr(reg, reg_name, dec_val)

    # CLEAR THE FLAGS
    reg.f &= ~(Z_MASK | N_MASK | H_MASK)  # Clear Z, N, H flags (leave C alone)

    if dec_val == 0:
        reg.f |= Z_MASK
    if half_borrow:
        reg.f |= H_MASK
    reg.f |= N_MASK  # Set N flag for decrement operation

def cp_a_hl(mem, reg):
    val = mem[reg.hl]
    low_a = reg.a & 0x0F
    low_val = val & 0x0F

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)
    if val == reg.a:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    else:
        reg.f &= ~Z_MASK  # Clear Z flag if result is not zero
    if low_a < low_val:
        reg.f |= H_MASK  # Set H flag for half borrow
    # If B > A set C
    if val > reg.a:
        reg.f |= C_MASK
    reg.f |= N_MASK  # Set N flag for subtraction

def cpl(reg):
    reg.a ^= 0xFF  # Invert all bits in A
    reg.f |= 0x60  # Set N and H flags, clear Z and C flags

def cp_d8(mem, reg):
    val = fetch_byte(mem, reg)
    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)

    if reg.a == val:
        reg.f |= Z_MASK

    # SET N REGARDLESS
    reg.f |= N_MASK

    # Half and full borrow

    low_a = reg.a & 0x0F
    low_val = val & 0x0F
    half_borrow = low_a < low_val

    if half_borrow :
        reg.f |= H_MASK

    full_borrow = reg.a < val
    if full_borrow:
        reg.f |= C_MASK

def add_a_hl(mem, reg):
    val = mem[reg.hl]
    original_a = reg.a
    low_a = reg.a & 0x0F
    low_val = val & 0x0F

    result = (reg.a + val) & 0xFF
    reg.a = result

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags

    if result == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    if low_a + low_val > 0x0F:
        reg.f |= H_MASK  # Set H flag for half carry
    # If B > A set C
    if original_a + val > 0xFF:
        reg.f |= C_MASK

def sub_a_b(reg):
    # subtract b from a
    val = reg.b
    original_a = reg.a
    # get both nibbles
    low_a = reg.a & 0x0F
    low_val = val & 0x0F

    result = (reg.a - val) & 0xFF
    reg.a = result

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags

    if result == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    reg.f |= N_MASK  # Set N flag for subtraction
    if low_a < low_val:
        reg.f |= H_MASK  # Set H flag for half borrow
    # If B > A set C
    if original_a < val:
        reg.f |= C_MASK

def inc8(reg, reg_name):
    val = getattr(reg, reg_name)
    low = val & 0x0F
    half_carry = (low == 0x0F)
    inc_val = (val + 1) & 0xFF
    setattr(reg, reg_name, inc_val)

    reg.f &= ~(Z_MASK | N_MASK | H_MASK)  # clear only Z, N, H — leave C alone
    if inc_val == 0:
        reg.f |= Z_MASK
    if half_carry:
        reg.f |= H_MASK

def and_a_r8(reg, reg_name):
    val = getattr(reg, reg_name)
    reg.a &= val

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    reg.f |= H_MASK  # Set H flag for AND operation

def and_a_d8(mem, reg):
    val = fetch_byte(mem, reg)
    reg.a &= val

    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    reg.f |= H_MASK  # Set H flag for AND operation

def xor_a_r8(reg, reg_name):
    reg.a ^= getattr(reg, reg_name)
    reg.f = 0x00  # Clear all flags

    if reg.a == 0:
        reg.f |= 0x80  # Set Z flag if result is zero

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
    reg.f &= ~(Z_MASK | N_MASK | H_MASK)  # Clear Z, N, H flags
    if new_carry:
        reg.f |= C_MASK  # Set C flag if new carry is 1

def rl_r8(reg, reg_name):
    carry = (reg.f & 0x10) >> 4  # Get the current carry flag (C) 0101 0000
    val = getattr(reg, reg_name)
    new_carry = (val & 0x80) >> 7
    val = ((val << 1) | carry) & 0xFF
    setattr(reg, reg_name, val)
    reg.f &= ~(Z_MASK | N_MASK | H_MASK)  # Clear Z, N, H flags
    if val == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero
    if new_carry:
        reg.f |= C_MASK  # Set C flag if new carry is 1

# --- CB-prefixed bit/swap instructions ---
def swap_r8(reg, reg_name):
    val = getattr(reg, reg_name)
    swapped_val = ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)
    setattr(reg, reg_name, swapped_val)



    reg.f &= ~(Z_MASK | N_MASK | H_MASK | C_MASK)  # Clear Z, N, H, C flags
    if swapped_val == 0:
        reg.f |= Z_MASK  # Set Z flag if result is zero

def bit_7_h(reg):
    # Clear N flag
    reg.f &= ~N_MASK

    # Set H flag
    reg.f |= H_MASK

    # Check Z bit
    if reg.h & Z_MASK:
        reg.f &= ~Z_MASK
    else:
        reg.f |= Z_MASK
