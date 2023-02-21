import bitbin as bb


bb.set_endianness(bb.BIG_ENDIAN)


class PlusVersion(bb.BitStruct):
    major: bb.Nibble
    minor: bb.Nibble


class NiceStruct(bb.Struct):
    version: PlusVersion
    name: str
    data: bb.Switch[bb.this.name, bb.Int32ub]


data = bb.models(NiceStruct).data
data.register('foo', bb.Int8ub)
data.register('bar', bb.Int16ub)


pkt = bb.dumps(NiceStruct((5, 10), 'foo', data=255))
print(pkt)
print(bb.loads(NiceStruct, pkt))
