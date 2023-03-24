import bitbin as bb


bb.set_endianness(bb.LITTLE_ENDIAN)


class State(bb.BitStruct):
    a: bb.Bit = False
    b: bb.Bit = False
    c: bb.Bit = False
    d: bb.Bit = False
    e: bb.Bit = False
    f: bb.Bit = False
    g: bb.Bit = False
    h: bb.Bit = False


xff = State(e=True, f=True)
pkt = bb.dumps(xff)
print(pkt)
print(bb.loads(State, pkt))
