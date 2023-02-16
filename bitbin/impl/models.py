import construct as _lib

from bitbin import core
from bitbin import util


__all__ = (
    'BitsInteger',
    'Bytes',
    'BytesInteger',
    'Check',
    'Checksum',
    'Compiled',
    'Computed',
    'FocusedSeq',
    'FormatField',
    'IfThenElse',
    'LazyBound',
    'Probe',
    'Seek',
    'Select',
    'Sequence',
    'StopIf',
)


class BitsInteger(core.Model):
    """Port to construct.BitsInteger"""

    _impl = _lib.BitsInteger  # (length, signed=False, swapped=False)


class Bytes(core.Model):
    """Port to construct.Bytes"""

    _impl = _lib.Bytes  # (length)


class BytesInteger(core.Model):
    """Port to construct.BytesInteger"""

    _impl = _lib.BytesInteger  # (length, signed=False, swapped=False)


class Check(core.Model):
    """Port to construct.Check"""

    _impl = _lib.Check  # (func)


class Checksum(core.Model):
    """Port to construct.Checksum"""

    _impl = _lib.Checksum  # (checksumfield, hashfunc, bytesfunc)


class Compiled(core.Model):
    """Port to construct.Compiled"""

    _impl = _lib.Compiled  # (parsefunc, buildfunc)


class Computed(core.Model):
    """Port to construct.Computed"""

    _impl = _lib.Computed  # (func)


class FocusedSeq(core.Model):
    """Port to construct.FocusedSeq"""

    _impl = _lib.FocusedSeq  # (parsebuildfrom, *subcons, **subconskw)


class FormatField(core.Model):
    """Port to construct.FormatField"""

    _impl = _lib.FormatField  # (endianity, format)


class IfThenElse(core.Model):
    """Port to construct.IfThenElse"""

    _impl = _lib.IfThenElse  # (condfunc, thensubcon, elsesubcon)


class LazyBound(core.Model):
    """Port to construct.LazyBound"""

    _impl = _lib.LazyBound  # (subconfunc)


class Probe(core.Model):
    """Port to construct.Probe"""

    _impl = _lib.Probe  # (into=None, lookahead=None)


class Seek(core.Model):
    """Port to construct.Seek"""

    _impl = _lib.Seek  # (at, whence=0)


class Select(core.Model):
    """Port to construct.Select"""

    _impl = _lib.Select  # (*subcons, **subconskw)


class Sequence(core.Model):
    """Port to construct.Sequence"""

    _impl = _lib.Sequence  # (*subcons, **subconskw)
    _fields = None
    _cache = None

    @classmethod
    def _construct(cls):
        if not cls._cache:
            if cls._fields:
                cls._fields = (util.make_model(f)._construct() for f in cls._fields)
            cls._cache = cls._impl(*cls._fields)
        return cls._cache


class StopIf(core.Model):
    """Port to construct.StopIf"""

    _impl = _lib.StopIf  # (condfunc)
