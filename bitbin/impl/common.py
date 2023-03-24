from __future__ import annotations

from typing import Callable

import construct as _lib

from bitbin import config
from bitbin import core
from bitbin import util


__all__ = (
    'Bytes',
    'FormatField',

    'Bool',
    'Bit',
    'Float32l',
    'Float32b',
    'Float32n',
    'Float64l',
    'Float64b',
    'Float64n',
    'Int8sl',
    'Int8sb',
    'Int8sn',
    'Int8ul',
    'Int8ub',
    'Int8un',
    'Int16sl',
    'Int16sb',
    'Int16sn',
    'Int16ul',
    'Int16ub',
    'Int16un',
    'Int24sl',
    'Int24sb',
    'Int24sn',
    'Int24ul',
    'Int24ub',
    'Int24un',
    'Int32sl',
    'Int32sb',
    'Int32sn',
    'Int32ul',
    'Int32ub',
    'Int32un',
    'Int64sl',
    'Int64sb',
    'Int64sn',
    'Int64ul',
    'Int64ub',
    'Int64un',
    'Nibble',
    'Octet',
    'Pass',

    'char',
    'unsigned_char',
    'short',
    'unsigned_short',
    'long',
    'unsigned_int',
    'unsigned_long',
    'long_long',
    'unsigned_long_long',
    'double',

    'int_type',
    'bitwise_int_type',
)

Bool = Flag = core.Atomic(_lib.Flag, bool)
Bit = core.Atomic(_lib.Bit, int)
Nibble = core.Atomic(_lib.Nibble, int)
Octet = core.Atomic(_lib.Octet, int)


def bitwise_int_type(
        bit_length,
        signed=True,
        endianness=config.ENDIANNESS
):
    swapped = endianness == config.Endianness.LITTLE
    return core.Atomic(_lib.BitsInteger(bit_length), signed=signed, swapped=swapped)



Int8sl = core.Atomic(_lib.Int8sl, int)
Int8sb = core.Atomic(_lib.Int8sb, int)
Int8sn = core.Atomic(_lib.Int8sn, int)
Int8ul = core.Atomic(_lib.Int8ul, int)
Int8ub = core.Atomic(_lib.Int8ub, int)
Int8un = core.Atomic(_lib.Int8un, int)

Int16sl = core.Atomic(_lib.Int16sl, int)
Int16sb = core.Atomic(_lib.Int16sb, int)
Int16sn = core.Atomic(_lib.Int16sn, int)
Int16ul = core.Atomic(_lib.Int16ul, int)
Int16ub = core.Atomic(_lib.Int16ub, int)
Int16un = core.Atomic(_lib.Int16un, int)

Int24sl = core.Atomic(_lib.Int24sl, int)
Int24sb = core.Atomic(_lib.Int24sb, int)
Int24sn = core.Atomic(_lib.Int24sn, int)
Int24ul = core.Atomic(_lib.Int24ul, int)
Int24ub = core.Atomic(_lib.Int24ub, int)
Int24un = core.Atomic(_lib.Int24un, int)

Int32sl = core.Atomic(_lib.Int32sl, int)
Int32sb = core.Atomic(_lib.Int32sb, int)
Int32sn = core.Atomic(_lib.Int32sn, int)
Int32ul = core.Atomic(_lib.Int32ul, int)
Int32ub = core.Atomic(_lib.Int32ub, int)
Int32un = core.Atomic(_lib.Int32un, int)

Int64sl = core.Atomic(_lib.Int64sl, int)
Int64sb = core.Atomic(_lib.Int64sb, int)
Int64sn = core.Atomic(_lib.Int64sn, int)
Int64ul = core.Atomic(_lib.Int64ul, int)
Int64ub = core.Atomic(_lib.Int64ub, int)
Int64un = core.Atomic(_lib.Int64un, int)


def int_type(
        byte_length,
        signed=True,
        endianness=config.ENDIANNESS
):
    swapped = endianness == config.Endianness.LITTLE
    return core.Atomic(_lib.BytesInteger(byte_length), signed=signed, swapped=swapped)


Float32l = core.Atomic(_lib.Float32l, float)
Float32b = core.Atomic(_lib.Float32b, float)
Float32n = core.Atomic(_lib.Float32n, float)
Float64l = core.Atomic(_lib.Float64l, float)
Float64b = core.Atomic(_lib.Float64b, float)
Float64n = core.Atomic(_lib.Float64n, float)

Pass = core.Singleton(_lib.Pass, None)


if config.ENDIANNESS == config.Endianness.BIG:
    char = Int8sb
    unsigned_char = Int8ub

    short = Int16sb
    unsigned_short = Int16ub

    long = Int32sb
    long_int = Int32sb
    unsigned = Int32ub
    unsigned_int = Int32ub
    unsigned_long = Int32ub
    unsigned_long_int = Int32ub

    long_long = Int64sb
    long_long_int = Int64sb
    unsigned_long_long = Int64ub
    unsigned_long_long_int = Int64ub

    double = Float64b
else:
    char = Int8sl
    unsigned_char = Int8ul

    short = Int16sl
    unsigned_short = Int16ul

    long = Int32sl
    long_int = Int32sl
    unsigned = Int32ul
    unsigned_int = Int32ul
    unsigned_long = Int32ul
    unsigned_long_int = Int32ul

    long_long = Int64sl
    long_long_int = Int64sl
    unsigned_long_long = Int64ul
    unsigned_long_long_int = Int64ul

    double = Float64l


atomic_types = util.atomic_types
atomic_types.register(int, core.Atomic(_lib.Int32sb, int))
atomic_types.register(float, core.Atomic(_lib.Float32b, float))
atomic_types.register(str, core.Atomic(_lib.CString(config.DEFAULT_ENCODING), str))
atomic_types.register(bytes, core.Atomic(_lib.GreedyBytes, bytes))
atomic_types.register(bytearray, core.Atomic(_lib.GreedyBytes, bytearray))

generic_types = util.generic_types
generic_types.register(list, core.Generic(list))
generic_types.register(set, core.Generic(set))
generic_types.register(frozenset, core.Generic(frozenset))
generic_types.register(tuple, core.Generic(tuple))


class Bytes(core.Atomic):
    """Port to construct.Bytes"""
    length: int | Callable[[_lib.Container], int]

    _impl = _lib.Bytes  # (length)

    def __init__(self, length):
        self.length = length
        super().__init__(self._impl(length), bytes, False)

    def _init(self, obj, context=None):
        return self._initializer(obj)

    def _load(self, data, context):
        return self._loader(data)


class FormatField(core.Atomic):
    """Port to construct.FormatField"""

    _impl = _lib.FormatField  # (endianity, format)
    _non_int_types = {
        'f': float, 'd': float, 'e': float,
        's': str, 'p': str, '?': bool
    }

    def __init__(self, endianity, fmt):
        self.endianity = endianity
        self.format = fmt
        lib_object = self._impl(endianity, fmt)
        super().__init__(
            lib_object,
            self._non_int_types.get(fmt, int),
            False
        )
