import dataclasses

import construct as _lib

from constance import composite

__all__ = (
    'BitStruct',
    'Sequence',
    'Struct',

    'field',
)


class Struct(composite.Data):
    _impl = _lib.Struct


class BitStruct(composite.Data):
    _impl = _lib.BitStruct


class Sequence(composite.Data):
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

    def __init_subclass__(cls, extends=composite.MISSING_EXTENDS, **env):
        if extends is composite.MISSING_EXTENDS:
            extends = cls.__base__
        super_fields = (
            (getattr(extends, 'fields', None) or ())
            if extends is not None else ()
        )
        fields = [*super_fields, *(getattr(cls, 'fields') or ())]

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
            super().__init_subclass__(**env)
        finally:
            cls.__annotations__ = orig_annotations


def field(name, constance, **kwargs) -> dataclasses.Field:
    metadata = kwargs.setdefault('metadata', {})
    metadata.update(constance=constance)
    f = dataclasses.field(**kwargs)
    f.name = name
    return f
