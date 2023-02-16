"""Recipes for configuring the construct library."""

import functools
import importlib
import locale
import sys

import construct as _lib


__all__ = (
    'register_encoding',
    'set_global_endianness',
    'Endianness',
    'GLOBAL_ENDIANNESS',
    'DEFAULT_ENCODING',
    'VALID_ENDIANNESSES',
)


DEFAULT_ENCODING = locale.getpreferredencoding()
MOCK_STRING = '\0'


@functools.lru_cache(0)
def register_encoding(encoding, unit_size=None):
    if unit_size is None:
        unit_size = len(MOCK_STRING.encode(encoding))
    _lib.possiblestringencodings[encoding] = unit_size


class Endianness:
    LITTLE = 'l'
    BIG = 'b'
    NATIVE = sys.byteorder[0]


VALID_ENDIANNESSES = {
    'l': Endianness.LITTLE,
    'little': Endianness.LITTLE,
    'big': Endianness.BIG,
    'b': Endianness.BIG,
    'native': Endianness.NATIVE,
    'n': Endianness.NATIVE,
}


GLOBAL_ENDIANNESS = Endianness.BIG


def set_global_endianness(endianness):
    global GLOBAL_ENDIANNESS
    try:
        endianness = VALID_ENDIANNESSES[endianness.lower()]
    except KeyError:
        raise ValueError(f'invalid endianness {endianness!r}') from None
    GLOBAL_ENDIANNESS = endianness
    from bitbin import core
    importlib.reload(core)
