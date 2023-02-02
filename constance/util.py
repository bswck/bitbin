import functools
import types
import typing


__all__ = (
    'make_ctype',
)


def _make_constance_generic(tp, args):
    from constance import impl

    nparams = _TypingLib.get_nparams(tp)

    if nparams == -1:
        count = len(args)
        if ... in args:
            args.remove(...)
            count = None
    else:
        count = None
    if tp is typing.Literal:
        """return _make_constance_literal(args)"""
    factories = list(map(make_ctype, args))
    if isinstance(tp, types.UnionType):
        "return _make_constance_union(tp, factories)"
    tp = generic_types.dispatch(tp) or tp
    if isinstance(tp, type):  #and issubclass(tp, classes.Constance):
        return tp
    if not isinstance(tp, type):
        return # tp(factories, count=count)
    raise TypeError(f'{tp.__name__} type as a data field type is not supported')


def make_ctype(data_type, qualname=None):
    from constance import impl

    if data_type is None:
        raise ValueError(
            'constance class cannot be None' + (' in ' + qualname if qualname else '')
        )

    tp = typing.get_origin(data_type)
    args = list(typing.get_args(data_type))

    # if isinstance(data_type, (classes.AtomicConstruct, classes.Subconstruct)) or (
    #     isinstance(data_type, type)
    #     # and not args
    #     and issubclass(data_type, classes.Constance)
    # ):
    #     return data_type

    if tp and args:
        return _make_constance_generic(tp, args)

    atomic = atomic_types.dispatch(data_type)
    if atomic:
        return atomic

    raise TypeError(
        f'cannot use ambiguous non-factory type {data_type} as a data field'
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
        tp = cls._BUILTIN_TYPES_COUNTERPARTS.get(tp, tp)
        return getattr(tp, '_nparams', None)


generic_types = functools.singledispatch(None)

atomic_types = functools.singledispatch(None)
