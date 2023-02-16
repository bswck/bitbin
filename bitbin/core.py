from __future__ import annotations

import contextlib
import dataclasses
import functools
import inspect
import typing

import construct as _lib

from bitbin import util

__all__ = (
    'AnnotationManager',
    'load', 'loads',
    'dump', 'dumps',
    'field',
    'Model',
    'ModelFeature',
    'ModelFeatureStorage',
    'ModelDataclass',
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
    if initializer is not missing:
        model = model._init(initializer)
    return model._dump(**context)


class Model:
    _is_model = True
    _storage_based = False

    # @typing.overload
    # def _init(self): ...

    def _init(self, *args):
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


class ModelFeatureStorage(Model):
    _storage_based = True

    def __init__(self, factory, instance):
        self._factory = factory
        self._instance = instance

    def _construct(self):
        subcon = self._instance._construct()
        return self._factory(subcon)

    def _dump(self, **context):
        return self._construct().build(
            self._instance._extract(),
            **context
        )


class ModelFeature(Model):
    """Typically links to Subconstruct subclasses"""

    _feature_impl = None
    _storage_based = True
    _storage_class = ModelFeatureStorage

    def __init__(self, model, /, *args, **kwargs):
        self._model = util.make_model(model)
        self._params = args, kwargs

    def _get_construct_factory(self):
        args, kwargs = self._params
        return lambda subcon: self._feature_impl(
            subcon, *args, **kwargs
        )

    def _get_construct(self, subcon=None):
        factory = self._get_construct_factory()
        if subcon is None:
            subcon = self._model._construct()
        return factory(subcon)

    def _init(self, obj):
        instance = self._model._init(obj)
        if self._model._storage_based:
            return self._storage_class(
                self._get_construct,
                instance
            )
        return instance

    def _load(self, data, context):
        return self._model._load(data, context)

    def _construct(self):
        return self._get_construct()

    def _dump(self, obj, **context):
        return self._construct().build(obj, **context)


class Singleton(Model):
    _storage_based = False

    def __init__(self, construct, value):
        self._aconstruct = construct
        self._value = value

    def _init(self):
        return self._value

    def _load(self, data=None, context=None):
        return self._value

    def _construct(self):
        return self._aconstruct

    def _dump(self, obj=None, **context):
        return self._construct().dump()


class Atomic(Model):
    def __init__(self, construct, atype, pass_context=False, loader=None, initializer=None):
        self._aconstruct = construct
        self._atype = atype
        self._loader = loader or atype
        self._initializer = initializer or atype
        self._pass_context = pass_context

    def _init(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return loads(self, obj)
        return self._initializer(obj)

    def _load(self, data, context):
        if isinstance(data, (bytes, bytearray)):
            return self._init(self._aconstruct.parse(data))
        return self._loader(data, context) if self._pass_context else self._loader(data)

    def _construct(self):
        return self._aconstruct

    def _dump(self, obj, **context):
        return self._aconstruct.dump(self._init(obj), **context)


@dataclasses.dataclass
class Generic(Model):
    _atype: type

    def __call__(self, args, *, count=None):
        if len(args) == 1:
            model = util.make_model(*args)
        else:
            args = [arg._construct() for arg in map(util.make_model, args)]
            if len(set(args)) > 1:
                return Atomic(_lib.Sequence(*args), self._atype)
            model = Atomic(args[0])
        if count is None:
            return Atomic(
                _lib.GreedyRange(model._construct()), self._atype
            )
        return Atomic(
            _lib.Array(count, model._construct()), self._atype
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
    f.metadata = dict(f.metadata, model=util.make_model(model) if model else None)
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
            '_AnnotationHelper', (),
            {'__annotations__': anns}
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
        return (
            getattr(instance or self.model_dataclass, name)
            if default is MISSING else
            getattr(instance or self.model_dataclass, name, default)
        )

    def set_field(self, name, value, instance=None):
        setattr(instance or self.model_dataclass, name, value)

    @contextlib.contextmanager
    def replace_annotations(self, stack_offset=1):
        stack_offset += 1  # +1 from the context manager frame

        old = self.model_dataclass.__annotations__

        self.model_dataclass.__annotations__ = self.map_to_fields(stack_offset + 1)

        try:
            yield
        finally:
            self.model_dataclass.__annotations__ = old


class ModelDataclass(Model):
    _dataclass_params = {}
    _annotation_manager = None
    _annotations = None
    _storage_based = True
    _impl = None
    __cache = None

    def __init_subclass__(
            cls,
            _bitbin=False,
            stack_offset=1,
            annotation_manager=None
    ):
        if _bitbin:
            return
        if cls._annotation_manager is None:
            if annotation_manager is None:
                annotation_manager = AnnotationManager(cls)
            cls._annotation_manager = annotation_manager
        with annotation_manager.replace_annotations(stack_offset+1):
            dataclasses.dataclass(cls, **cls._dataclass_params)

    def __post_init__(self):
        for f in dataclasses.fields(self):
            name = f.name
            model = f.metadata['model']
            missing = object()
            orig = self._annotation_manager.get_field(name, default=missing, instance=self)
            if orig is missing:
                continue
            value = model._init(orig)
            self._annotation_manager.set_field(name, value, instance=self)

    @classmethod
    def _init(cls, obj):
        if isinstance(obj, LazyModelDataclass):
            return obj
        if isinstance(obj, dict):
            return cls(**obj)
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, (bytes, bytearray)):
            return loads(cls, obj)
        if isinstance(obj, typing.Iterable):
            return cls(*obj)
        raise TypeError(f'cannot initialize {cls.__name__} from type {type(obj).__name__!r}')

    @classmethod
    def _load(cls, pkt, context):
        data = pkt
        if isinstance(pkt, (bytes, bytearray)):
            data = cls._parse(pkt, context)
        return cls._load_from_container(data, context)

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
            initdict[name] = f.metadata['model']._load(data[name := f.name], context)
        return cls._init(initdict)

    @classmethod
    def _lazy_load(cls, data, context):
        return LazyModelDataclass(cls, data, context)

    @classmethod
    def _parse(cls, data, context):
        cs = cls._construct()
        return cs.parse(data, **context)

    @classmethod
    def _purge(cls):
        cls.__cache = None

    @classmethod
    def _construct(cls):
        if cls.__cache:
            return cls.__cache
        initdict = {}
        for f in dataclasses.fields(cls):
            name = f.name
            construct = f.metadata['model']._construct()
            initdict[name] = construct
        impl = cls._impl(**initdict)
        cls.__cache = impl.compile()
        return impl

    def _extract(self):
        return dataclasses.asdict(self)

    def _dump(self, **context):
        data = self._extract()
        cs = self._construct()
        return cs.build(data, **context)


@typing.final
@functools.total_ordering
class LazyModelDataclass:
    def __init__(self, dataclass, container, context=None):
        self.__dataclass = dataclass
        self.__container = container
        self.__context = context
        self.__object = None

    def __call__(self):
        if self.__object is None:
            self.__object = self.__dataclass._eager_load(self.__container, self.__context)
        return self.__object

    def __getattr__(self, item):
        return getattr(self, self(), item)

    def __eq__(self, other):
        return self() == other

    def __le__(self, other):
        return self() <= other

    def __repr__(self):
        return f'<LazyModelDataclass {self.__dataclass.__name__!r}>'
