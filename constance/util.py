import collections.abc
import functools
import types
import typing

import construct as _lib

from constance import _constants


__all__ = (
    'call_construct_method',
    'construct_coerce_type',
    'ensure_construct',
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
    if not construct:
        raise ValueError
    if name:
        return _lib.Renamed(construct, name)
    return construct


def construct_coerce_type(python_type, construct):
    if python_type and not getattr(construct, _constants.CONSTRUCT_TYPE_COERCION_ATTR, False):
        parsereport = construct._parsereport
        setattr(construct, _constants.CONSTRUCT_TYPE_COERCION_ATTR, True)
        construct._parsereport = lambda stream, context, path: (
            python_type(result) if not isinstance(
                result := parsereport(stream, context, path), python_type
            ) else result
        )
    return construct


def call_construct_method(f):
    try:
        construct = f.construct
    except AttributeError:
        construct = f.metadata.get('construct')
    ret = None
    if construct:
        ret = construct if isinstance(construct, _lib.Construct) else construct()
    if ret is None:
        raise ValueError(f'{f}.construct() is unknown or returned None')
    return ret


def ensure_construct(obj):
    if isinstance(obj, _lib.Construct):
        return obj
    return call_construct_method(make_constance(obj))


def find_type_annotation(obj):
    annotation = None
    if isinstance(obj, property):
        annotation = getattr(obj.fget, '__annotations__', {}).get('return')
    if callable(obj) or isinstance(obj, (classmethod, staticmethod)):
        annotation = obj.__annotations__.get('return')
    return annotation


def initialize_constance(constance, init):
    from constance.classes import Atomic
    if isinstance(constance, Atomic):
        return constance(init)
    if isinstance(init, collections.abc.Mapping):
        return constance._load_from_args(init)
    return constance(*init)
