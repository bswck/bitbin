import bitbin as bb
from bitbin.impl import *


class MyStruct(bb.Struct):
    a: long = 1
    b: int = 2


pkt = bb.dumps(MyStruct(a=10000000))
print(
    pkt,
    bb.loads(MyStruct, pkt)
)
