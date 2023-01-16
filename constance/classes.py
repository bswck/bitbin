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
    'FieldListData',
    'Subconstance',
    'subconstance',
    'Array',
    'ArrayLike',
    'Switch',
    'field',
)


MISSING_CAST = object()
MISSING_EXTENDS = object()
MISSING_MAPPER = object()
MISSING_LAMBDA = object()
MISSING_KEY = object()


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
        return (
            self._python_type.__name__
            if self._python_type
            else type(self._construct).__name__
        )

    def construct(self):
        return self._construct

    def subconstance(self, subconstance_cls, *args, **kwargs):
        return subconstance(self, subconstance_cls, *args, **kwargs)

    def __call__(self, obj, _context=None):
        return self._load(obj)

    def _load(self, obj, context=None):
        if callable(obj):
            return LazyDataProxy(self, obj)
        return self._eager_load(obj, context)

    def _eager_load(self, obj, _context=None):
        if callable(obj):
            obj = obj()
        if self._python_type and isinstance(obj, self._python_type):
            return obj
        try:
            return self._cast(obj)
        except Exception as exc:
            err = TypeError(
                f'cannot cast {obj} to the desired type'
                + (
                    ' ' + self._python_type.__name__.join('()')
                    if self._python_type
                    else ''
                )
            )
            cause = None
            if self._cast:
                cause = exc
            raise err from cause

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
        name=None,
        /,
        *,
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
        raise ValueError(
            f'{cls.__name__}[{", ".join(map(str, args)) or ()}] is undefined'
        )


class LazyDataProxy:
    def __init__(self, constance, argument, context, kwargs):
        self.__constance = constance
        self.__argument = argument
        self.__kwargs = kwargs
        self.__context = context
        self.__object = None

    def _wake_up(self):
        if self.__object is None:
            self.__object = self.__constance._eager_load(
                self.__argument, self.__context, **self.__kwargs
            )

    def __getattr__(self, item):
        self._wake_up()
        return getattr(self.__object, item)

    def __call__(self):
        self._wake_up()
        return self.__object

    def __repr__(self):
        if self.__object is None:
            return f'<lazy instance of {self.__constance}>'
        return repr(self.__object)


def _load_into(cls, container, context=None, **kwargs):
    if isinstance(container, (_lib.LazyContainer, _lib.LazyListContainer)):
        return cls._lazy_load(cls, container, context, kwargs)
    return cls._eager_load(container, context, **kwargs)


class Data(Composite):
    """
    A composite Constance that represents data.
    Uses `dataclasses` in the background for managing the data fields.
    """

    _impl = None
    _field_environment = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _skip_fields = None  # type: typing.ClassVar[list[str]]
    _dataclass_params = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _default_context = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _private_entries = None  # type: _DataPrivateEntries | None
    _container = None  # type: _lib.Container[str, typing.Any] | None
    _field_names = []  # type: typing.ClassVar[list[str]]
    _terminated = False  # type: typing.ClassVar[bool]
    _compiled = False  # type: typing.ClassVar[bool]
    _lazy_load = LazyDataProxy
    _context = _lib.Container()

    def __post_init__(self):
        context = self._container
        fs = getattr(self, _constants.FIELDS)

        if not fs and self._container:
            raise TypeError(f'{type(self).__name__} stores no data')

        for f in fs:
            constance = util.ensure_constance_of_field(f)
            if not context:
                context = _lib.Container(self._data_for_building())
            context['_'] = self._context
            value = util.initialize_constance(constance, getattr(self, f.name), context)
            object.__setattr__(self, f.name, value)

    def __init_subclass__(
        cls,
        stack_level=1,
        env=None,
        extends=MISSING_EXTENDS,
        terminated=None,
        compiled=None,
    ):
        data_fs = []
        setattr(cls, _constants.FIELDS, data_fs)

        if extends is MISSING_EXTENDS:
            extends = cls.__base__

        fs = []
        dataclasses.dataclass(cls, **(cls._dataclass_params or {}))

        cls._configure_annotations(extends)
        cls._setup_field_environment(stack_level + 1, env or {})

        type_hints = typing.get_type_hints(cls, cls._field_environment)

        fs.extend(dataclasses.fields(cls))  # noqa

        for f in fs:
            if f.name in cls._skip_fields:
                continue
            constance = util.make_constance(type_hints.get(f.name))
            f.metadata = dict(**f.metadata, constance=constance)
            data_fs.append(f)

        cls._setup_default_context(extends)

        if terminated is not None:
            cls._terminated = terminated

        if compiled is not None:
            cls._compiled = compiled

    @classmethod
    def _configure_annotations(cls, extends=None):
        if cls._field_names is not None:

            cls._field_names = [
                *(getattr(extends, '_field_names', None) or [] if extends else []),
                *cls._field_names,
            ]
            cls._skip_fields = [
                *(getattr(extends, '_skip_fields', None) or [] if extends else []),
                *(cls._skip_fields or []),
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

    @classmethod
    def _setup_default_context(cls, extends=None):
        default_context = cls._default_context
        if default_context is None:
            default_context = {}
        cls._default_context = {
            **(getattr(extends, '_default_context', None) or {}),
            **default_context,
        }

    def _set_defaults(self, **context):
        self._default_context.update(context)

    def _data_for_building(self):
        data = util.traverse_data_for_building(self, recursive=False)
        for f in self._skip_fields:
            with contextlib.suppress(KeyError):
                del data[f]
        return data

    @classmethod
    def _extraction_operator(cls, item):
        if len(item) == 1:
            (count,) = item
            return Array.of(cls, count=count)
        return super()._extraction_operator(item)

    def __bytes__(self):
        return self.build(**self._default_context)

    def __iter__(self):
        yield from self._data_for_building()

    @classmethod
    def subconstance(cls, subconstance_cls, *args, **kwargs):
        return subconstance(cls, subconstance_cls, *args, **kwargs)

    @classmethod
    def construct(cls):
        fs = (
            util.get_field_construct(util.ensure_constance_of_field(f), name=f.name)
            for f in getattr(cls, _constants.FIELDS)
        )
        if cls._terminated:
            impl = cls._impl(*fs, _lib.Terminated)
        else:
            impl = cls._impl(*fs)
        if cls._compiled:
            impl = impl.compile()
        return impl

    @classmethod
    def load(cls, data, **kwargs):
        construct = cls.construct()
        container = construct.parse(data)
        return cls._load(container, **kwargs)

    @classmethod
    def _load(cls, container, context=None, /, **kwargs):
        return _load_into(cls, container, context, **kwargs)

    @classmethod
    def _eager_load(cls, container, context=None, /, **custom_kwargs):
        private_entries = _DataPrivateEntries()
        if isinstance(container, dict):
            args = ()
            container = private_entries.update(container)
            kwargs = container
        else:
            kwargs = {}
            args = container
        instance = object.__new__(cls)
        if callable(getattr(container, 'items', None)):
            instance._container = _lib.Container(container)
        instance._context = context
        instance.__init__(*args, **kwargs, **custom_kwargs)
        private_entries.set_constance(instance)
        instance._private_entries = private_entries
        return instance

    def build(self, **spec_context):
        construct = self.construct()
        context = {**self._default_context, **spec_context}
        return construct.build(self._data_for_building(), **context)


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


class FieldHolder(list):
    def __init__(self, init_list=None):
        super().__init__(init_list)
        self._fields_by_name = {}
        self._annotations = {}

        for idx, f in enumerate(self):
            self._process_field(f, idx)

    def _process_field(self, f, idx):
        anns = self._annotations
        name = getattr(f, 'name', None) or self._autocreate_field_name(f, idx)
        if isinstance(f, dataclasses.Field):
            anns[name] = f.metadata.get('constance') or f.type
            f.name = name
            self._fields_by_name[name] = f
        else:
            anns[name] = f
            self._fields_by_name[name] = field(name, f)

    def append(self, f):
        super().append(f)
        self._process_field(f, len(self) - 1)

    def remove(self, f):
        super().remove(f)
        del self._annotations[f.name], self._fields_by_name[f.name]

    def _get_fields(self):
        return list(self._fields_by_name.values())

    @staticmethod
    def _autocreate_field_name(_f, i):
        return f'field_{i}'

    def _emulate_annotations(self):
        return self._annotations

    def __getattr__(self, item):
        try:
            return self._fields_by_name[item]
        except KeyError:
            raise AttributeError(
                f'{type(self).__name__!r} object has no attribute {item!r}'
            ) from None


class FieldListData(Data):
    fields = None
    field_holder_cls = FieldHolder

    def __init_subclass__(
        cls,
        stack_level=1,
        env=None,
        extends=MISSING_EXTENDS,
        terminated=None,
        compiled=None,
    ):
        if extends is MISSING_EXTENDS:
            extends = cls.__base__
        orig_annotations = cls.__annotations__

        fs = cls.fields = cls._resolve_fields(extends)

        cls.__annotations__ = fs._emulate_annotations()
        try:
            super().__init_subclass__(
                stack_level=stack_level + 1,
                env=env,
                extends=extends,
                terminated=terminated,
                compiled=compiled,
            )
        finally:
            cls.__annotations__ = orig_annotations

    def __getitem__(self, item):
        return [*self][item]

    def __iter__(self):
        yield from self._data_for_building()

    @classmethod
    def _eager_load(cls, container, _context=None, /, **custom_kwargs):
        return cls(*container, **custom_kwargs)

    @classmethod
    def _resolve_fields(cls, extends=None):
        sfs = getattr(extends, 'fields', None) or ()
        fs = [*sfs, *(cls.fields or ())]
        return FieldHolder(fs)

    @classmethod
    def from_fields(cls, fields, name=None):
        return type(name or cls.__name__, (cls,), {'fields': fields})

    @classmethod
    def add_field(cls, f):
        cls.fields.append(f)

    @classmethod
    def remove_field(cls, f):
        cls.fields.remove(f)

    @classmethod
    def construct(cls):
        fs = (
            util.get_field_construct(util.ensure_constance_of_field(f), name=f.name)
            for f in cls.fields._fields_by_name.values()
        )
        return cls._impl(*fs)


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
        raise TypeError(
            f'{cls.__name__} can only be used with .of() or []: {cls.__name__}[...]'
        )

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
        return (
            bound
            if isinstance(constance_cls, Atomic)
            else bound.traverse_data_for_building()
        )

    @classmethod
    def load(cls, subconstance_cls, constance_cls, args, **kwargs):
        return subconstance_cls(*args, **kwargs)

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, s_args, s_kwargs, instance=None):
        return bound_subconstance.type_name + (
            f'({instance.__bound__})' if instance is not None else ''
        )

    @staticmethod
    def iter(instance):
        yield from instance.traverse_data_for_building()

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
                init
                if (isinstance(constance_cls, type) and isinstance(init, constance_cls))
                else util.initialize_constance(constance_cls, init)
            )
            for init in inits
        ]
        if isinstance(constance_cls, Atomic):
            return copy.deepcopy(instance.__bound__)
        return [member._data_for_building() for member in instance.__bound__]

    @staticmethod
    def load(subconstance_cls, constance_cls, args, **kwargs):
        return subconstance_cls(
            *(
                util.initialize_constance(
                    constance_cls, sub_args, subconstance_cls, **kwargs
                )
                for sub_args in args
            )
        )

    @classmethod
    def repr(cls, constance_cls, bound_subconstance, s_args, s_kwargs, instance=None):
        return super().repr(constance_cls, bound_subconstance, s_args, s_kwargs) + (
            ', '.join(map(repr, instance.__bound__)).join('()')
            if instance is not None
            else ''
        )

    @staticmethod
    def iter(instance):
        yield from instance.__bound__


class Array(ArrayLike):
    _impl = _lib.Array  # (count, subcon, discard=False)

    @classmethod
    def _extraction_operator(cls, args):
        return cls.subconstruct(MISSING_MAPPER, *args)


def subconstance(
    constance_cls, subconstance_cls: type[Subconstance], *s_args, **s_kwargs
):
    class SubconstanceMeta(type):
        _type_name = None

        @property
        def type_name(self):
            if not self._type_name:
                self._type_name = subconstance_cls.__name__
                type_name = getattr(constance_cls, 'type_name', constance_cls.__name__)
                fmt = filter(
                    None,
                    (
                        type_name,
                        ', '.join(map(repr, s_args)),
                        ', '.join(
                            f'{key!s}={value!r}' for key, value in s_kwargs.items()
                        ),
                    ),
                )
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

        def _data_for_building(self):
            return self.__build_bound__

        @classmethod
        def construct(cls):
            s_kwargs.update(subcon=constance_cls.construct())
            return subconstance_cls.subconstruct(MISSING_MAPPER, *s_args, **s_kwargs)

        @classmethod
        def _eager_load(cls, container, _context=None, /, **custom_kwargs):
            return subconstance_cls.load(cls, constance_cls, container, **custom_kwargs)

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
                s_kwargs=s_kwargs,
            )

    return BoundSubconstance


class ConstructCaseDict(dict):
    def values(self):
        yield from map(util.ensure_construct, super().values())

    def items(self):
        return zip(self.keys(), self.values())

    def __getitem__(self, item):
        return util.ensure_construct(super().__getitem__(item))

    def get(self, item, default=None):
        return util.ensure_construct_or_none(super().get(item, default))


class Switch(Constance):
    """Port to construct.Switch"""

    _impl = _lib.Switch  # (keyfunc, cases, default=None)
    _lazy_load = LazyDataProxy
    cases = None

    @classmethod
    def construct(cls):
        return cls._impl(cls.key, ConstructCaseDict(cls.cases), cls.default())

    @classmethod
    def default(cls):
        return _lib.Error

    @classmethod
    def key(cls, context):
        raise NotImplementedError

    @classmethod
    def autokey(cls, _constance_cls):
        return len(cls.cases)

    @classmethod
    def register(cls, key=MISSING_KEY, constance_cls=None):
        if constance_cls is None:
            return lambda constance: cls.register(key, constance)
        constance_cls = util.make_constance(constance_cls)
        if key is MISSING_KEY:
            key = cls.autokey(constance_cls)
        if key in cls.cases:
            return cls._register_overload(key, constance_cls)
        cls.cases[key] = constance_cls
        return constance_cls

    @classmethod
    def _register_overload(cls, key, constance_cls):
        from constance.core import Select

        overload_case = cls.cases[key]
        if not (isinstance(overload_case, type) and issubclass(overload_case, Select)):
            overload_case = Select.from_fields(
                [overload_case], name=f'Select_{cls.__name__}_overloads_{key}'
            )
            cls.cases[key] = overload_case
        if constance_cls in overload_case.fields:
            return constance_cls
        overload_case.add_field(constance_cls)
        return constance_cls

    @classmethod
    def _load(cls, container, context=None, /, **kwargs):
        return _load_into(cls, container, context, **kwargs)

    @classmethod
    def _eager_load(cls, container, context=None, /, **kwargs):
        return util.initialize_constance(
            cls.cases[cls.key(context)], container, **kwargs
        )

    def __init_subclass__(cls, stack_level=1, extends=MISSING_EXTENDS):
        if extends is MISSING_EXTENDS:
            extends = cls.__base__
        cases = cls.cases
        if cases is None:
            cases = {}
        cls.cases = {**(getattr(extends, 'cases', None) or {}), **cases}


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
                _lib.GreedyRange(constance.construct()), python_type=self._python_type
            )

        return Atomic(
            _lib.Array(count, constance.construct()), python_type=self._python_type
        )


# def sanitize_field_name(constance, name):
#     return f'f_{name}'


def field(name, constance, **kwargs) -> dataclasses.Field:
    metadata = kwargs.setdefault('metadata', {})
    metadata.update(constance=constance)
    # metadata.update(orig_name=name)
    f = dataclasses.field(**kwargs)
    f.name = name
    # f.name = sanitize_field_name(name)
    f.metadata = dict(f.metadata)
    return f
