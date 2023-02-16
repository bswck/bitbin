import dataclasses
import functools
import types
import typing


__all__ = (
    'make_model',
)

import weakref


def get_type_name(obj):
    if isinstance(obj, type):
        return obj.__name__
    return getattr(obj, '_type_name', None) or type(obj).__name__


def make_model(data_type):
    if data_type is None:
        raise ValueError('model cannot be None')
    if getattr(data_type, '_is_model', False):
        return data_type
    if (tp := typing.get_origin(data_type)) and (args := list(typing.get_args(data_type))):
        nparams = _TypingLib.get_nparams(tp)
        if nparams == -1:
            count = len(args)
            if ... in args:
                args.remove(...)
                count = None
        else:
            count = None
        if tp is typing.Literal:
            raise TypeError('cannot use Literal as a model yet')
        if isinstance(tp, types.UnionType):
            raise TypeError('cannot use Union as a model yet')
        [*factories] = map(make_model, args)
        tp = generic_types.dispatch(tp) or tp
        if isinstance(tp, type):
            return tp
        if not isinstance(tp, type):
            return tp(factories, count=count)  # noqa
        raise TypeError(f'{tp.__name__} type as a bitbin type is not supported')
    try:
        weakref.ref(data_type)
    except TypeError:
        pass
    else:
        atomic = atomic_types.dispatch(data_type)
        if atomic:
            return atomic
    raise TypeError(
        f'illegal object of type {type(data_type).__name__!r} for a model'
    )


class _TypingLib:
    _BUILTIN_TYPES_COUNTERPARTS = {}

    @classmethod
    def make_builtin_types(cls):
        if not cls._BUILTIN_TYPES_COUNTERPARTS:
            cls._BUILTIN_TYPES_COUNTERPARTS.update(
                filter(None, map(cls.generic, vars(typing).values()))
            )

    @staticmethod
    def generic(tp):
        generic = None
        if hasattr(tp, '_nparams'):
            orig = typing.get_origin(tp)
            generic = orig, tp
        return generic

    @classmethod
    def get_nparams(cls, tp):
        cls.make_builtin_types()
        tp = cls._BUILTIN_TYPES_COUNTERPARTS.get(tp) or tp
        return getattr(tp, '_nparams', None)


generic_types = functools.singledispatch(None)
atomic_types = functools.singledispatch(None)
