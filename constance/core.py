from __future__ import annotations

import contextlib
import dataclasses
import inspect
import typing


from constance import util


class Constance:
    def __init__(self, *args, **kwargs):
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def _load(cls, data, context=None):
        raise NotImplementedError

    @classmethod
    def _construct(cls, **context):
        raise NotImplementedError

    def _build(self, **context):
        raise NotImplementedError


MISSING = dataclasses.MISSING


def field(
        ctype,
        *,
        name=None,
        default=MISSING,
        default_factory=MISSING,
        **kwargs
):
    f = dataclasses.field(default, default_factory, **kwargs)
    f.metadata = dict(f.metadata, name=name, ctype=util.make_ctype(ctype))
    return f


@dataclasses.dataclass
class AnnotationManager:
    constance: type[Data]

    def __post_init__(self):
        self._annotations = (
            self.constance._annotations
            or self.constance.__annotations__
        )
        self._globals = {}
        self._locals = {}

    def get_env(self, stack_offset=None):
        global_ns, local_ns = self._globals, self._locals
        if stack_offset is not None:
            frame = inspect.stack()[stack_offset].frame
            global_ns.update(frame.f_globals)
            local_ns.update(frame.f_locals)
        return global_ns, local_ns

    def map_to_fields(self, stack_offset=1):
        global_ns, local_ns = self.get_env(stack_offset)
        for name, type_hint in typing.get_type_hints(
                self.constance,
                globalns=global_ns,
                localns=local_ns
        ).items():
            f = self.get_field(name, None)
            ctype = None
            if isinstance(f, dataclasses.Field):
                default = f.default
                default_factory = f.default_factory
                metadata = f.metadata
                ctype = metadata.get('ctype')
            else:
                default = f
                default_factory = dataclasses.MISSING
                metadata = {}
            if ctype is None:
                ctype = util.make_ctype(
                    type_hint, qualname=f'{self.constance.__name__}.{name}'
                )
            f = field(
                ctype, name=name,
                default=default,
                default_factory=default_factory,
                **metadata,
            )
            self._annotations[name] = ctype
            self.set_field(name, f)
        return self._annotations

    def get_field(self, name, default=MISSING):
        return (
            getattr(self.constance, name)
            if default is MISSING else
            getattr(self.constance, name, default)
        )

    def set_field(self, name, value):
        setattr(self.constance, name, value)

    @contextlib.contextmanager
    def patch(self, stack_offset=1):
        old = self.constance.__annotations__

        self.constance.__annotations__ = self.map_to_fields(stack_offset)

        try:
            yield
        finally:
            self.constance.__annotations__ = old


class Data(Constance):
    _dataclass_params = {}  # type: typing.ClassVar[dict]
    _annotation_manager = None   # type: typing.ClassVar[AnnotationManager]
    _annotations = None  # type: typing.ClassVar[dict]

    def __init_subclass__(cls, stack_offset=1, annotation_manager=None):
        if cls._annotation_manager is None:
            if annotation_manager is None:
                annotation_manager = AnnotationManager(cls)
            cls._annotation_manager = annotation_manager
        with annotation_manager.patch(stack_offset+1):
            dataclasses.dataclass(cls)
        if cls._dataclass_params.get('init', True):
            cls._init = cls.__init__

