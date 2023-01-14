import collections.abc
import dataclasses
import functools
import types
import typing

import construct as _lib


__all__ = (
    'call_construct_method',
    'ensure_construct',
    'ensure_construct_or_none',
    'get_field_construct',
    'make_constance',
)


def make_constance(python_type, qualname=None):
    from constance import classes

    if python_type is None:
        raise ValueError(
            'constance class cannot be None'
            + (' in ' + qualname if qualname else '')
        )

    tp = typing.get_origin(python_type)
    args = list(typing.get_args(python_type))
    if (
        isinstance(python_type, (classes.Atomic, classes.Subconstruct))
        or (
            isinstance(python_type, type)
            # and not args
            and issubclass(python_type, classes.Constance)
        )
    ):
        return python_type

    if tp and args:
        nparams = _TypingLib.get_nparams(tp)

        if nparams == -1:
            count = len(args)
            if ... in args:
                args.remove(...)
                count = None
        else:
            count = None
        factories = list(map(make_constance, args))
        if issubclass(tp, types.UnionType):
            return classes.Atomic(_lib.Select(*factories[::-1]))
        tp = generic_types.dispatch(tp) or tp
        if isinstance(tp, type) and issubclass(tp, classes.Constance):
            return tp
        if not isinstance(tp, type):
            return tp(factories, count=count)
        raise TypeError(f'{tp.__name__} type as a data field type is not supported')

    atomic = atomic_types.dispatch(python_type)
    if atomic:
        return atomic
    raise TypeError(f'cannot use ambiguous non-factory type {python_type} as a data field')


generic_types = functools.singledispatch(None)

atomic_types = functools.singledispatch(None)


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
        tp = cls._BUILTIN_TYPES_COUNTERPARTS.get(tp, tp)
        return getattr(tp, '_nparams', None)


def get_field_construct(constance, name):
    construct = _lib.extractfield(call_construct_method(constance))
    assert construct
    if name:
        return _lib.Renamed(construct, name)
    return construct


def call_construct_method(constance_cls):
    return constance_cls.construct()


def ensure_construct(obj):
    if isinstance(obj, _lib.Construct):
        return obj
    return call_construct_method(make_constance(obj))


def ensure_construct_or_none(obj):
    if obj is None:
        return obj
    return ensure_construct(obj)


def find_type_annotation(obj):
    annotation = None
    if isinstance(obj, property):
        annotation = getattr(obj.fget, '__annotations__', {}).get('return')
    if callable(obj) or isinstance(obj, (classmethod, staticmethod)):
        annotation = obj.__annotations__.get('return')
    return annotation


def initialize_constance(constance, initializer, context=None, /, **kwargs):
    from constance.classes import Atomic
    if hasattr(constance, '_load'):
        return constance._load(initializer, context, **kwargs)
    if isinstance(constance, Atomic):
        return constance(initializer, context, **kwargs)
    if not isinstance(initializer, collections.abc.Iterable):
        raise TypeError(
            f'cannot instantiate class {constance.__name__} with {initializer}'
        )
    return constance(*initializer, context, **kwargs)
