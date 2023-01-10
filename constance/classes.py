from __future__ import annotations

import contextlib
import copy
import dataclasses
import functools
import inspect
import typing
import weakref

import construct as _lib

from constance import _constants
from constance import util


__all__ = (
    'Constance',

    'Atomic',
    'Composite',
    'Subconstruct',

    'Data',
    'Subconstance',
    'subconstance',

    'BitStruct',
    'Sequence',
    'Struct',

    'field',

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


_MISSING_CAST = object()
_MISSING_EXTENDS = object()


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
    def __init__(self, construct, python_type=None, cast=_MISSING_CAST):
        self._construct = construct
        self._python_type = python_type
        if cast is _MISSING_CAST:
            cast = python_type
        self._cast = typing.cast(typing.Callable, cast)

    @property
    def type_name(self):
        return self._python_type.__name__ if self._python_type else type(self._construct).__name__

    def construct(self):
        return self._construct

    def subconstance(self, subconstance_cls, /, **kwargs):
        return subconstance(self, subconstance_cls, **kwargs)

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
        return Array[size, self._construct]

    def __repr__(self):
        return f'{type(self).__name__}({type(self._construct).__name__})'


class Subconstruct(Constance):
    def __init__(
            self,
            name=None, /, *,
            factory,
            args=(),
            kwargs=None,
            python_type=None
    ):
        self._name = name or (
            factory.__name__
            if isinstance(factory, type) else type(factory).__name__
        )
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
        return Array[size, self._factory]

    def construct(self):
        return self._factory(*self._args, **self._kwargs)


class Composite(Constance):
    def __class_getitem__(cls, args):
        if not isinstance(args, tuple):
            args = (args,)
        return cls._extraction_operator(args)

    @classmethod
    def _extraction_operator(cls, args):
        raise ValueError(f'{cls.__name__}[{", ".join(map(str, args)) or ()}] is undefined')


class Data(Composite):
    """
    A composite Constance that represents data.
    Uses `dataclasses` in the background for managing the data fields.
    """

    _impl = None  # type: typing.ClassVar[type[Constance] | None]
    _field_environment = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _skip_fields = None  # type: typing.ClassVar[list[str]]
    _field_names = []  # type: typing.ClassVar[list[str]]
    _dataclass_params = None

    def __init_subclass__(cls, stack_level=1, env=None, extends=_MISSING_EXTENDS):
        data_fields = []
        setattr(cls, _constants.DATA_FIELDS_ATTR, data_fields)

        if extends is _MISSING_EXTENDS:
            extends = cls.__base__

        dataclass_fields = []

        if cls._field_names is not None:

            cls._field_names = [
                *(getattr(extends, '_field_names', None) or [] if extends else []),
                *cls._field_names
            ]
            cls._skip_fields = [
                *(getattr(extends, '_skip_fields', None) or [] if extends else []),
                *(cls._skip_fields or [])
            ]

            for field_name in set(cls._field_names).difference(cls._skip_fields):
                if field_name not in cls.__annotations__:
                    _find_annotation = util.find_type_annotation
                    try:
                        obj = getattr(cls, field_name)
                        annotation = _find_annotation(obj)
                        if annotation is None:
                            raise AttributeError
                    except AttributeError:
                        raise AttributeError(
                            f'{cls.__name__}.{field_name} is missing a type annotation'
                        ) from None
                    cls.__annotations__[field_name] = annotation

        dataclasses.dataclass(cls, **(cls._dataclass_params or {}))

        cls._setup_field_environment(stack_level+1, env or {})
        type_hints = typing.get_type_hints(cls, cls._field_environment)

        dataclass_fields.extend(dataclasses.fields(cls))  # noqa

        for f in dataclass_fields:
            if f.name in cls._skip_fields:
                continue
            constance = util.make_constance(type_hints.get(f.name))
            f.metadata = dict(
                **f.metadata,
                constance=constance,
                construct=util.get_field_construct(
                    constance, f.name
                )
            )
            data_fields.append(f)

    def __post_init__(self):
        for f in getattr(self, _constants.DATA_FIELDS_ATTR):
            constance = f.metadata['constance']
            value = util.initialize_constance(constance, getattr(self, f.name))
            object.__setattr__(self, f.name, value)

    @classmethod
    def _setup_field_environment(cls, stack_level=2, user_env=None):
        env = {}
        if stack_level is not None:
            frame = inspect.stack()[stack_level].frame
            env.update(frame.f_locals)
            env.update(frame.f_globals)
        if user_env:
            env.update(user_env)
        if cls._field_environment is None:
            cls._field_environment = {}
        cls._field_environment.update(env)

    def _get_data_for_building(self):
        data = dataclasses.asdict(self)  # noqa
        for skip_field in self._skip_fields:
            with contextlib.suppress(KeyError):
                del data[skip_field]
        return data

    @classmethod
    def _extraction_operator(cls, item):
        if len(item) == 1:
            count, = item
            return Array.of(cls, count=count)
        return super()._extraction_operator(item)

    def __bytes__(self):
        return self.build()

    def __iter__(self):
        yield from self._get_data_for_building()

    @classmethod
    def subconstance(cls, subconstance_cls, /, **kwds):
        return subconstance(cls, subconstance_cls, **kwds)

    @classmethod
    def construct(cls):
        fields = map(util.call_construct_method, getattr(cls, _constants.DATA_FIELDS_ATTR))
        return cls._impl(*fields)

    @classmethod
    def load(cls, data, **kwargs):
        construct = cls.construct()
        args = construct.parse(data)
        return cls._load_from_args(args, **kwargs)

    @classmethod
    def _load_from_args(cls, args, **kwargs):
        private_entries = _DataPrivateEntries()
        init = private_entries.update(args)
        instance = cls(**init, **kwargs)
        private_entries.set_payload(instance)
        return instance

    def build(self, **context):
        construct = self.construct()
        return construct.build(self._get_data_for_building(), **context)


@dataclasses.dataclass
class _DataPrivateEntries:
    payload: dataclasses.InitVar[Data] = None
    entries: dict = dataclasses.field(default_factory=dict)
    _payload = None

    def __post_init__(self, payload: Data):
        if payload is None:
            return
        self.set_payload(payload)

    def set_payload(self, payload: Data):
        self._payload = weakref.ref(payload)

    def update(self, container: _lib.Container):
        init = {}
        for key, value in container.items():
            if key.startswith('_'):
                self.entries[key] = value
            else:
                init[key] = value
        return init


class Subconstance(Composite):
    _impl = None

    @classmethod
    def _extraction_operator(cls, args):
        return cls.subconstruct(args)

    @classmethod
    def construct(cls):
        raise TypeError(f'{cls.__name__} can only be used with .of() or []: {cls.__name__}[...]')

    @classmethod
    def subconstruct(cls, *args, **kwargs):
        return Subconstruct(
            cls.__name__,
            factory=cls._impl,
            args=args,
            kwargs=kwargs
        ).construct()

    @staticmethod
    def map_kwargs(kwargs):
        return kwargs

    @classmethod
    def init(cls, constance_cls, instance, *args, **kwargs):
        instance.__bound__ = bound = constance_cls(*args, **kwargs)
        return bound if isinstance(constance_cls, Atomic) else bound._get_data_for_building()

    @classmethod
    def load(cls, subconstance_cls, constance_cls, args, **kwargs):
        return subconstance_cls(*args, **kwargs)

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, instance=None, **kwds):
        return (
            bound_subconstance.type_name
            + (f'({instance.__bound__})' if instance is not None else '')
        )

    @staticmethod
    def iter(instance):
        yield from instance._get_data_for_building()

    @classmethod
    def of(cls, constance=None, **kwargs):
        if constance is None:
            return functools.partial(cls.of, **kwargs)
        constance = util.make_constance(constance)
        kwargs = cls.map_kwargs(kwargs)
        return constance.subconstance(cls, **kwargs)


def subconstance(constance_cls, subconstance_cls: type[Subconstance], /, **kwds):
    class SubconstanceMeta(type):
        _type_name = None

        @property
        def type_name(self):
            if not self._type_name:
                self._type_name = subconstance_cls.__name__
                type_name = getattr(constance_cls, 'type_name', constance_cls.__name__)
                fmt = filter(None, (
                    type_name,
                    ', '.join(
                        f'{key!s}={value!r}'
                        for key, value in kwds.items())
                ))
                self._type_name += ', '.join(fmt)
                self._type_name = self._type_name.join('<>')
            return self._type_name if self == BoundSubconstance else self.__name__

        def __repr__(self):
            return self.type_name

    class BoundSubconstance(Data, metaclass=SubconstanceMeta):
        _skip_fields = ['__build_bound__']
        _dataclass_params = {'init': False, 'repr': False}
        __build_bound__: typing.Any

        def __init__(self, *args, **kwargs):
            self.__build_bound__ = subconstance_cls.init(
                constance_cls, self, *args, **kwargs
            )

        def _get_data_for_building(self):
            return self.__build_bound__

        @classmethod
        def construct(cls):
            return subconstance_cls.subconstruct(
                subcon=util.call_construct_method(constance_cls), **kwds
            )

        @classmethod
        def _load_from_args(cls, args, **kwargs):
            return subconstance_cls.load(cls, constance_cls, args, **kwargs)

        @classmethod
        def subconstance(cls, outer_wrapper_cls, /, **kwargs):
            return subconstance(cls, outer_wrapper_cls, **kwargs)

        def __iter__(self):
            yield from subconstance_cls.iter(self)

        def __repr__(self):
            return subconstance_cls.repr(
                constance_cls,
                bound_subconstance=type(self),
                instance=self, **kwds
            )

    return BoundSubconstance


class Generic:
    def __init__(self, python_type=None):
        self._python_type = python_type

    def __call__(self, args, *, count=None):
        if len(args) == 1:
            constance = util.make_constance(*args)
        else:
            args = list(map(util.ensure_construct, args))
            if len(set(args)) > 1:
                return Atomic(_lib.Sequence(*args), python_type=self._python_type)
            constance = Atomic(args[0])

        if count is None:
            return Atomic(
                _lib.GreedyRange(util.call_construct_method(constance)),
                python_type=self._python_type
            )

        return Atomic(
            _lib.Array(count, util.call_construct_method(constance)),
            python_type=self._python_type
        )


class Struct(Data):
    _impl = _lib.Struct


class BitStruct(Data):
    _impl = _lib.BitStruct


class Sequence(Data):
    _impl = _lib.Sequence

    fields = None

    @classmethod
    def _load_from_args(cls, args, **kwargs):
        instance = cls(*args, **kwargs)
        return instance

    @classmethod
    def _autocreate_field_name(cls, _f, i):
        return f'field_{i}'

    def _get_data_for_building(self):
        return list(super()._get_data_for_building().values())

    def __getitem__(self, item):
        return list(self)[item]

    def __iter__(self):
        yield from self._get_data_for_building()

    def __init_subclass__(cls, stack_level=1, env=None, extends=_MISSING_EXTENDS):
        if extends is _MISSING_EXTENDS:
            extends = cls.__base__
        super_fields = (
            (getattr(extends, 'fields', None) or ())
            if extends is not None else ()
        )
        fields = [*super_fields, *(cls.fields or ())]

        orig_annotations = cls.__annotations__
        cls.__annotations__ = {
            name: (
                f.metadata.get('constance') or f.type
                if isinstance(f, dataclasses.Field) else f
            )
            for i, f in enumerate(fields, start=1)
            if (name := getattr(f, 'name', cls._autocreate_field_name(f, i))) != 'fields'
        }
        env.update(vars(cls))

        try:
            super().__init_subclass__(stack_level+1, env)
        finally:
            cls.__annotations__ = orig_annotations


def field(name, constance, **kwargs) -> dataclasses.Field:
    metadata = kwargs.setdefault('metadata', {})
    metadata.update(constance=constance)
    f = dataclasses.field(**kwargs)
    f.name = name
    return f


class ArrayLike(Subconstance):
    @staticmethod
    def init(constance_cls, instance, *inits):
        instance.__bound__ = [
            (
                init if (isinstance(constance_cls, type) and isinstance(init, constance_cls))
                else util.initialize_constance(constance_cls, init)
            )
            for init in inits
        ]
        if isinstance(constance_cls, Atomic):
            return copy.deepcopy(instance.__bound__)
        return [member._get_data_for_building() for member in instance.__bound__]

    @staticmethod
    def load(subconstance_cls, constance_cls, args, **kwargs):
        return subconstance_cls(*(
            constance_cls(sub_args)
            if isinstance(constance_cls, Atomic)
            else constance_cls._load_from_args(sub_args, **kwargs)
            for sub_args in args
        ))

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, instance=None, **kwds):
        return super().repr(constance_cls, bound_subconstance, **kwds) + (
            ', '.join(map(repr, instance.__bound__)).join('()')
            if instance is not None else ''
        )

    @staticmethod
    def iter(instance):
        yield from instance.__bound__


class Array(ArrayLike):
    _impl = _lib.Array

    @classmethod
    def _extraction_operator(cls, args):
        return cls.subconstruct(args)


class LazyArray(ArrayLike):
    _impl = _lib.LazyArray


class GreedyRange(ArrayLike):
    _impl = _lib.GreedyRange


class Prefixed(Subconstance):
    _impl = _lib.Prefixed

    @staticmethod
    def map_kwargs(kwargs):
        kwargs.update(lengthfield=util.ensure_construct(kwargs.get('lengthfield')))
        return kwargs


class Rebuild(Subconstance):
    _impl = _lib.Rebuild


class Default(Subconstance):
    _impl = _lib.Default

    @classmethod
    def init(cls, constance_cls, instance, *args, **kwargs):
        instance.__bound__ = bound_subconstance = None
        if args or kwargs:
            bound_subconstance = super().init(constance_cls, instance, *args, **kwargs)
        return bound_subconstance


class Optional(Subconstance):
    _impl = _lib.Optional


class Pointer(Subconstance):
    _impl = _lib.Pointer


class Peek(Subconstance):
    _impl = _lib.Peek


class Padded(Subconstance):
    _impl = _lib.Padded
