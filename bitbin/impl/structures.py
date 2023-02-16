import functools

import construct as _lib


from bitbin import core

__all__ = (
    'Struct',
    'BitStruct',
    'LazyStruct',
    'AlignedStruct',
)


class Struct(core.ModelDataclass, interface=True):
    _impl = _lib.Struct


class BitStruct(core.ModelDataclass, interface=True):
    _impl = _lib.BitStruct


class LazyStruct(core.ModelDataclass, interface=True):
    _impl = _lib.LazyStruct


class AlignedStruct(core.ModelDataclass, interface=True):
    _impl = _lib.AlignedStruct

    @classmethod
    def _modulus(cls, context):
        raise NotImplementedError

    def __init_subclass__(cls, interface=False, **kwargs):
        if interface:
            return
        super().__init_subclass__()
        cls._impl = functools.partial(cls._impl, cls._modulus)
