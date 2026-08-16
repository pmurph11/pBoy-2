class Registers():
    def __init__(self):
        self.a = 0
        self.b = 0
        self.c = 0
        self.d = 0
        self.e = 0
        self.h = 0
        self.l = 0
        self.f = 0
        self.pc = 0x0000
        self.sp = 0x0000

    # Register pairs
    @property
    def bc(self):
        return (self.b << 8) | self.c
    
    @property
    def hl(self):
        return (self.h << 8) | self.l
    
    @property
    def de(self):
        return (self.d << 8) | self.e

    @de.setter
    def de(self, value):
        self.d = (value >> 8) & 0xFF
        self.e = value & 0xFF

    @property
    def af(self):
        return (self.a << 8) | self.f



    def __repr__(self):
        return f"Registers(a={self.a:02X}, b={self.b:02X}, c={self.c:02X}, d={self.d:02X}, e={self.e:02X}, h={self.h:02X}, l={self.l:02X}, f={self.f:02X}, bc={self.bc:04X}, de={self.de:04X}, hl={self.hl:04X}, af={self.af:04X}, pc={self.pc:04X}, sp={self.sp:04X})"
