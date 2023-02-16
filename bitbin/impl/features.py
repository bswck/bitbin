import dataclasses
from typing import Callable, Any

import construct as _lib

from bitbin import core

__all__ = (
    'Adapter',
    'Aligned',
    'Array',
    'Compressed',
    'CompressedLZ4',
    'Const',
    'Debugger',
    'Default',
    'Enum',
    'ExprAdapter',
    'ExprSymmetricAdapter',
    'ExprValidator',
    'FixedSized',
    'FlagsEnum',
    'GreedyRange',
    'Hex',
    'HexDump',
    'Indexing',
    'Lazy',
    'LazyArray',
    'Mapping',
    'NamedTuple',
    'NullStripped',
    'NullTerminated',
    'Padded',
    'Peek',
    'Pointer',
    'Prefixed',
    'ProcessRotateLeft',
    'ProcessXor',
    'RawCopy',
    'Rebuffered',
    'Rebuild',
    'Renamed',
    'RepeatUntil',
    'RestreamData',
    'Restreamed',
    'Slicing',
    'StringEncoded',
    'SymmetricAdapter',
    'TimestampAdapter',
    'Transformed',
    'Tunnel',
    'Validator',
)


class _ModelFeatureDataclass(core.ModelFeature):
    def _extract_args(self):
        args = dataclasses.asdict(self)
        del args['model']
        return args

    def _get_construct_factory(self):
        return lambda subcon: self._feature_impl(
            **{**self._extract_args(), 'subcon': subcon}
        )


@dataclasses.dataclass
class Adapter(_ModelFeatureDataclass):
    """Port to construct.Adapter"""
    _feature_impl = _lib.Adapter  # (subcon)


@dataclasses.dataclass
class Aligned(_ModelFeatureDataclass):
    """Port to construct.Aligned"""
    modulus: int | Callable[[], int]
    pattern: bytes = b'\x00'
    model: Any = None

    _feature_impl = _lib.Aligned  # (modulus, subcon, pattern=b'\x00')


@dataclasses.dataclass
class Array(_ModelFeatureDataclass):
    """Port to construct.Array"""
    count: int | Callable[[], int]
    model: Any  # require model here for no decorator syntax
    discard: bool = False
    type: type = list

    _storage_based = True
    _feature_impl = _lib.Array  # (count, subcon, discard=False)

    def _extract_args(self):
        args = super()._extract_args()
        del args['type']
        return args

    def _init(self, obj):
        return self.type(map(self.model._init, obj))

    def _load(self, data, context):
        if isinstance(data, (bytes, bytearray)):
            data = self._construct().parse(data, **(context or {}))
        loaded = (self.model._init(element) for element in data)
        return self.type(loaded)


@dataclasses.dataclass
class Compressed(_ModelFeatureDataclass):
    """Port to construct.Compressed"""

    _feature_impl = _lib.Compressed  # (subcon, encoding, level=None)


@dataclasses.dataclass
class CompressedLZ4(_ModelFeatureDataclass):
    """Port to construct.CompressedLZ4"""

    _feature_impl = _lib.CompressedLZ4  # (subcon)


@dataclasses.dataclass
class Const(_ModelFeatureDataclass):
    """Port to construct.Const"""
    value: Any
    model: Any = None

    _feature_impl = _lib.Const  # (value, subcon=None)


@dataclasses.dataclass
class Debugger(_ModelFeatureDataclass):
    """Port to construct.Debugger"""

    _feature_impl = _lib.Debugger  # (subcon)


@dataclasses.dataclass
class Default(_ModelFeatureDataclass):
    """Port to construct.Default"""
    model: Any
    value: Any

    _feature_impl = _lib.Default  # (subcon, value)

    def _init(self, obj):
        if obj is None:
            return obj
        return super()._init(obj)


@dataclasses.dataclass
class Enum(_ModelFeatureDataclass):
    """Port to construct.Enum"""

    _feature_impl = _lib.Enum  # (subcon, *merge, **mapping)


@dataclasses.dataclass
class ExprAdapter(_ModelFeatureDataclass):
    """Port to construct.ExprAdapter"""

    _feature_impl = _lib.ExprAdapter  # (subcon, decoder, encoder)


@dataclasses.dataclass
class ExprSymmetricAdapter(_ModelFeatureDataclass):
    """Port to construct.ExprSymmetricAdapter"""

    _feature_impl = _lib.ExprSymmetricAdapter  # (subcon, encoder)


@dataclasses.dataclass
class ExprValidator(_ModelFeatureDataclass):
    """Port to construct.ExprValidator"""

    _feature_impl = _lib.ExprValidator  # (subcon, validator)


@dataclasses.dataclass
class FixedSized(_ModelFeatureDataclass):
    """Port to construct.FixedSized"""

    _feature_impl = _lib.FixedSized  # (length, subcon)


@dataclasses.dataclass
class FlagsEnum(_ModelFeatureDataclass):
    """Port to construct.FlagsEnum"""

    _feature_impl = _lib.FlagsEnum  # (subcon, *merge, **flags)


@dataclasses.dataclass
class GreedyRange(_ModelFeatureDataclass):
    """Port to construct.GreedyRange"""

    _feature_impl = _lib.GreedyRange  # (subcon, discard=False)


@dataclasses.dataclass
class Hex(_ModelFeatureDataclass):
    """Port to construct.Hex"""

    _feature_impl = _lib.Hex  # (subcon)


@dataclasses.dataclass
class HexDump(_ModelFeatureDataclass):
    """Port to construct.HexDump"""

    _feature_impl = _lib.HexDump  # (subcon)


@dataclasses.dataclass
class Indexing(_ModelFeatureDataclass):
    """Port to construct.Indexing"""

    _feature_impl = _lib.Indexing  # (subcon, count, index, empty=None)


@dataclasses.dataclass
class Lazy(_ModelFeatureDataclass):
    """Port to construct.Lazy"""

    _feature_impl = _lib.Lazy  # (subcon)


@dataclasses.dataclass
class LazyArray(_ModelFeatureDataclass):
    """Port to construct.LazyArray"""

    _feature_impl = _lib.LazyArray  # (count, subcon)


@dataclasses.dataclass
class Mapping(_ModelFeatureDataclass):
    """Port to construct.Mapping"""

    _feature_impl = _lib.Mapping  # (subcon, mapping)


@dataclasses.dataclass
class NamedTuple(_ModelFeatureDataclass):
    """Port to construct.NamedTuple"""

    _feature_impl = _lib.NamedTuple  # (tuplename, tuplefields, subcon)


@dataclasses.dataclass
class NullStripped(_ModelFeatureDataclass):
    """Port to construct.NullStripped"""

    _feature_impl = _lib.NullStripped  # (subcon, pad=b'\x00')


@dataclasses.dataclass
class NullTerminated(_ModelFeatureDataclass):
    """Port to construct.NullTerminated"""

    # (subcon, term=b'\x00', include=False, consume=True, require=True)
    _impl = _lib.NullTerminated


@dataclasses.dataclass
class Padded(_ModelFeatureDataclass):
    """Port to construct.Padded"""

    _feature_impl = _lib.Padded  # (length, subcon, pattern=b'\x00')


@dataclasses.dataclass
class Peek(_ModelFeatureDataclass):
    """Port to construct.Peek"""

    _feature_impl = _lib.Peek  # (subcon)


@dataclasses.dataclass
class Pointer(_ModelFeatureDataclass):
    """Port to construct.Pointer"""

    _feature_impl = _lib.Pointer  # (offset, subcon, stream=None)


@dataclasses.dataclass
class Prefixed(_ModelFeatureDataclass):
    """Port to construct.Prefixed"""

    _feature_impl = _lib.Prefixed  # (lengthfield, subcon, includelength=False)


@dataclasses.dataclass
class ProcessRotateLeft(_ModelFeatureDataclass):
    """Port to construct.ProcessRotateLeft"""

    _feature_impl = _lib.ProcessRotateLeft  # (amount, group, subcon)


@dataclasses.dataclass
class ProcessXor(_ModelFeatureDataclass):
    """Port to construct.ProcessXor"""

    _feature_impl = _lib.ProcessXor  # (padfunc, subcon)


@dataclasses.dataclass
class RawCopy(_ModelFeatureDataclass):
    """Port to construct.RawCopy"""

    _feature_impl = _lib.RawCopy  # (subcon)


@dataclasses.dataclass
class Rebuffered(_ModelFeatureDataclass):
    """Port to construct.Rebuffered"""

    _feature_impl = _lib.Rebuffered  # (subcon, tailcutoff=None)


@dataclasses.dataclass
class Rebuild(_ModelFeatureDataclass):
    """Port to construct.Rebuild"""

    _feature_impl = _lib.Rebuild  # (subcon, func)


@dataclasses.dataclass
class Renamed(_ModelFeatureDataclass):
    """Port to construct.Renamed"""

    _feature_impl = _lib.Renamed  # (subcon, newname=None, newdocs=None, newparsed=None)


@dataclasses.dataclass
class RepeatUntil(_ModelFeatureDataclass):
    """Port to construct.RepeatUntil"""

    _feature_impl = _lib.RepeatUntil  # (predicate, subcon, discard=False)


@dataclasses.dataclass
class RestreamData(_ModelFeatureDataclass):
    """Port to construct.RestreamData"""

    _feature_impl = _lib.RestreamData  # (datafunc, subcon)


@dataclasses.dataclass
class Restreamed(_ModelFeatureDataclass):
    """Port to construct.Restreamed"""

    _feature_impl = (
        _lib.Restreamed
    )  # (subcon, decoder, decoderunit, encoder, encoderunit, sizecomputer)


@dataclasses.dataclass
class Slicing(_ModelFeatureDataclass):
    """Port to construct.Slicing"""
    count: int
    start: int
    stop: int
    step: int = 1
    empty: Any = None

    _feature_impl = _lib.Slicing  # (subcon, count, start, stop, step=1, empty=None)


@dataclasses.dataclass
class StringEncoded(_ModelFeatureDataclass):
    """Port to construct.StringEncoded"""
    encoding: str

    _feature_impl = _lib.StringEncoded  # (subcon, encoding)


@dataclasses.dataclass
class SymmetricAdapter(_ModelFeatureDataclass):
    """Port to construct.SymmetricAdapter"""

    _feature_impl = _lib.SymmetricAdapter  # (subcon)


@dataclasses.dataclass
class TimestampAdapter(_ModelFeatureDataclass):
    """Port to construct.TimestampAdapter"""

    _feature_impl = _lib.TimestampAdapter  # (subcon)


@dataclasses.dataclass
class Transformed(_ModelFeatureDataclass):
    """Port to construct.Transformed"""
    decodefunc: Callable[[bytes], bytes]
    decodeamount: int
    encodefunc: Callable[[bytes], bytes]
    encodeamount: int

    _feature_impl = (
        _lib.Transformed
    )  # (subcon, decodefunc, decodeamount, encodefunc, encodeamount)


@dataclasses.dataclass
class Tunnel(_ModelFeatureDataclass):
    """Port to construct.Tunnel"""

    _feature_impl = _lib.Tunnel  # (subcon)


@dataclasses.dataclass
class Validator(_ModelFeatureDataclass):
    """Port to construct.Validator"""

    _feature_impl = _lib.Validator  # (subcon)
