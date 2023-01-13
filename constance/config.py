"""Recipes for configuring the construct library."""

import functools

import construct as _lib


MOCK_STRING = '\0'


@functools.lru_cache(0)
def register_encoding(encoding, unit_size=None):
    if unit_size is None:
        unit_size = len(MOCK_STRING.encode(encoding))
    _lib.possiblestringencodings[encoding] = unit_size
