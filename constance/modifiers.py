import collections.abc
import copy

import construct as _lib

from constance import api
from constance import composite
from constance import util


__all__ = (
    'Array',
    'ArrayLike',
    'Default',
    'GreedyRange',
    'LazyArray',
    'Optional',
    'Padded',
    'Peek',
    'Pointer',
    'Prefixed',
    'Rebuild',
)


class ArrayLike(composite.Modifier):
    @staticmethod
    def init(inner_cls, instance, *inits):
        instance.__modified__ = [
            (
                init if (isinstance(inner_cls, type) and isinstance(init, inner_cls))
                else util.initialize_constance(inner_cls, init)
            )
            for init in inits
        ]
        if isinstance(inner_cls, api.Atomic):
            return copy.deepcopy(instance.__modified__)
        return [member._get_data_for_building() for member in instance.__modified__]

    @staticmethod
    def load(outer_cls, inner_cls, args, **kwargs):
        return outer_cls(*(
            inner_cls(sub_args)
            if isinstance(inner_cls, api.Atomic)
            else inner_cls._load_from_args(sub_args, **kwargs)
            for sub_args in args
        ))

    @classmethod
    def repr(cls, inner_cls, modified_type, instance=None, **kwds):
        return super().repr(inner_cls, modified_type, **kwds) + (
            ', '.join(map(repr, instance.__modified__)).join('()')
            if instance is not None else ''
        )

    @staticmethod
    def iter(instance):
        yield from instance.__modified__


class Array(ArrayLike):
    _impl = _lib.Array

    @classmethod
    def _class_getitem(cls, args):
        return cls.subconstruct(args)


class LazyArray(ArrayLike):
    _impl = _lib.LazyArray


class GreedyRange(ArrayLike):
    _impl = _lib.GreedyRange


class Prefixed(composite.Modifier):
    _impl = _lib.Prefixed

    @staticmethod
    def map_kwargs(kwargs):
        kwargs.update(lengthfield=util.ensure_construct(kwargs.get('lengthfield')))
        return kwargs


class Rebuild(composite.Modifier):
    _impl = _lib.Rebuild


class Default(composite.Modifier):
    _impl = _lib.Default

    @classmethod
    def init(cls, inner_cls, instance, *args, **kwargs):
        instance.__modified__ = wrapped = None
        if args or kwargs:
            wrapped = super().init(inner_cls, instance, *args, **kwargs)
        return wrapped


class Optional(composite.Modifier):
    _impl = _lib.Optional


class Pointer(composite.Modifier):
    _impl = _lib.Pointer


class Peek(composite.Modifier):
    _impl = _lib.Peek


class Padded(composite.Modifier):
    _impl = _lib.Padded
