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


class Data(api.Composite):
    """
    A composite Constance that represents data.
    Uses `dataclasses` in the background for managing the data fields.
    """

    _impl = None  # type: typing.ClassVar[type[api.Constance] | None]
    _field_environment = None  # type: typing.ClassVar[dict[str, typing.Any] | None]
    _skip_fields = []  # type: typing.ClassVar[list[str]]

    def __init_subclass__(cls, **declaration_env):
        dataclasses.dataclass(cls)
        payload_fields = []

        cls._setup_field_environment(declaration_env)
        type_hints = typing.get_type_hints(cls, cls._field_environment)

        for field in dataclasses.fields(cls):  # noqa
            if field.name in cls._skip_fields:
                continue
            field.metadata = dict(field.metadata)
            field.metadata['construct'] = functools.partial(
                util.get_construct_method, field, type_hints.get(field.name)
            )
            payload_fields.append(field)

        setattr(cls, _constants.PAYLOAD_FIELDS_ATTR, payload_fields)

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
        fields = map(util.call_construct_method, getattr(cls, _constants.PAYLOAD_FIELDS_ATTR))
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
        self.entries.clear()
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
            name=cls.__name__, 
            factory=cls._impl, 
            args=args, 
            kwargs=kwargs
        ).construct()

    @staticmethod
    def map_kwargs(kwargs):
        return kwargs

    @staticmethod
    def init(inner_cls, instance, *args, **kwargs):
        instance.__modified__ = wrapped = inner_cls(*args, **kwargs)
        return wrapped if isinstance(inner_cls, api.Atomic) else wrapped._get_data_for_building()

    @staticmethod
    def load(outer_cls, inner_cls, args, **kwargs):
        return outer_cls(*args, **kwargs)

    @classmethod
    def repr(cls, inner_cls, instance=None, **kwds):
        return (
            cls.__name__
            + (', '.join(
                filter(None, (
                    inner_cls.type_name
                    if isinstance(inner_cls, api.Atomic)
                    else inner_cls.__name__,
                    ', '.join(
                        f'{key!s}={value!r}'
                        for key, value in kwds.items())
                ))
            )).join('<>')
            + (f'({instance.__inner_payload__})' if instance is not None else '')
        )

    @staticmethod
    def iter(instance):
        yield from instance._get_data_for_building()

    @classmethod
    def of(cls, payload=None, **kwargs):
        if payload is None:
            return functools.partial(cls.of, **kwargs)
        return util.make_constance(payload).modify(cls, **kwargs)


def modify(inner_cls, outer_cls: type[Modifier], /, **kwds):

    class ModifiedDataType(type):
        def __repr__(self):
            return cls_name

    class ModifiedData(Data, metaclass=ModifiedDataType):
        def __init__(self, *args, **kwargs):
            self.__modified__ = outer_cls.init(inner_cls, self, *args, **kwargs)

        def _get_data_for_building(self):
            return self.__modified__

        @classmethod
        def construct(cls):
            return outer_cls.subconstruct(subcon=util.ensure_construct(inner_cls), **kwds)

        @classmethod
        def _load_from_args(cls, args, **kwargs):
            return outer_cls.load(cls, inner_cls, args, **kwargs)

        @classmethod
        def modify(cls, outer_wrapper_cls, /, **kwargs):
            return modify(cls, outer_wrapper_cls, **kwargs)

        def __iter__(self):
            yield from outer_cls.iter(self)

        def __repr__(self):
            return outer_cls.repr(inner_cls, instance=self, **kwds)

    cls_name = outer_cls.repr(inner_cls, **kwds)
    return ModifiedData
