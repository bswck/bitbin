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

    'Array',
    'ArrayLike',

    'field',
)


MISSING_CAST = object()
MISSING_EXTENDS = object()
MISSING_MAPPER = object()
MISSING_LAMBDA = object()


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
    def __init__(self, construct, python_type=None, cast=MISSING_CAST):
        self._construct = construct
        self._python_type = python_type
        if cast is MISSING_CAST:
            cast = python_type
        self._cast = typing.cast(typing.Callable, cast)

    @property
    def type_name(self):
        return self._python_type.__name__ if self._python_type else type(self._construct).__name__

    def construct(self):
        return self._construct

    def subconstance(self, subconstance_cls, *args, **kwargs):
        return subconstance(self, subconstance_cls, *args, **kwargs)

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
            guilty = None
            if self._cast:
                guilty = exc
            raise err from guilty

    def __getitem__(self, count):
        return Array.of(self, count=count)

    def __repr__(self):
        return f'{type(self).__name__}({type(self._construct).__name__})'


class SubconstructArgumentManager:
    args = None
    kwargs = None

    def __init__(
            self,
            factory,
            name,
            args,
            kwargs,
            mapper=None,
    ):
        self.name = name
        self.factory = factory
        self.mapper = mapper
        self.manage_arguments(args, kwargs)

    def manage_arguments(self, args, kwargs):
        if not self.mapper:
            self.args = args
            self.kwargs = kwargs
            return
        signature = inspect.signature(self.factory)
        try:
            bound_args = signature.bind(*args, **kwargs)
        except TypeError as exc:
            raise TypeError(
                f'error during validating arguments passed to {self.name}.of() or {self.name}[]\n'
                f'Signature: {signature}\n'
                f'Check help({self.factory.__module__}.{self.factory.__qualname__}) '
                'for details on proper use.'
            ) from exc
        arguments = bound_args.arguments
        bound_args.arguments = self.mapper(arguments)
        self.args = bound_args.args
        self.kwargs = bound_args.kwargs


class Subconstruct(Constance):
    _argument_manager_cls = SubconstructArgumentManager

    def __init__(
            self,
            name=None, /, *,
            factory,
            args=(),
            kwargs=None,
            python_type=None,
            mapper=None,
    ):
        self._name = name or (
            factory.__name__ if isinstance(factory, type) else type(factory).__name__
        )
        self._factory = factory

        mgr = self._argument_manager_cls(factory, name, args, kwargs, mapper)
        self._args = mgr.args
        self._kwargs = mgr.kwargs

        self._python_type = python_type

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


class LazyDataProxy:
    def __init__(self, data_cls, container, kwargs):
        self.__cls = data_cls
        self.__container = container
        self.__kwargs = kwargs
        self.__obj = None

    def _wake_up(self):
        if self.__obj is None:
            self.__obj = self.__cls._eager_load(self.__container, **self.__kwargs)

    def __getattr__(self, item):
        self._wake_up()
        return getattr(self.__obj, item)

    def __call__(self):
        self._wake_up()
        return self.__obj

    def __repr__(self):
        if self.__obj is None:
            return f'LazyData<{self.__cls}>(?)'
        return repr(self.__obj)


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
    _lazy_proxy_cls = LazyDataProxy

    def __post_init__(self):
        for f in getattr(self, _constants.FIELDS):
            constance = f.metadata['constance']
            value = util.initialize_constance(constance, getattr(self, f.name))
            object.__setattr__(self, f.name, value)

    def __init_subclass__(cls, stack_level=1, env=None, extends=MISSING_EXTENDS):
        data_fields = []
        setattr(cls, _constants.FIELDS, data_fields)

        if extends is MISSING_EXTENDS:
            extends = cls.__base__

        dataclass_fields = []
        dataclasses.dataclass(cls, **(cls._dataclass_params or {}))

        cls._configure_annotations(extends)
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

    @classmethod
    def _configure_annotations(cls, extends=None):
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
    def subconstance(cls, subconstance_cls, *args, **kwargs):
        return subconstance(cls, subconstance_cls, *args, **kwargs)

    @classmethod
    def construct(cls):
        fields = map(util.call_construct_method, getattr(cls, _constants.FIELDS))
        return cls._impl(*fields)

    @classmethod
    def load(cls, data, **kwargs):
        construct = cls.construct()
        container = construct.parse(data)
        return cls._load(container, **kwargs)

    @classmethod
    def _load(cls, container, **kwargs):
        if isinstance(container, (_lib.LazyContainer, _lib.LazyListContainer)):
            return cls._lazy_proxy_cls(cls, container, kwargs)
        return cls._eager_load(container, **kwargs)

    @classmethod
    def _eager_load(cls, container, **kwargs):
        private_entries = _DataPrivateEntries()
        init = private_entries.update(container)
        instance = cls(**init, **kwargs)
        private_entries.set_constance(instance)
        return instance

    def build(self, **context):
        construct = self.construct()
        return construct.build(self._get_data_for_building(), **context)


@dataclasses.dataclass
class _DataPrivateEntries:
    constance: dataclasses.InitVar[Data] = None
    entries: dict = dataclasses.field(default_factory=dict)
    _constance = None

    def __post_init__(self, constance: Data):
        if constance is None:
            return
        self.set_constance(constance)

    def set_constance(self, constance: Data):
        self._constance = weakref.ref(constance)

    def update(self, container: _lib.Container):
        init = {}
        for key, value in container.items():
            if key.startswith('_'):
                self.entries[key] = value
            else:
                init[key] = value
        return init


class FieldListData(Data):
    fields = None

    def __init_subclass__(cls, stack_level=1, env=None, extends=MISSING_EXTENDS):
        if extends is MISSING_EXTENDS:
            extends = cls.__base__
        orig_annotations = cls.__annotations__
        cls.__annotations__ = {
            name: (
                auto_field.metadata.get('constance') or auto_field.type
                if isinstance(auto_field, dataclasses.Field) else auto_field
            )
            for idx, auto_field in enumerate(cls._resolve_fields(extends), start=1)
            if (
               name := getattr(auto_field, 'name', cls._autocreate_field_name(auto_field, idx))
            ) != 'fields'
        }

        try:
            super().__init_subclass__(stack_level+1, env)
        finally:
            cls.__annotations__ = orig_annotations

    def __getitem__(self, item):
        seq = list(self)
        return seq[item]

    def __iter__(self):
        yield from self._get_data_for_building()

    @classmethod
    def _eager_load(cls, container, **kwargs):
        return cls(*container, **kwargs)

    @classmethod
    def _resolve_fields(cls, extends=None):
        super_fields = getattr(extends, 'fields', None) or ()
        fields = [*super_fields, *(cls.fields or ())]
        return fields

    @classmethod
    def _autocreate_field_name(cls, _f, i):
        return f'field_{i}'

    def _get_data_for_building(self):
        return list(super()._get_data_for_building().values())

    @classmethod
    def from_fields(cls, fields, name=None):
        return type(name or cls.__name__, (cls,), {'fields': fields})

    @classmethod
    def add_field(cls, f):
        cls.fields.append(f)
        cls.__init_subclass__(stack_level=2)

    @classmethod
    def remove_field(cls, f):
        cls.fields.remove(f)
        cls.__init_subclass__(stack_level=2)


class MaybeConstructLambda:
    def __init__(self, context_lambda):
        self.context_lambda = context_lambda
        if callable(context_lambda):
            self.ret = MISSING_LAMBDA
        else:
            self.ret = util.ensure_construct(context_lambda)

    def __call__(self, *args, **kwargs):
        if self.ret is not MISSING_LAMBDA:
            return self.ret
        return util.ensure_construct(self.context_lambda(*args, **kwargs))


class Subconstance(Composite):
    _impl = None
    _subconstruct_cls = Subconstruct
    # _argument_manager_cls = SubconstructArgumentManager

    @classmethod
    def _extraction_operator(cls, args):
        return cls.subconstruct(MISSING_MAPPER, *args)

    @classmethod
    def construct(cls):
        raise TypeError(f'{cls.__name__} can only be used with .of() or []: {cls.__name__}[...]')

    @classmethod
    def subconstruct(cls, mapper, /, *args, **kwargs):
        return cls._subconstruct_cls(
            cls.__name__,
            factory=cls._impl,
            args=args,
            kwargs=kwargs,
            mapper=cls.map_arguments if mapper is MISSING_MAPPER else mapper,
        ).construct()

    @staticmethod
    def map_arguments(arguments):
        arguments.update(subcon=util.ensure_construct_or_none(arguments['subcon']))
        return arguments

    @classmethod
    def init(cls, constance_cls, instance, *args, **kwargs):
        instance.__bound__ = bound = constance_cls(*args, **kwargs)
        return bound if isinstance(constance_cls, Atomic) else bound._get_data_for_building()

    @classmethod
    def load(cls, subconstance_cls, constance_cls, args, **kwargs):
        return subconstance_cls(*args, **kwargs)

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, s_args, s_kwargs, instance=None):
        return (
            bound_subconstance.type_name
            + (f'({instance.__bound__})' if instance is not None else '')
        )

    @staticmethod
    def iter(instance):
        yield from instance._get_data_for_building()

    @classmethod
    def of(cls, constance=None, *args, **kwargs):
        if constance is None:
            return functools.partial(cls.of, *args, **kwargs)
        constance = util.make_constance(constance)
        return constance.subconstance(cls, *args, **kwargs)


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
            else constance_cls._load(sub_args, **kwargs)
            for sub_args in args
        ))

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, s_args, s_kwargs, instance=None):
        return super().repr(constance_cls, bound_subconstance, s_args, s_kwargs) + (
            ', '.join(map(repr, instance.__bound__)).join('()')
            if instance is not None else ''
        )

    @staticmethod
    def iter(instance):
        yield from instance.__bound__


class Array(ArrayLike):
    _impl = _lib.Array  # (count, subcon, discard=False)

    @classmethod
    def _extraction_operator(cls, args):
        return cls.subconstruct(MISSING_MAPPER, *args)


def subconstance(constance_cls, subconstance_cls: type[Subconstance], *s_args, **s_kwargs):
    class SubconstanceMeta(type):
        _type_name = None

        @property
        def type_name(self):
            if not self._type_name:
                self._type_name = subconstance_cls.__name__
                type_name = getattr(constance_cls, 'type_name', constance_cls.__name__)
                fmt = filter(None, (
                    type_name,
                    ', '.join(map(repr, s_args)),
                    ', '.join(
                        f'{key!s}={value!r}'
                        for key, value in s_kwargs.items())
                ))
                self._type_name += ', '.join(fmt).join('<>')
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
            s_kwargs.update(subcon=util.call_construct_method(constance_cls))
            return subconstance_cls.subconstruct(MISSING_MAPPER, *s_args, **s_kwargs)

        @classmethod
        def _eager_load(cls, container, **kwargs):
            return subconstance_cls.load(cls, constance_cls, container, **kwargs)

        @classmethod
        def subconstance(cls, outer_subconstance_cls, /, **kwargs):
            return subconstance(cls, outer_subconstance_cls, **kwargs)

        def __iter__(self):
            yield from subconstance_cls.iter(self)

        def __repr__(self):
            return subconstance_cls.repr(
                constance_cls,
                bound_subconstance=type(self),
                instance=self,
                s_args=s_args,
                s_kwargs=s_kwargs
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


def field(name, constance, **kwargs) -> dataclasses.Field:
    metadata = kwargs.setdefault('metadata', {})
    metadata.update(constance=constance)
    f = dataclasses.field(**kwargs)
    f.name = name
    return f
