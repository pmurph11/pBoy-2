from mem import fetch_byte

# --- 8-bit Arithmetic/Logic instructions ---
def sra_a(reg):
    reg.a = (reg.a >> 1) | (reg.a & 0x80)  # Preserve the MSB
    # Clear Z, N, H flags, set
    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= z_mask  # Set Z flag if result is zero

def or_r8_r8(reg, dest_name, src_name):
    dest_byte = getattr(reg, dest_name)
    src_byte = getattr(reg, src_name)
    result = dest_byte | src_byte
    setattr(reg, dest_name, result)

    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if result == 0:
        reg.f |= z_mask  # Set Z flag if result is zero

def or_a_c(reg):
    reg.a |= reg.c

    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= z_mask  # Set Z flag if result is zero

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
    if val == reg.a:
        reg.f |= 0x80  # Set Z flag if result is zero
    else:
        reg.f &= ~0x80  # Clear Z flag if result is not zero
    if low_a < low_val:
        reg.f |= h_mask  # Set H flag for half borrow
    # If B > A set C
    if val > reg.a:
        reg.f |= c_mask
    reg.f |= 0x40  # Set N flag for subtraction

def cpl(reg):
    reg.a ^= 0xFF  # Invert all bits in A
    reg.f |= 0x60  # Set N and H flags, clear Z and C flags

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

def add_a_hl(mem, reg):
    hl = (reg.h << 8) | reg.l
    val = mem[hl]
    original_a = reg.a
    low_a = reg.a & 0x0F
    low_val = val & 0x0F

    result = (reg.a + val) & 0xFF
    reg.a = result

    # Flags
    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags

    if result == 0:
        reg.f |= z_mask  # Set Z flag if result is zero
    if low_a + low_val > 0x0F:
        reg.f |= h_mask  # Set H flag for half carry
    # If B > A set C
    if original_a + val > 0xFF:
        reg.f |= c_mask

def sub_a_b(reg):
    # subtract b from a
    val = reg.b
    original_a = reg.a
    # get both nibbles
    low_a = reg.a & 0x0F
    low_val = val & 0x0F

    result = (reg.a - val) & 0xFF
    reg.a = result

    # Flags
    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags

    if result == 0:
        reg.f |= z_mask  # Set Z flag if result is zero
    reg.f |= n_mask  # Set N flag for subtraction
    if low_a < low_val:
        reg.f |= h_mask  # Set H flag for half borrow
    # If B > A set C
    if original_a < val:
        reg.f |= c_mask

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

def and_a_r8(reg, reg_name):
    val = getattr(reg, reg_name)
    reg.a &= val

    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= z_mask  # Set Z flag if result is zero
    reg.f |= h_mask  # Set H flag for AND operation

def and_a_d8(mem, reg):
    val = fetch_byte(mem, reg)
    reg.a &= val

    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if reg.a == 0:
        reg.f |= z_mask  # Set Z flag if result is zero
    reg.f |= h_mask  # Set H flag for AND operation

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
    # Clear Z, N, H flags, set C flag
    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    reg.f &= ~(z_mask | n_mask | h_mask)  # Clear Z, N, H flags
    if new_carry:
        reg.f |= 0x10  # Set C flag if new carry is 1

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

# --- CB-prefixed bit/swap instructions ---
def swap_r8(reg, reg_name):
    val = getattr(reg, reg_name)
    swapped_val = ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)
    setattr(reg, reg_name, swapped_val)

    # Clear Z, N, H, C flags
    z_mask = 0x80
    n_mask = 0x40
    h_mask = 0x20
    c_mask = 0x10

    reg.f &= ~(z_mask | n_mask | h_mask | c_mask)  # Clear Z, N, H, C flags
    if swapped_val == 0:
        reg.f |= z_mask  # Set Z flag if result is zero

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
