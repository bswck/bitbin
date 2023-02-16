# This is slow, don't use it

import dataclasses
import typing

import construct as _lib

from bitbin import core
#
# __all__ = (
#     'Fields',
#     'sequence',
#     'Sequence',
#     'SequenceDataclass',
# )
# #
# #
# class SequenceDataclass(core.ModelDataclass, interface=True):
#     _impl = _lib.Sequence
#
#     def _extract(self):
#         return list(dataclasses.asdict(self).values())
#
#     @classmethod
#     def _load_from_container(cls, data, context):
#         if isinstance(data, _lib.ListContainer):
#             return cls._eager_load(data, context)
#         if isinstance(data, _lib.LazyListContainer):
#             return cls._lazy_load(data, context)
#         raise TypeError(f'cannot load data from type {type(data).__name__!r}')
#
#     @classmethod
#     def _eager_load(cls, data, context):
#         fs = dataclasses.fields(cls)
#         initlist = (
#             fs[i].metadata['model']._load(value, context)
#             for i, value in enumerate(data)
#         )
#         return cls._init(initlist)
#
#
# class Fields(list):
#     def __init__(self, *fs, name_factory=None):
#         if name_factory is None:
#             name_factory = (lambda n: f'field_{n+1}')
#         data = []
#         self._named_fields = {}
#         self._annotations = {}
#         for i, type_hint in enumerate(fs):
#             if isinstance(type_hint, dataclasses.Field):
#                 f = type_hint
#                 if f.name is None:
#                     f.name = name_factory(i)
#             else:
#                 f = core.make_field(name=name_factory(i), type_hint=type_hint)
#             self._named_fields[f.name] = f
#             self._annotations[f.name] = f.metadata['model']
#             data.append(f)
#         super().__init__(data)
#
#     def __getattr__(self, name):
#         return self._named_fields.get(name)
#
#
# class SeqProperty:
#     def __get__(self, instance, owner):
#         if instance is None:
#             return owner._implicit
#         return instance._internal
#
#
# class Sequence(core.Model):
#     _internal_class = SequenceDataclass
#     _fields_class = Fields
#     _implicit: typing.ClassVar[type[SequenceDataclass]]
#     fields = _fields_class()
#     seq = SeqProperty()
#
#     def __init_subclass__(cls, **kwargs):
#         if not isinstance(cls.fields, cls._fields_class):
#             cls.fields = cls._fields_class(*cls.fields)
#         cls._implicit = type(
#             cls.__name__,
#             (cls._internal_class,),
#             {
#                 '_annotations': cls.fields._annotations,
#                 **cls.fields._named_fields
#             }
#         )
#
#     def __init__(self, *args, **kwargs):
#         if self._implicit is None:
#             raise TypeError('cannot instantiate abstract class')
#         self._internal = self._implicit(*args, **kwargs)
#         self._inithook()
#
#     def _inithook(self):
#         """Override this instead of overriding the constructor."""
#
#     def _construct(self):
#         return self._internal._construct()
#
#     @classmethod
#     def _init(cls, data):
#         instance = object.__new__(cls)
#         instance._internal = cls._implicit._init(data)
#         instance._inithook()
#         return instance
#
#     @classmethod
#     def _load(cls, data, context):
#         instance = object.__new__(cls)
#         instance._internal = cls._implicit._load(data, context)
#         instance._inithook()
#         return instance
#
#     def _dump(self, **context):
#         return self._internal._dump(**context)
#
#     def __getitem__(self, item):
#         return self._internal._extract()[item]
#
#     def __iter__(self):
#         yield from self._internal._extract()
#
#     def __class_getitem__(cls, item):
#         return cls.fields[item]
#
#     def __repr__(self):
#         return repr(self._internal)
#
#
# def sequence(*fields, name='Sequence', field_name_factory=None):
#     """Sequence factory"""
#     return type(
#         name, (Sequence,),
#         {'fields': fields},
#         name_factory=field_name_factory
#     )
