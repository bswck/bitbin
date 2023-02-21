import functools
import construct as _lib
from bitbin import core


__all__ = (
    'Struct',
    'BitStruct',
    'LazyStruct',
    'AlignedStruct',
)


class Struct(core.ModelDataclass, _bitbin=True):
    _impl = _lib.Struct


class BitStruct(core.ModelDataclass, _bitbin=True):
    _impl = _lib.BitStruct


class LazyStruct(core.ModelDataclass, _bitbin=True):
    _impl = _lib.LazyStruct


class AlignedStruct(core.ModelDataclass, _bitbin=True):
    _impl = _lib.AlignedStruct

    @classmethod
    def _modulus(cls, context):
        raise NotImplementedError

    def __init_subclass__(
            cls, _bitbin=False,
            stack_offset=1,
            annotation_mgr=None
    ):
        if _bitbin:
            return
        super().__init_subclass__(
            stack_offset=stack_offset+1,
            annotation_mgr=annotation_mgr
        )
        cls._impl = functools.partial(cls._impl, cls._modulus)


class Union(core.ModelDataclass):
    """Port to construct.Union"""

    _impl = _lib.Union  # (parsefrom, *subcons, **subconskw)
