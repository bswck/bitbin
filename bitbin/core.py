from __future__ import annotations

import contextlib
import dataclasses
import functools
import inspect
import typing
from typing import Generic, TypeVar

import construct as _lib

from bitbin import util

__all__ = (
    'load', 'loads',
    'dump', 'dumps',
    'field',
    'AnnotationManager',
    'Model',
    'ModelFeature',
    'ModelDataclass', 'models',
    'StorageBasedModel',
)


def load(model, fp, **context):
    return load(model, fp.read(), **context)


def loads(model, data, **context):
    return model._load(data, context)


def dump(model, fp, *args, **kwargs):
    data = dumps(model, *args, **kwargs)
    fp.write(data)
    return data


missing = dataclasses.MISSING


def dumps(model, initializer=missing, /, **context):
    instance = model
    if initializer is not missing:
        instance = model._init(initializer)
    return instance._dump(**context)


T = TypeVar('T')


class Model(Generic[T]):
    _is_model = True
    _storage_based = False

    def _init(self, data, context=None):
        raise NotImplementedError

    @classmethod
    def _load(cls, data, context):
        raise NotImplementedError

    @classmethod
    def _construct(cls):
        raise NotImplementedError

    @typing.overload
    def _dump(self, obj, **context): ...

    def _dump(self, **context):
        raise NotImplementedError

    @classmethod
    def _sizeof(cls, **context):
        return cls._construct().sizeof(**context)

    @classmethod
    def _fieldhook(cls, f):
        return f


class ModelFeature(Model):
    """Typically links to Subconstruct subclasses"""

    model: typing.Any

    _feature_impl = None
    _obj_type = None
    _pass_context = False

    def __post_init__(self):
        if self.model is not None:
            self.model = util.make_model(self.model)

    @classmethod
    def _initializer(cls, obj):
        return obj

    @classmethod
    def _loader(cls, obj):
        return obj

    def __call__(self, model):
        self.model = util.make_model(self.model)
        return self

    def __class_getitem__(cls, initlist):
        # for nicer annotation syntax :3
        return cls(*initlist)

    def _get_construct_factory(self):
        raise NotImplementedError

    def _get_construct(self, subcon=None):
        factory = self._get_construct_factory()
        if subcon is None:
            subcon = self.model._construct()
        return factory(subcon)

    def _load(self, data, context):
        loaded = self.model._load(data, context)
        if isinstance(loaded, (bytes, bytearray)):
            return self._init(self._construct().parse(loaded, **(context or {})), context)
        return self._loader(loaded, context) if self._pass_context else self._loader(loaded)

    def _init(self, obj, context=None):
        return self._initializer(self.model._init(obj))

    def _construct(self):
        return self._get_construct()

    def _dump(self, obj, **context):
        return self._construct().build(obj, **context)


class Singleton(Model):
    _storage_based = False

    def __init__(self, construct, value):
        self._construct_object = construct
        self._value = value

    def _init(self, _obj=None, _context=None):
        return self._value

    def _load(self, data=None, context=None):
        return self._value

    def _construct(self):
        return self._construct_object

    def _dump(self, obj=None, **context):
        return self._construct().dump()


class Atomic(Model):
    def __init__(
            self,
            lib_object,
            obj_type,
            pass_context=False,
            loader=None,
            initializer=None
    ):
        self._lib_object = lib_object
        self._obj_type = obj_type
        self._loader = loader or obj_type
        self._initializer = initializer or obj_type
        self._pass_context = pass_context

    def _init(self, obj, context=None):
        if isinstance(obj, (bytes, bytearray)):
            return loads(self, obj)
        return self._initializer(obj)

    def _load(self, data, context):
        if isinstance(data, (bytes, bytearray)):
            return self._init(self._lib_object.parse(data))
        return self._loader(data, context) if self._pass_context else self._loader(data)

    def _construct(self):
        return self._lib_object

    def _dump(self, obj, **context):
        return self._lib_object.build(self._init(obj), **context)


@dataclasses.dataclass
class Generic(Model):
    _obj_type: type

    def __call__(self, args, *, count=None):
        if len(args) == 1:
            model = util.make_model(*args)
        else:
            args = [arg._construct() for arg in map(util.make_model, args)]
            if len(set(args)) > 1:
                return Atomic(_lib.Sequence(*args), self._obj_type)
            model = Atomic(args[0])
        if count is None:
            return Atomic(
                _lib.GreedyRange(model._construct()), self._obj_type
            )
        return Atomic(
            _lib.Array(count, model._construct()), self._obj_type
        )


# Dataclasses-related

MISSING = dataclasses.MISSING


def field(
        model=None,
        name=None,
        *,
        default=MISSING,
        default_factory=MISSING,
        **kwargs
):
    # note 1: class.__init_subclass__() may override the field name
    # note 2: model= does not provide type annotation functionality (it's all about the order)
    f = dataclasses.field(default=default, default_factory=default_factory, **kwargs)
    f.name = name
    model = util.make_model(model)
    f.metadata = dict(f.metadata, model=model if model else None)
    model._fieldhook(f)
    return f


def make_field(f=MISSING, *, name, type_hint):
    model = None
    if isinstance(f, dataclasses.Field):
        default = f.default
        default_factory = f.default_factory
        metadata = f.metadata  # type: dict
        model = metadata.pop('model', None)
    else:
        default = f
        default_factory = dataclasses.MISSING
        metadata = {}
    if model is None:
        model = util.make_model(type_hint)
    f = field(
        model, name=name,
        default=default,
        default_factory=default_factory,
        **metadata,
    )
    return f


@dataclasses.dataclass
class AnnotationManager:
    model_dataclass: type[ModelDataclass]

    def __post_init__(self):
        anns = (
            self.model_dataclass._annotations
            or self.model_dataclass.__annotations__
        )
        self._mock_object = type(
            '_AnnotationManagerMockObject',
            (), {'__annotations__': anns}
        )
        self._globals = {}
        self._locals = {}
        self._annotations = anns

    def get_env(self, stack_offset=None):
        global_ns, local_ns = self._globals, self._locals
        if stack_offset is not None:
            frame = inspect.stack()[stack_offset].frame
            global_ns.update(frame.f_globals)
            local_ns.update(frame.f_locals)
        return global_ns, local_ns

    def map_to_fields(self, stack_offset=1):
        global_ns, local_ns = self.get_env(stack_offset+1)
        for name, type_hint in typing.get_type_hints(
                self._mock_object,
                globalns=global_ns,
                localns=local_ns
        ).items():
            missing = object()
            f = self.get_field(name, default=missing)
            if f is missing:
                f = dataclasses.MISSING
            f = make_field(f, name=name, type_hint=type_hint)
            self._annotations[name] = f.metadata['model']
            self.set_field(name, f)
        return self._annotations

    def get_field(self, name, default=MISSING, instance=None):
        target = instance or self.model_dataclass
        return (
            getattr(target, name)
            if default is MISSING else
            getattr(target, name, default)
        )

    def set_field(self, name, value, instance=None):
        target = instance or self.model_dataclass
        setattr(target, name, value)

    @contextlib.contextmanager  # <-- +1 frame
    def replace_annotations(self, stack_offset=1):
        stack_offset += 1  # +1 from the context manager
        old = self.model_dataclass.__annotations__
        self.model_dataclass.__annotations__ = self.map_to_fields(stack_offset + 1)
        try:
            yield
        finally:
            self.model_dataclass.__annotations__ = old


class StorageBasedModel(Model):
    _impl = None
    _cache = None
    _storage_based = True

    @classmethod
    def _load(cls, pkt, context):
        data = pkt
        if isinstance(pkt, (bytes, bytearray)):
            data = cls._parse(pkt, context)
        return cls._load_from_container(data, context)

    @classmethod
    def _load_from_container(cls, data, context):
        raise NotImplementedError

    @classmethod
    def _eager_load(cls, data, context):
        raise NotImplementedError

    @classmethod
    def _lazy_load(cls, data, context):
        return LazyStorageBased(cls, data, context)

    @classmethod
    def _parse(cls, data, context):
        cs = cls._construct()
        return cs.parse(data, **context)

    @classmethod
    def _purge(cls):
        cls._cache = None

    @classmethod
    def _construct(cls):
        raise NotImplementedError

    def _get_storage(self):
        raise NotImplementedError

    def _dump(self, **context):
        data = self._get_storage()
        cs = self._construct()
        return cs.build(data, **context)


class ModelDataclass(StorageBasedModel):
    _annotations = None
    _annotation_mgr = None
    _impl = None
    _cache = None
    _dataclass_params = {}

    def __init_subclass__(
            cls,
            _bitbin=False,
            stack_offset=1,
            annotation_mgr=None
    ):
        # never inherit cache
        cls._cache = None
        if _bitbin:
            return
        if cls._annotation_mgr is None:
            if annotation_mgr is None:
                annotation_mgr = AnnotationManager(cls)
            cls._annotation_mgr = annotation_mgr
        # some hacking
        with annotation_mgr.replace_annotations(stack_offset + 1):
            # there we go
            dataclasses.dataclass(cls, **cls._dataclass_params)

    def __post_init__(self):
        missing_cookie = object()
        context = {}
        for f in dataclasses.fields(self):
            name = f.name
            model = f.metadata['model']
            orig = self._annotation_mgr.get_field(name, default=missing_cookie, instance=self)
            if orig is missing_cookie:
                continue
            value = model._init(orig, context)
            self._annotation_mgr.set_field(name, value, instance=self)
            context[name] = value

    @classmethod
    def _init(cls, obj, context=None):
        if isinstance(obj, (cls, LazyStorageBased)):
            return obj
        if isinstance(obj, dict):
            return cls(**obj)
        if isinstance(obj, (bytes, bytearray)):
            return loads(cls, obj, **(context or {}))
        if isinstance(obj, typing.Iterable):
            return cls(*obj)
        raise TypeError(f'cannot initialize {cls.__name__} from type {type(obj).__name__!r}')

    @classmethod
    def _load_from_container(cls, data, context):
        if isinstance(data, _lib.Container):
            return cls._eager_load(data, context)
        if isinstance(data, _lib.LazyContainer):
            return cls._lazy_load(data, context)
        raise TypeError(f'cannot load data from type {type(data).__name__!r}')

    @classmethod
    def _eager_load(cls, data, context):
        initdict = {}
        for f in dataclasses.fields(cls):
            name, model = f.name, f.metadata['model']
            init = model._load(data[name], context)
            initdict[name] = init
            context[name] = init
        return cls._init(initdict)

    @classmethod
    def _construct(cls):
        if cls._cache:
            return cls._cache
        initdict = {}
        for f in dataclasses.fields(cls):
            name, model = f.name, f.metadata['model']
            construct = model._construct()
            initdict[name] = construct
        impl = cls._impl(**initdict)
        cls._cache = impl  # .compile()
        return impl

    def _get_storage(self):
        return dataclasses.asdict(self)


def models(cls):
    fields = {f.name: f for f in dataclasses.fields(cls)}
    return _lib.Container(zip(fields.keys(), map(lambda f: f.metadata['model'], fields.values())))


@typing.final
@functools.total_ordering
class LazyStorageBased:
    def __init__(self, model, container, context=None):
        self.__model = model
        self.__container = container
        self.__context = context
        self.__object = None

    def __call__(self):
        if self.__object is None:
            self.__object = self.__model._eager_load(self.__container, self.__context)
        return self.__object

    def __getattr__(self, item):
        return getattr(self, self(), item)

    def __eq__(self, other):
        return self() == other

    def __le__(self, other):
        return self() <= other

    def __repr__(self):
        return f'<{type(self).__name__} {self.__model.__name__!r}>'
