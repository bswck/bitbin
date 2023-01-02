import collections
import contextlib
import dataclasses
import functools
import typing
import weakref

import construct as _lib

from constance import _constants
from constance import api
from constance import util


__all__ = (
    'Data',
    'Modifier',
    'modify',
)

MISSING_EXTENDS = object()


class Data(api.Composite):
    """
    A composite Constance that represents data.
    Uses `dataclasses` in the background for managing the data fields.
    """

    _impl = None  # type: typing.ClassVar[type[api.Constance] | None]
    _field_environment = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _skip_fields = None  # type: typing.ClassVar[list[str]]
    _field_names = []  # type: typing.ClassVar[list[str]]
    _dataclass_params = None

    def __init_subclass__(cls, extends=MISSING_EXTENDS, **declaration_env):
        data_fields = []
        setattr(cls, _constants.DATA_FIELDS_ATTR, data_fields)

        if extends is MISSING_EXTENDS:
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

        cls._setup_field_environment(declaration_env)
        type_hints = typing.get_type_hints(cls, cls._field_environment)

        dataclass_fields.extend(dataclasses.fields(cls))  # noqa
        for field in dataclass_fields:
            if field.name in cls._skip_fields:
                continue
            constance = util.make_constance(type_hints.get(field.name))
            field.metadata = dict(
                **field.metadata,
                constance=constance,
                construct=util.get_field_construct(
                    constance, field.name
                )
            )
            data_fields.append(field)

    def __post_init__(self):
        for field in getattr(self, _constants.DATA_FIELDS_ATTR):
            constance = field.metadata['constance']
            value = util.initialize_constance(constance, getattr(self, field.name))
            object.__setattr__(self, field.name, value)

    @classmethod
    def _setup_field_environment(cls, declaration_env):
        env = {}
        if declaration_env:
            env.update(declaration_env)
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
    def _class_getitem(cls, item):
        from constance.modifiers import Array

        if len(item) == 1:
            count, = item
            return Array.of(cls, count=count)
        return super()._class_getitem(item)

    def __bytes__(self):
        return self.build()

    def __iter__(self):
        yield from self._get_data_for_building()

    @classmethod
    def modify(cls, wrapper_cls, /, **kwds):
        return modify(cls, wrapper_cls, **kwds)

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


class Modifier(api.Composite):
    _impl = None

    @classmethod
    def construct(cls):
        raise TypeError(f'{cls.__name__} can only be used with []: {cls.__name__}[...]')

    @classmethod
    def _class_getitem(cls, args):
        return cls.subconstruct(args)

    @classmethod
    def subconstruct(cls, *args, **kwargs):
        return api.SubconstructAlias(
            cls.__name__,
            factory=cls._impl, 
            args=args, 
            kwargs=kwargs
        ).construct()

    @staticmethod
    def map_kwargs(kwargs):
        return kwargs

    @classmethod
    def init(cls, inner_cls, instance, *args, **kwargs):
        instance.__modified__ = modified = inner_cls(*args, **kwargs)
        return modified if isinstance(inner_cls, api.Atomic) else modified._get_data_for_building()

    @classmethod
    def load(cls, outer_cls, inner_cls, args, **kwargs):
        return outer_cls(*args, **kwargs)

    @classmethod
    def repr(cls, inner_cls, modified_type, instance=None, **kwds):
        return (
            modified_type.type_name
            + (f'({instance.__modified__})' if instance is not None else '')
        )

    @staticmethod
    def iter(instance):
        yield from instance._get_data_for_building()

    @classmethod
    def of(cls, payload=None, **kwargs):
        if payload is None:
            return functools.partial(cls.of, **kwargs)
        return util.make_constance(payload).modify(cls, **cls.map_kwargs(kwargs))


def modify(inner_cls, outer_cls: type[Modifier], /, **kwds):

    class ModifiedDataType(type):
        _type_name = None

        @property
        def type_name(self):
            if not self._type_name:
                self._type_name = (
                    outer_cls.__name__
                    + (
                        ', '.join(
                            filter(None, (
                                getattr(inner_cls, 'type_name', inner_cls.__name__),
                                ', '.join(
                                    f'{key!s}={value!r}'
                                    for key, value in kwds.items())
                            ))
                        )
                    ).join('<>')
                )
            return self._type_name if self == ModifiedData else self.__name__

        def __repr__(self):
            return self.type_name

    class ModifiedData(Data, metaclass=ModifiedDataType):
        _skip_fields = ['__modified_for_building__']
        _dataclass_params = {'init': False, 'repr': False}
        __modified_for_building__: typing.Any

        def __init__(self, *args, **kwargs):
            self.__modified_for_building__ = outer_cls.init(inner_cls, self, *args, **kwargs)

        def _get_data_for_building(self):
            return self.__modified_for_building__

        @classmethod
        def construct(cls):
            return outer_cls.subconstruct(subcon=util.call_construct_method(inner_cls), **kwds)

        @classmethod
        def _load_from_args(cls, args, **kwargs):
            return outer_cls.load(cls, inner_cls, args, **kwargs)

        @classmethod
        def modify(cls, outer_wrapper_cls, /, **kwargs):
            return modify(cls, outer_wrapper_cls, **kwargs)

        def __iter__(self):
            yield from outer_cls.iter(self)

        def __repr__(self):
            return outer_cls.repr(inner_cls, modified_type=type(self), instance=self, **kwds)

    return ModifiedData
