from __future__ import annotations

import sys
import typing

import construct as _lib

from constance import _constants
from constance import classes
from constance import util

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import Literal


__all__ = (
    'Int8sl',
    'Int8sb',
    'Int8sn', 'char',
    'Int8ul',
    'Int8ub',
    'Int8un', 'unsigned_char',
    'Int16sl',
    'Int16sb',
    'Int16sn', 'short',
    'Int16ul',
    'Int16ub',
    'Int16un', 'unsigned_short',
    'Int24sl',
    'Int24sb',
    'Int24sn',
    'Int24ul',
    'Int24ub',
    'Int24un',
    'Int32sl',
    'Int32sb',
    'Int32sn', 'long',
    'Int32ul',
    'Int32ub',
    'Int32un', 'unsigned_long',
    'Int64sl',
    'Int64sb',
    'Int64sn', 'long_long',
    'Int64ul',
    'Int64ub',
    'Int64un', 'unsigned_long_long',
    'Float32l',
    'Float32b',
    'Float32n',
    'Float64l',
    'Float64b',
    'Float64n', 'double',

)


def _char_cast(obj):
    if isinstance(obj, str):
        return ord(obj)
    return int(obj)


Int8sl = classes.Atomic(_lib.Int8sl, int)
Int8sb = classes.Atomic(_lib.Int8sb, int)
Int8sn = classes.Atomic(_lib.Int8sn, int)
Int8ul = classes.Atomic(_lib.Int8ul, int, cast=_char_cast)
Int8ub = classes.Atomic(_lib.Int8ub, int, cast=_char_cast)
Int8un = classes.Atomic(_lib.Int8un, int, cast=_char_cast)

Int16sl = classes.Atomic(_lib.Int16sl, int)
Int16sb = classes.Atomic(_lib.Int16sb, int)
Int16sn = classes.Atomic(_lib.Int16sn, int)
Int16ul = classes.Atomic(_lib.Int16ul, int, cast=_char_cast)
Int16ub = classes.Atomic(_lib.Int16ub, int, cast=_char_cast)
Int16un = classes.Atomic(_lib.Int16un, int, cast=_char_cast)

Int24sl = classes.Atomic(_lib.Int24sl, int)
Int24sb = classes.Atomic(_lib.Int24sb, int)
Int24sn = classes.Atomic(_lib.Int24sn, int)
Int24ul = classes.Atomic(_lib.Int24ul, int)
Int24ub = classes.Atomic(_lib.Int24ub, int)
Int24un = classes.Atomic(_lib.Int24un, int)

Int32sl = classes.Atomic(_lib.Int32sl, int)
Int32sb = classes.Atomic(_lib.Int32sb, int)
Int32sn = classes.Atomic(_lib.Int32sn, int)
Int32ul = classes.Atomic(_lib.Int32ul, int)
Int32ub = classes.Atomic(_lib.Int32ub, int)
Int32un = classes.Atomic(_lib.Int32un, int)

Int64sl = classes.Atomic(_lib.Int64sl, int)
Int64sb = classes.Atomic(_lib.Int64sb, int)
Int64sn = classes.Atomic(_lib.Int64sn, int)
Int64ul = classes.Atomic(_lib.Int64ul, int)
Int64ub = classes.Atomic(_lib.Int64ub, int)
Int64un = classes.Atomic(_lib.Int64un, int)

Float32l = classes.Atomic(_lib.Float32l, float)
Float32b = classes.Atomic(_lib.Float32b, float)
Float32n = classes.Atomic(_lib.Float32n, float)
Float64l = classes.Atomic(_lib.Float64l, float)
Float64b = classes.Atomic(_lib.Float64b, float)
Float64n = classes.Atomic(_lib.Float64n, float)

char = Int8sn
unsigned_char = Int8un

short = Int16sn
unsigned_short = Int16un

long = Int32sn
unsigned_long = Int32un

long_long = Int64sn
unsigned_long_long = Int64un

double = Float64n

atomic_types, generic_types = util.atomic_types, util.generic_types

atomic_types.register(int, classes.Atomic(_lib.Int32sn, int))
atomic_types.register(float, classes.Atomic(_lib.Float32n, float))
atomic_types.register(str, classes.Atomic(_lib.CString(_constants.DEFAULT_ENCODING), str))
atomic_types.register(bytes, classes.Atomic(_lib.GreedyBytes, bytes))
atomic_types.register(bytearray, classes.Atomic(_lib.GreedyBytes, bytearray))

generic_types.register(list, classes.Generic(list))
generic_types.register(set, classes.Generic(set))
generic_types.register(frozenset, classes.Generic(frozenset))
generic_types.register(tuple, classes.Generic(tuple))


VALID_ENDIANNESSES = {
    'l': 'l',
    'little': 'l',
    'big': 'b',
    'b': 'b',
    'native': (byte_order := sys.byteorder),
    'n': byte_order,
}


def integer(
    size: int | Callable = 4,
    signed: bool = True,
    bitwise: bool = False,
    endianness: Literal['l', 'little', 'big', 'b', 'native', 'n'] = 'n'
):
    endianness = VALID_ENDIANNESSES[endianness.lower()]
    cs = (_lib.BytesInteger, _lib.BitsInteger)[bitwise]
    return classes.Atomic(cs(size, signed=signed, swapped=endianness == 'l'), int)
