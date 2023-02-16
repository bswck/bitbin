import bitbin as bb
from bitbin.impl import *


class Test1(Struct):
    test: Default[Array[2, Default[int, 1], False, tuple], [5, 5]] = None
