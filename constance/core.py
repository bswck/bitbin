from __future__ import annotations

import functools
import sys
import typing

import construct as _lib

from constance import _constants
from constance import classes
from constance import util

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import Literal


__all__ = (
    'Int8sl',
    'Int8sb',
    'Int8sn', 'char',
    'Int8ul',
    'Int8ub',
    'Int8un', 'unsigned_char',
    'Int16sl',
    'Int16sb',
    'Int16sn', 'short',
    'Int16ul',
    'Int16ub',
    'Int16un', 'unsigned_short',
    'Int24sl',
    'Int24sb',
    'Int24sn',
    'Int24ul',
    'Int24ub',
    'Int24un',
    'Int32sl',
    'Int32sb',
    'Int32sn', 'long',
    'Int32ul',
    'Int32ub',
    'Int32un', 'unsigned_long',
    'Int64sl',
    'Int64sb',
    'Int64sn', 'long_long',
    'Int64ul',
    'Int64ub',
    'Int64un', 'unsigned_long_long',
    'Float32l',
    'Float32b',
    'Float32n',
    'Float64l',
    'Float64b',
    'Float64n', 'double',

    'Adapter',
    'Aligned',
    'BitsInteger',
    'Bytes',
    'BytesInteger',
    'Check',
    'Checksum',
    'Compiled',
    'Compressed',
    'CompressedLZ4',
    'Computed',
    'Const',
    'Debugger',
    'Default',
    'Enum',
    'ExprAdapter',
    'ExprSymmetricAdapter',
    'ExprValidator',
    'FixedSized',
    'FlagsEnum',
    'FocusedSeq',
    'FormatField',
    'GreedyRange',
    'Hex',
    'HexDump',
    'IfThenElse',
    'Indexing',
    'Lazy',
    'LazyArray',
    'LazyBound',
    'LazyStruct',
    'Mapping',
    'NamedTuple',
    'NullStripped',
    'NullTerminated',
    'Padded',
    'Peek',
    'Pointer',
    'Prefixed',
    'Probe',
    'ProcessRotateLeft',
    'ProcessXor',
    'RawCopy',
    'Rebuffered',
    'Rebuild',
    'Renamed',
    'RepeatUntil',
    'RestreamData',
    'Restreamed',
    'Seek',
    'Select',
    'Sequence',
    'Slicing',
    'StopIf',
    'StringEncoded',
    'Struct',
    'Switch',
    'SymmetricAdapter',
    'TimestampAdapter',
    'Transformed',
    'Tunnel',
    'Union',
    'Validator',
)


def _char_cast(obj):
    if isinstance(obj, str):
        return ord(obj)
    return int(obj)


Int8sl = classes.Atomic(_lib.Int8sl, int)
Int8sb = classes.Atomic(_lib.Int8sb, int)
Int8sn = classes.Atomic(_lib.Int8sn, int)
Int8ul = classes.Atomic(_lib.Int8ul, int, cast=_char_cast)
Int8ub = classes.Atomic(_lib.Int8ub, int, cast=_char_cast)
Int8un = classes.Atomic(_lib.Int8un, int, cast=_char_cast)

Int16sl = classes.Atomic(_lib.Int16sl, int)
Int16sb = classes.Atomic(_lib.Int16sb, int)
Int16sn = classes.Atomic(_lib.Int16sn, int)
Int16ul = classes.Atomic(_lib.Int16ul, int, cast=_char_cast)
Int16ub = classes.Atomic(_lib.Int16ub, int, cast=_char_cast)
Int16un = classes.Atomic(_lib.Int16un, int, cast=_char_cast)

Int24sl = classes.Atomic(_lib.Int24sl, int)
Int24sb = classes.Atomic(_lib.Int24sb, int)
Int24sn = classes.Atomic(_lib.Int24sn, int)
Int24ul = classes.Atomic(_lib.Int24ul, int)
Int24ub = classes.Atomic(_lib.Int24ub, int)
Int24un = classes.Atomic(_lib.Int24un, int)

Int32sl = classes.Atomic(_lib.Int32sl, int)
Int32sb = classes.Atomic(_lib.Int32sb, int)
Int32sn = classes.Atomic(_lib.Int32sn, int)
Int32ul = classes.Atomic(_lib.Int32ul, int)
Int32ub = classes.Atomic(_lib.Int32ub, int)
Int32un = classes.Atomic(_lib.Int32un, int)

Int64sl = classes.Atomic(_lib.Int64sl, int)
Int64sb = classes.Atomic(_lib.Int64sb, int)
Int64sn = classes.Atomic(_lib.Int64sn, int)
Int64ul = classes.Atomic(_lib.Int64ul, int)
Int64ub = classes.Atomic(_lib.Int64ub, int)
Int64un = classes.Atomic(_lib.Int64un, int)

Float32l = classes.Atomic(_lib.Float32l, float)
Float32b = classes.Atomic(_lib.Float32b, float)
Float32n = classes.Atomic(_lib.Float32n, float)
Float64l = classes.Atomic(_lib.Float64l, float)
Float64b = classes.Atomic(_lib.Float64b, float)
Float64n = classes.Atomic(_lib.Float64n, float)

char = Int8sn
unsigned_char = Int8un

short = Int16sn
unsigned_short = Int16un

long = Int32sn
unsigned_long = Int32un

long_long = Int64sn
unsigned_long_long = Int64un

double = Float64n

atomic_types, generic_types = util.atomic_types, util.generic_types

atomic_types.register(int, classes.Atomic(_lib.Int32sn, int))
atomic_types.register(float, classes.Atomic(_lib.Float32n, float))
atomic_types.register(str, classes.Atomic(_lib.CString(_constants.DEFAULT_ENCODING), str))
atomic_types.register(bytes, classes.Atomic(_lib.GreedyBytes, bytes))
atomic_types.register(bytearray, classes.Atomic(_lib.GreedyBytes, bytearray))

generic_types.register(list, classes.Generic(list))
generic_types.register(set, classes.Generic(set))
generic_types.register(frozenset, classes.Generic(frozenset))
generic_types.register(tuple, classes.Generic(tuple))

VALID_ENDIANNESSES = {
    'l': 'l',
    'little': 'l',
    'big': 'b',
    'b': 'b',
    'native': (byte_order := sys.byteorder),
    'n': byte_order,
}


def integer(
        size: int | Callable = 4,
        signed: bool = True,
        bitwise: bool = False,
        endianness: Literal['l', 'little', 'big', 'b', 'native', 'n'] = 'n'
):
    endianness = VALID_ENDIANNESSES[endianness.lower()]
    cs = (_lib.BytesInteger, _lib.BitsInteger)[bitwise]
    return classes.Atomic(cs(size, signed=signed, swapped=endianness == 'l'), int)


class Adapter(classes.Subconstance):
    """Port to construct.Adapter"""
    _impl = _lib.Adapter  # (subcon)


class Aligned(classes.Subconstance):
    """Port to construct.Aligned"""
    _impl = _lib.Aligned  # (modulus, subcon, pattern=b'\x00')


class BitsInteger(classes.Constance):
    """Port to construct.BitsInteger"""
    _impl = _lib.BitsInteger  # (length, signed=False, swapped=False)


class Bytes(classes.Constance):
    """Port to construct.Bytes"""
    _impl = _lib.Bytes  # (length)


class BytesInteger(classes.Constance):
    """Port to construct.BytesInteger"""
    _impl = _lib.BytesInteger  # (length, signed=False, swapped=False)


class Check(classes.Constance):
    """Port to construct.Check"""
    _impl = _lib.Check  # (func)


class Checksum(classes.Constance):
    """Port to construct.Checksum"""
    _impl = _lib.Checksum  # (checksumfield, hashfunc, bytesfunc)


class Compiled(classes.Constance):
    """Port to construct.Compiled"""
    _impl = _lib.Compiled  # (parsefunc, buildfunc)


class Compressed(classes.Subconstance):
    """Port to construct.Compressed"""
    _impl = _lib.Compressed  # (subcon, encoding, level=None)


class CompressedLZ4(classes.Subconstance):
    """Port to construct.CompressedLZ4"""
    _impl = _lib.CompressedLZ4  # (subcon)


class Computed(classes.Constance):
    """Port to construct.Computed"""
    _impl = _lib.Computed  # (func)


class Const(classes.Subconstance):
    """Port to construct.Const"""
    _impl = _lib.Const  # (value, subcon=None)


class Debugger(classes.Subconstance):
    """Port to construct.Debugger"""
    _impl = _lib.Debugger  # (subcon)


class Default(classes.Subconstance):
    """Port to construct.Default"""
    _impl = _lib.Default  # (subcon, value)

    @classmethod
    def init(cls, constance_cls, instance, *args, **kwargs):
        instance.__bound__ = bound_subconstance = None
        if args or kwargs:
            bound_subconstance = super().init(constance_cls, instance, *args, **kwargs)
        return bound_subconstance


class Enum(classes.Subconstance):
    """Port to construct.Enum"""
    _impl = _lib.Enum  # (subcon, *merge, **mapping)


class ExprAdapter(classes.Subconstance):
    """Port to construct.ExprAdapter"""
    _impl = _lib.ExprAdapter  # (subcon, decoder, encoder)


class ExprSymmetricAdapter(classes.Subconstance):
    """Port to construct.ExprSymmetricAdapter"""
    _impl = _lib.ExprSymmetricAdapter  # (subcon, encoder)


class ExprValidator(classes.Subconstance):
    """Port to construct.ExprValidator"""
    _impl = _lib.ExprValidator  # (subcon, validator)


class FixedSized(classes.Subconstance):
    """Port to construct.FixedSized"""
    _impl = _lib.FixedSized  # (length, subcon)


class FlagsEnum(classes.Subconstance):
    """Port to construct.FlagsEnum"""
    _impl = _lib.FlagsEnum  # (subcon, *merge, **flags)


class FocusedSeq(classes.Constance):
    """Port to construct.FocusedSeq"""
    _impl = _lib.FocusedSeq  # (parsebuildfrom, *subcons, **subconskw)


class FormatField(classes.Constance):
    """Port to construct.FormatField"""
    _impl = _lib.FormatField  # (endianity, format)


class GreedyRange(classes.Subconstance):
    """Port to construct.GreedyRange"""
    _impl = _lib.GreedyRange  # (subcon, discard=False)


class Hex(classes.Subconstance):
    """Port to construct.Hex"""
    _impl = _lib.Hex  # (subcon)


class HexDump(classes.Subconstance):
    """Port to construct.HexDump"""
    _impl = _lib.HexDump  # (subcon)


class IfThenElse(classes.Constance):
    """Port to construct.IfThenElse"""
    _impl = _lib.IfThenElse  # (condfunc, thensubcon, elsesubcon)


class Indexing(classes.Subconstance):
    """Port to construct.Indexing"""
    _impl = _lib.Indexing  # (subcon, count, index, empty=None)


class Lazy(classes.Subconstance):
    """Port to construct.Lazy"""
    _impl = _lib.Lazy  # (subcon)


class LazyArray(classes.ArrayLike):
    """Port to construct.LazyArray"""
    _impl = _lib.LazyArray  # (count, subcon)


class LazyBound(classes.Constance):
    """Port to construct.LazyBound"""
    _impl = _lib.LazyBound  # (subconfunc)

    @staticmethod
    def map_arguments(arguments):
        arguments.update(subcon=lambda: util.ensure_construct(arguments['subconfunc']()))
        return arguments


class LazyStruct(classes.Data):
    """Port to construct.LazyStruct"""
    _impl = _lib.LazyStruct  # (*subcons, **subconskw)


class Mapping(classes.Subconstance):
    """Port to construct.Mapping"""
    _impl = _lib.Mapping  # (subcon, mapping)


class NamedTuple(classes.Subconstance):
    """Port to construct.NamedTuple"""
    _impl = _lib.NamedTuple  # (tuplename, tuplefields, subcon)


class NullStripped(classes.Subconstance):
    """Port to construct.NullStripped"""
    _impl = _lib.NullStripped  # (subcon, pad=b'\x00')


class NullTerminated(classes.Subconstance):
    """Port to construct.NullTerminated"""
    # (subcon, term=b'\x00', include=False, consume=True, require=True)
    _impl = _lib.NullTerminated


class Padded(classes.Subconstance):
    """Port to construct.Padded"""
    _impl = _lib.Padded  # (length, subcon, pattern=b'\x00')


class Peek(classes.Subconstance):
    """Port to construct.Peek"""
    _impl = _lib.Peek  # (subcon)


class Pointer(classes.Subconstance):
    """Port to construct.Pointer"""
    _impl = _lib.Pointer  # (offset, subcon, stream=None)


class Prefixed(classes.Subconstance):
    """Port to construct.Prefixed"""
    _impl = _lib.Prefixed  # (lengthfield, subcon, includelength=False)

    @staticmethod
    def map_arguments(arguments):
        arguments.update(lengthfield=util.ensure_construct(arguments.get('lengthfield')))
        return arguments


class Probe(classes.Constance):
    """Port to construct.Probe"""
    _impl = _lib.Probe  # (into=None, lookahead=None)


class ProcessRotateLeft(classes.Subconstance):
    """Port to construct.ProcessRotateLeft"""
    _impl = _lib.ProcessRotateLeft  # (amount, group, subcon)


class ProcessXor(classes.Subconstance):
    """Port to construct.ProcessXor"""
    _impl = _lib.ProcessXor  # (padfunc, subcon)


class RawCopy(classes.Subconstance):
    """Port to construct.RawCopy"""
    _impl = _lib.RawCopy  # (subcon)


class Rebuffered(classes.Subconstance):
    """Port to construct.Rebuffered"""
    _impl = _lib.Rebuffered  # (subcon, tailcutoff=None)


class Rebuild(classes.Subconstance):
    """Port to construct.Rebuild"""
    _impl = _lib.Rebuild  # (subcon, func)


class Renamed(classes.Subconstance):
    """Port to construct.Renamed"""
    _impl = _lib.Renamed  # (subcon, newname=None, newdocs=None, newparsed=None)


class RepeatUntil(classes.Subconstance):
    """Port to construct.RepeatUntil"""
    _impl = _lib.RepeatUntil  # (predicate, subcon, discard=False)


class RestreamData(classes.Subconstance):
    """Port to construct.RestreamData"""
    _impl = _lib.RestreamData  # (datafunc, subcon)

    @staticmethod
    def map_arguments(arguments):
        arguments.update(datafunc=classes.MaybeConstructLambda(arguments['datafunc']))
        return arguments


class Restreamed(classes.Subconstance):
    """Port to construct.Restreamed"""
    _impl = _lib.Restreamed  # (subcon, decoder, decoderunit, encoder, encoderunit, sizecomputer)


class Seek(classes.Constance):
    """Port to construct.Seek"""
    _impl = _lib.Seek  # (at, whence=0)


class Select(classes.FieldListData):
    """Port to construct.Select"""
    _impl = _lib.Select  # (*subcons, **subconskw)
    fields = None


class Sequence(classes.FieldListData):
    """Port to construct.Sequence"""
    _impl = _lib.Sequence  # (*subcons, **subconskw)
    fields = None


class Slicing(classes.Subconstance):
    """Port to construct.Slicing"""
    _impl = _lib.Slicing  # (subcon, count, start, stop, step=1, empty=None)


class StopIf(classes.Constance):
    """Port to construct.StopIf"""
    _impl = _lib.StopIf  # (condfunc)


class StringEncoded(classes.Subconstance):
    """Port to construct.StringEncoded"""
    _impl = _lib.StringEncoded  # (subcon, encoding)


class Struct(classes.Data):
    """Port to construct.Struct"""
    _impl = _lib.Struct  # (*subcons, **subconskw)


MISSING_KEY = object()


class Switch(classes.Constance):
    """Port to construct.Switch"""
    _impl = _lib.Switch  # (keyfunc, cases, default=None)
    cases = None

    @classmethod
    def construct(cls):
        return cls._impl(
            classes.MaybeConstructLambda(cls.key), cls.cases,
            classes.MaybeConstructLambda(cls.default),
        )

    @classmethod
    def default(cls):
        return _lib.Pass

    @classmethod
    def key(cls):
        raise NotImplementedError

    @classmethod
    def autokey(cls, _constance_cls):
        return len(cls.cases)

    @classmethod
    def register(cls, key=MISSING_KEY, constance_cls=None):
        if constance_cls is None:
            return functools.partial(cls.register, key=key)
        if key is MISSING_KEY:
            key = cls.autokey(constance_cls)
        if key in cls.cases:
            return cls.register_overload(cls, key, constance_cls)
        cls.cases[key] = constance_cls
        return constance_cls

    @classmethod
    def register_overload(cls, key, constance_cls):
        overload_case = cls.cases[key]
        if not isinstance(overload_case, Select):
            overload_case = Select.from_fields([overload_case])
        overload_case.add_field(constance_cls)
        return constance_cls


class SymmetricAdapter(classes.Subconstance):
    """Port to construct.SymmetricAdapter"""
    _impl = _lib.SymmetricAdapter  # (subcon)


class TimestampAdapter(classes.Subconstance):
    """Port to construct.TimestampAdapter"""
    _impl = _lib.TimestampAdapter  # (subcon)


class Transformed(classes.Subconstance):
    """Port to construct.Transformed"""
    _impl = _lib.Transformed  # (subcon, decodefunc, decodeamount, encodefunc, encodeamount)


class Tunnel(classes.Subconstance):
    """Port to construct.Tunnel"""
    _impl = _lib.Tunnel  # (subcon)


class Union(classes.Data):
    """Port to construct.Union"""
    _impl = _lib.Union  # (parsefrom, *subcons, **subconskw)


class Validator(classes.Subconstance):
    """Port to construct.Validator"""
    _impl = _lib.Validator  # (subcon)
