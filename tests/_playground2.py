from constance import *


class CharOrStr(Switch):
    key = this.packet_type


@CharOrStr.register(0)
class UCharOverload(Struct, terminated=True):
    data: unsigned_char


@CharOrStr.register(0)
class StrOverload(Struct):
    data: str


class MyStruct(Struct, compiled=True):
    packet_type: Int8un
    data: CharOrStr


for mock_val in ('string', 255):
    s = MyStruct(0, [mock_val])
    print(s, end=' -> ')

    p = s.build()
    print(p, end=' -> ')
    r = MyStruct.load(p)
    print(r)
