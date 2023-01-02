from __future__ import annotations

import inspect

import construct as _lib

from constance import util


__all__ = (
    'Constance',

    'Atomic',
    'Composite',
    'SubconstructAlias',
)


class Constance:
    """Constance - class-based factory of construct.Construct objects."""

    @classmethod
    def construct(cls) -> _lib.Construct:
        """Return a construct for self-serialization and self-deserialization."""
        raise NotImplementedError

    @classmethod
    def sizeof(cls, **context) -> int:
        """Compute size of a factorized construct."""
        construct = cls.construct()
        return construct.sizeof(**context)


class Atomic(Constance):
    def __init__(self, construct, cast=None, python_type=None):
        self._construct = construct
        self._cast = cast
        self._python_type = python_type

    @property
    def type_name(self):
        return self._python_type.__name__ if self._python_type else type(self._construct).__name__

    def construct(self):
        return util.construct_coerce_type(self._python_type, self._construct)

    def modify(self, outer_wrapper_cls, /, **kwargs):
        from constance.composite import modify
        return modify(self, outer_wrapper_cls, **kwargs)

    def __call__(self, obj):
        if self._python_type and isinstance(obj, self._python_type):
            return obj
        try:
            return self._cast(obj)
        except Exception as exc:
            err = TypeError(
                f'cannot cast {obj} to the desired type'
                + (' ' + self._python_type.__name__.join('()') if self._python_type else '')
            )
            if self._cast:
                raise err from exc
            else:
                raise err from None

    def __getitem__(self, size):
        from constance.modifiers import Array
        return Array[size, self._construct]

    def __repr__(self):
        return f'{type(self).__name__}({type(self._construct).__name__})'


class SubconstructAlias(Constance):
    def __init__(
            self,
            name,
            factory,
            args=(),
            kwargs=None,
            python_type=None
    ):
        self._name = name
        self._factory = factory

        self._args = args
        self._kwargs = kwargs or {}

        self._python_type = python_type

        if __debug__:
            self._validate_arguments()

    def _validate_arguments(self):
        signature = inspect.signature(self._factory)
        try:
            signature.bind(*self._args, **self._kwargs)
        except TypeError as exc:
            raise TypeError(
                f'error during validating arguments passed to {self._name}[]\n'
                f'Check help({self._factory.__module__}.{self._factory.__qualname__}) '
                'for details on proper use.'
            ) from exc

    def __call__(self, *args, **kwargs):
        return self

    def __getitem__(self, size):
        from constance.modifiers import Array
        return Array[size, self._factory]

    def construct(self):
        return util.construct_coerce_type(
            self._python_type, self._factory(*self._args, **self._kwargs)
        )


class Composite(Constance):
    def __class_getitem__(cls, args):
        if not isinstance(args, tuple):
            args = (args,)
        return cls._class_getitem(args)

    @classmethod
    def _class_getitem(cls, args):
        raise ValueError(f'{cls.__name__}[{", ".join(map(str, args)) or ()}] is undefined')
