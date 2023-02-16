import timeit

import construct as cs

import bitbin as bb
from bitbin.impl import *


class SubStruct(bb.LazyStruct):
    a: long = 1
    b: int = 2


class Class(bb.LazyStruct):
    a: long
    b: long
    c: SubStruct = ()


def test1():
    pkt = bb.dumps(Class(a=1, b=2, c=SubStruct(a=3, b=4)))
    return pkt, bb.loads(Class, pkt)


SUBSTRUCT = cs.LazyStruct(
    a=long._aconstruct,
    b=long._aconstruct
)


CLASS = cs.LazyStruct(
    a=long._aconstruct,
    b=long._aconstruct,
    c=SUBSTRUCT
)


def test2():
    pkt = CLASS.build({'a': 1, 'b': 2, 'c': {'a': 3, 'b': 4}})
    return pkt, CLASS.parse(pkt)


print(*test1())
print(*test2())

print(timeit.timeit(test1, number=10000))
print(timeit.timeit(test2, number=10000))
