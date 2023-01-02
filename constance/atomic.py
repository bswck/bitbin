import construct as _lib

from constance import _constants
from constance import api
from constance import util


__all__ = (
    'atomic_defaults',
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


Int8sl = api.Atomic(_lib.Int8sl, python_type=int)
Int8sb = api.Atomic(_lib.Int8sb, python_type=int)
Int8sn = api.Atomic(_lib.Int8sn, python_type=int)
Int8ul = api.Atomic(_lib.Int8ul, python_type=int, cast=_char_cast)
Int8ub = api.Atomic(_lib.Int8ub, python_type=int, cast=_char_cast)
Int8un = api.Atomic(_lib.Int8un, python_type=int, cast=_char_cast)

Int16sl = api.Atomic(_lib.Int16sl, python_type=int)
Int16sb = api.Atomic(_lib.Int16sb, python_type=int)
Int16sn = api.Atomic(_lib.Int16sn, python_type=int)
Int16ul = api.Atomic(_lib.Int16ul, python_type=int, cast=_char_cast)
Int16ub = api.Atomic(_lib.Int16ub, python_type=int, cast=_char_cast)
Int16un = api.Atomic(_lib.Int16un, python_type=int, cast=_char_cast)

Int24sl = api.Atomic(_lib.Int24sl, python_type=int)
Int24sb = api.Atomic(_lib.Int24sb, python_type=int)
Int24sn = api.Atomic(_lib.Int24sn, python_type=int)
Int24ul = api.Atomic(_lib.Int24ul, python_type=int)
Int24ub = api.Atomic(_lib.Int24ub, python_type=int)
Int24un = api.Atomic(_lib.Int24un, python_type=int)

Int32sl = api.Atomic(_lib.Int32sl, python_type=int)
Int32sb = api.Atomic(_lib.Int32sb, python_type=int)
Int32sn = api.Atomic(_lib.Int32sn, python_type=int)
Int32ul = api.Atomic(_lib.Int32ul, python_type=int)
Int32ub = api.Atomic(_lib.Int32ub, python_type=int)
Int32un = api.Atomic(_lib.Int32un, python_type=int)

Int64sl = api.Atomic(_lib.Int64sl, python_type=int)
Int64sb = api.Atomic(_lib.Int64sb, python_type=int)
Int64sn = api.Atomic(_lib.Int64sn, python_type=int)
Int64ul = api.Atomic(_lib.Int64ul, python_type=int)
Int64ub = api.Atomic(_lib.Int64ub, python_type=int)
Int64un = api.Atomic(_lib.Int64un, python_type=int)

Float32l = api.Atomic(_lib.Float32l, python_type=float)
Float32b = api.Atomic(_lib.Float32b, python_type=float)
Float32n = api.Atomic(_lib.Float32n, python_type=float)
Float64l = api.Atomic(_lib.Float64l, python_type=float)
Float64b = api.Atomic(_lib.Float64b, python_type=float)
Float64n = api.Atomic(_lib.Float64n, python_type=float)

char = Int8sn
unsigned_char = Int8un

short = Int16sn
unsigned_short = Int16un

long = Int32sn
unsigned_long = Int32un

long_long = Int64sn
unsigned_long_long = Int64un

double = Float64n

atomic_defaults = {
    int: api.Atomic(_lib.Int32sn, python_type=int),
    float: api.Atomic(_lib.Float32n, python_type=float),
    str: api.Atomic(_lib.CString(_constants.DEFAULT_ENCODING), python_type=str),
    bytes: api.Atomic(_lib.GreedyBytes, python_type=bytes),
    bytearray: api.Atomic(_lib.GreedyBytes, python_type=bytearray),
}

util.make_constance.atomic.update(atomic_defaults)
