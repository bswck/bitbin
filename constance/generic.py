import construct as _lib

from constance import api
from constance import util


__all__ = (
    'generic_defaults',
    'Generic',
)


class Generic:
    def __init__(self, python_type=None):
        self._python_type = python_type

    def __call__(self, args, *, count=None):
        if len(args) == 1:
            constance = util.make_constance(*args)
        else:
            args = list(map(util.ensure_construct, args))
            if len(set(args)) > 1:
                return api.Atomic(_lib.Sequence(*args), python_type=self._python_type)
            constance = api.Atomic(args[0])

        if count is None:
            return api.Atomic(
                _lib.GreedyRange(util.call_construct_method(constance)),
                python_type=self._python_type
            )

        return api.Atomic(
            _lib.Array(count, util.call_construct_method(constance)),
            python_type=self._python_type
        )


generic_defaults = {
    list: Generic(python_type=list),
    set: Generic(python_type=set),
    frozenset: Generic(python_type=frozenset),
    tuple: Generic(python_type=tuple),
}

util.make_constance.generic.update(generic_defaults)
