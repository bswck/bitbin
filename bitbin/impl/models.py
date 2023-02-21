import functools
import typing

import construct as _lib

from bitbin import core
from bitbin import util


__all__ = (
    'Check',
    'Checksum',
    'Computed',
    'IfThenElse',
    'LazyBound',
    'Probe',
    'Seek',
    'Select',
    'FocusedSeq',
    'Sequence',
    'StopIf',
    'Switch',
)


class Check(core.Model):
    """Port to construct.Check"""

    _impl = _lib.Check  # (func)


class Checksum(core.Model):
    """Port to construct.Checksum"""

    _impl = _lib.Checksum  # (checksumfield, hashfunc, bytesfunc)


class Computed(core.Model):
    """Port to construct.Computed"""

    _impl = _lib.Computed  # (func)


class IfThenElse(core.Model):
    """Port to construct.IfThenElse"""

    _impl = _lib.IfThenElse  # (condfunc, thensubcon, elsesubcon)


class LazyBound(core.Model):
    """Port to construct.LazyBound"""

    _impl = _lib.LazyBound  # (subconfunc)


class Probe(core.Model):
    """Port to construct.Probe"""

    _impl = _lib.Probe  # (into=None, lookahead=None)


class Seek(core.Atomic):
    """Port to construct.Seek"""

    _impl = _lib.Seek  # (at, whence=0)

    def __init__(self, at, whence=0):
        self.at = at
        self.whence = whence
        super().__init__(self._impl(at, whence), int, False)


class Select(core.Model):
    """Port to construct.Select"""

    _impl = _lib.Select  # (*subcons, **subconskw)


class Sequence(list, core.StorageBasedModel):
    """Port to construct.Sequence"""

    _impl = _lib.Sequence  # (*subcons, **subconskw)
    _models = None

    def __init_subclass__(cls):
        if cls._models:
            cls._models = [util.make_model(model) for model in cls._models]

    def __init__(self, *values):
        super().__init__(
            model._init(value) for value, model in zip(values, self._models)
        )

    @classmethod
    def _construct(cls):
        if not cls._cache:
            cls._cache = cls._impl(*(model._construct() for model in cls._models))
        return cls._cache

    @classmethod
    def _init(cls, obj, context=None):
        if isinstance(obj, (cls, core.LazyStorageBased)):
            return obj
        if isinstance(obj, dict):
            return cls._init_from_dict(obj, context)
        if isinstance(obj, (bytes, bytearray)):
            return core.loads(cls, obj, **(context or {}))
        if isinstance(obj, typing.Iterable):
            return cls(*obj)
        raise TypeError(f'cannot initialize {cls.__name__} from type {type(obj).__name__!r}')

    @classmethod
    def _init_from_dict(cls, data, default=None):
        initlist = []
        for model in (cls._models or ()):
            name = getattr(model, 'newname', None)
            if name in data:
                value = model._init(data[name])
            else:
                value = model._init(default)
            initlist.append(value)
        return cls(*initlist)

    @classmethod
    def _load_from_container(cls, data, context):
        if isinstance(data, _lib.ListContainer):
            return cls._eager_load(data, context)
        if isinstance(data, _lib.LazyListContainer):
            return cls._lazy_load(data, context)
        raise TypeError(f'cannot load data from type {type(data).__name__!r}')

    @classmethod
    def _eager_load(cls, data, context):
        initlist = []
        for elem, model in zip(data, cls._models):
            initlist.append(model._load(elem, context))
        return cls(*data)

    def _get_storage(self):
        return self


class FocusedSeq(Sequence):
    """Port to construct.FocusedSeq"""

    _impl = _lib.FocusedSeq  # (parsebuildfrom, *subcons, **subconskw)
    _parsebuildfrom = None
    _storage_based = False
    # TODO

    @classmethod
    def _construct(cls):
        if not cls._cache:
            cls._cache = cls._impl(
                cls._parsebuildfrom, *(model._construct() for model in cls._models)
            )
        return cls._cache


class StopIf(core.Model):
    """Port to construct.StopIf"""

    _impl = _lib.StopIf  # (condfunc)


class Switch(core.Model):
    """Port to construct.StopIf"""

    _impl = _lib.Switch  # (keyfunc, cases, default=None)

    def __init__(self, keyfunc, default=None, cases=None):
        if isinstance(keyfunc, str):
            keyfunc = getattr(_lib.this, keyfunc.replace('this.', '', 1))
        self._keyfunc = keyfunc
        self._cases = {}
        self._cases_cs = {}
        for case, model in (cases or {}).items():
            self.register(case, model)
        self._default = util.make_model(default) if default else None
        self._default_cs = default._construct() if default else None

    def register(self, case, model=None):
        if model is None:
            return functools.partial(self.register, case)
        if case in self._cases:
            raise ValueError(
                f'case {case!r} already exists '
                '- consider registering a Switch/Select for this case'
            )
        model = util.make_model(model)
        self._cases[case] = model
        self._cases_cs[case] = model._construct()
        return model

    def _init(self, data, context=None):
        if not context:
            raise ValueError('context is required for Switch')
        case = self._keyfunc(_lib.Container(context))
        impl = self._cases.get(case, self._default)
        if impl is None:
            raise ValueError(f'no case for {case!r}')
        return impl._init(data, context)

    def _construct(self):
        return self._impl(
            self._keyfunc,
            self._cases_cs,
            self._default_cs
        )

    def _load(self, data, context):
        if not context:
            raise ValueError('context is required for Switch')
        case = self._keyfunc(context)
        impl = self._cases.get(case, self._default)
        if impl is None:
            raise ValueError(f'no case for {case!r}')
        return impl._load(data, context)

    def _dump(self, obj, **context):
        if not context:
            raise ValueError('context is required for Switch')
        case = self._keyfunc(_lib.Container(context))
        impl = self._cases.get(case, self._default)
        if impl is None:
            raise ValueError(f'no case for {case!r}')
        if impl._storage_based:
            return impl._init(obj, context).dump(**context)
        return impl._dump(obj, **context)

    def __class_getitem__(cls, item):
        return cls(*item)
