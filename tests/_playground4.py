import bitbin as bb
from bitbin.impl import *


class MyPacket(Struct):
    foo: int
    bar: int


mypacket = MyPacket(foo=1, bar=2)
pkt = bb.dumps(mypacket)
print(str(mypacket).ljust(35), '->', pkt)

print(str(pkt).ljust(35), '->', bb.loads(MyPacket, pkt))
